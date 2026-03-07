#!/usr/bin/env bash
set -euo pipefail

# tcpoai-deploy.sh
# Uso:
#   ./tcpopai-deploy.sh
#   ./tcpopai-deploy.sh --reindex
#   ./tcpopai-deploy.sh --reindex --kb-path data/knowledge_base.jsonl
#   ./tcpopai-deploy.sh --no-pull
#
# Pré-req:
# - Serviços systemd: tcpopai-api e tcpopai-ui
# - Repo em /home/lhanowar/TCPOPAI (ou rode o script de dentro do repo)
# - API acessível em http://127.0.0.1:8000

BRANCH="main"
DO_PULL=1
DO_REINDEX=0
KB_PATH="data/knowledge_base.jsonl"
REBUILD=true
SERVICES=("tcpopai-api" "tcpopai-ui")
API_URL="http://127.0.0.1:8000"
HEALTH_TIMEOUT_SEC=45

usage() {
  echo "Uso: $0 [--reindex] [--kb-path PATH] [--no-pull] [--branch BRANCH]"
  exit 1
}

wait_for_api_health() {
  local waited=0
  while (( waited < HEALTH_TIMEOUT_SEC )); do
    if curl -fsS "$API_URL/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    waited=$((waited + 1))
  done
  return 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --reindex) DO_REINDEX=1; shift ;;
    --kb-path) KB_PATH="${2:-}"; [[ -z "$KB_PATH" ]] && usage; shift 2 ;;
    --no-pull) DO_PULL=0; shift ;;
    --branch) BRANCH="${2:-}"; [[ -z "$BRANCH" ]] && usage; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Argumento desconhecido: $1"; usage ;;
  esac
done

# Garantir que estamos no root do repo
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_DIR="$(git rev-parse --show-toplevel)"
else
  echo "[deploy] ERRO: rode este script dentro do repositório git."
  exit 1
fi

cd "$REPO_DIR"
echo "[deploy] Repo: $REPO_DIR"

# Trocar para branch e atualizar
echo "[deploy] Checkout $BRANCH"
git checkout "$BRANCH" >/dev/null

BEFORE="$(git rev-parse HEAD)"
if [[ $DO_PULL -eq 1 ]]; then
  echo "[deploy] git pull"
  git pull --ff-only
else
  echo "[deploy] pull desativado (--no-pull)"
fi
AFTER="$(git rev-parse HEAD)"

# Instalar deps somente se requirements mudou (ou se venv não existe)
VENV_PY="$REPO_DIR/.venv/bin/python"
REQ_CHANGED=0

if [[ "$BEFORE" != "$AFTER" ]]; then
  if git diff --name-only "$BEFORE" "$AFTER" | grep -q "^requirements\.txt$"; then
    REQ_CHANGED=1
  fi
fi

if [[ ! -x "$VENV_PY" ]]; then
  echo "[deploy] .venv não existe. Criando venv e instalando dependências..."
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
elif [[ $REQ_CHANGED -eq 1 ]]; then
  echo "[deploy] requirements.txt mudou. Atualizando dependências..."
  .venv/bin/pip install -r requirements.txt
else
  echo "[deploy] requirements.txt não mudou. Pulando pip install."
fi

# Reiniciar serviços
echo "[deploy] Reiniciando serviços: ${SERVICES[*]}"
sudo systemctl restart "${SERVICES[@]}"

echo "[deploy] Status (últimas linhas):"
for svc in "${SERVICES[@]}"; do
  sudo systemctl --no-pager --full status "$svc" | sed -n '1,12p' || true
done

echo "[deploy] Aguardando API ficar pronta em $API_URL/health ..."
if ! wait_for_api_health; then
  echo "[deploy] ERRO: API não ficou pronta em ${HEALTH_TIMEOUT_SEC}s."
  sudo journalctl -u tcpopai-api -n 80 --no-pager || true
  exit 1
fi
echo "[deploy] API pronta."

# Reindex opcional
if [[ $DO_REINDEX -eq 1 ]]; then
  echo "[deploy] Reindex acionado: $KB_PATH (rebuild=$REBUILD)"
  if ! curl -fsS -X POST "$API_URL/admin/index" \
    -H "Content-Type: application/json" \
    -d "{\"kb_path\":\"$KB_PATH\",\"rebuild\":$REBUILD}" \
    | sed 's/^/[deploy] /'; then
    echo "[deploy] ERRO: reindex falhou."
    sudo journalctl -u tcpopai-api -n 80 --no-pager || true
    exit 1
  fi
else
  echo "[deploy] Reindex não solicitado. (use --reindex)"
fi

echo "[deploy] OK ✅"
