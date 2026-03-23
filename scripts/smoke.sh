#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

TMP_DIR="$(mktemp -d)"
SERVER_LOG="${TMP_DIR}/server.log"

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]] && kill -0 "${SERVER_PID}" 2>/dev/null; then
    kill "${SERVER_PID}" 2>/dev/null || true
    wait "${SERVER_PID}" 2>/dev/null || true
  fi
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

echo "[smoke] starting API server at ${BASE_URL}"
"${PYTHON_BIN}" -m uvicorn src.api.main:app --host "${HOST}" --port "${PORT}" >"${SERVER_LOG}" 2>&1 &
SERVER_PID=$!

for _ in $(seq 1 40); do
  if curl -sS "${BASE_URL}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -sS "${BASE_URL}/health" >/dev/null 2>&1; then
  echo "[smoke] server failed to start; log:"
  cat "${SERVER_LOG}"
  exit 1
fi

echo "[smoke] GET /health"
curl --fail-with-body -sS "${BASE_URL}/health"
echo

echo "[smoke] POST /index"
curl --fail-with-body -sS -X POST "${BASE_URL}/index" \
  -H "Content-Type: application/json" \
  -d '{"kb_path":"data/knowledge_base.jsonl","rebuild":true}'
echo

RETRIEVE_PAYLOAD='{
  "query":"Detalhes essenciais. Desengordurante multiuso. Removedor de gordura para cozinhas e superficies lavaveis. pequenos negocios e uso domestico. azulejo, inox e superficies lavaveis. pronto uso. 1 a 3 minutos.",
  "domain":"limpeza",
  "subcategory":"desengordurante",
  "doc_type":"COMERCIAL",
  "section":"Detalhes essenciais",
  "top_k":3
}'

BASELINE_PAYLOAD='{
  "mode":"baseline",
  "domain":"limpeza",
  "subcategory":"desengordurante",
  "doc_type":"COMERCIAL",
  "section":"Detalhes essenciais",
  "top_k":3,
  "input_item":{
    "item_id":"LIMPEZA_001",
    "domain":"limpeza",
    "subcategory":"desengordurante",
    "risk_level":"medio",
    "nome":"Desengordurante multiuso",
    "descricao_curta":"Removedor de gordura para cozinhas e superficies lavaveis.",
    "publico_alvo":"pequenos negocios e uso domestico",
    "canal_venda":"marketplace",
    "atributos_comuns":[{"k":"volume","v":"500 mL"},{"k":"forma","v":"liquido em borrifador"}],
    "atributos_limpeza":{
      "superficie_alvo":"azulejo, inox e superficies lavaveis",
      "diluicao":"pronto uso",
      "tempo_acao":"1 a 3 minutos",
      "compatibilidades":"inoxidavel, azulejo, plastico rigido",
      "incompatibilidades":"madeira nao selada e superficies sensiveis",
      "epi":"luvas; evitar contato com olhos",
      "observacoes":"nao informado"
    },
    "atributos_servico":{}
  }
}'

RAG_PAYLOAD='{
  "mode":"rag",
  "domain":"limpeza",
  "subcategory":"desengordurante",
  "doc_type":"COMERCIAL",
  "section":"Detalhes essenciais",
  "top_k":3,
  "input_item":{
    "item_id":"LIMPEZA_001",
    "domain":"limpeza",
    "subcategory":"desengordurante",
    "risk_level":"medio",
    "nome":"Desengordurante multiuso",
    "descricao_curta":"Removedor de gordura para cozinhas e superficies lavaveis.",
    "publico_alvo":"pequenos negocios e uso domestico",
    "canal_venda":"marketplace",
    "atributos_comuns":[{"k":"volume","v":"500 mL"},{"k":"forma","v":"liquido em borrifador"}],
    "atributos_limpeza":{
      "superficie_alvo":"azulejo, inox e superficies lavaveis",
      "diluicao":"pronto uso",
      "tempo_acao":"1 a 3 minutos",
      "compatibilidades":"inoxidavel, azulejo, plastico rigido",
      "incompatibilidades":"madeira nao selada e superficies sensiveis",
      "epi":"luvas; evitar contato com olhos",
      "observacoes":"nao informado"
    },
    "atributos_servico":{}
  }
}'

echo "[smoke] POST /retrieve"
curl --fail-with-body -sS -X POST "${BASE_URL}/retrieve" \
  -H "Content-Type: application/json" \
  -d "${RETRIEVE_PAYLOAD}"
echo

echo "[smoke] POST /generate (mode=baseline)"
curl -sS -X POST "${BASE_URL}/generate" \
  --fail-with-body \
  -H "Content-Type: application/json" \
  -d "${BASELINE_PAYLOAD}"
echo

echo "[smoke] POST /generate (mode=rag)"
curl -sS -X POST "${BASE_URL}/generate" \
  --fail-with-body \
  -H "Content-Type: application/json" \
  -d "${RAG_PAYLOAD}"
echo

echo "[smoke] done"
