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

BASELINE_PAYLOAD='{
  "mode":"baseline",
  "domain":"limpeza",
  "subcategory":"desengordurante",
  "doc_type":"TECNICO",
  "section":"Modo de uso (objetivo e conciso)",
  "top_k":3,
  "input_item":{
    "item_id":"case_0_deseng_001",
    "domain":"limpeza",
    "subcategory":"desengordurante",
    "risk_level":"medio",
    "nome":"Desengordurante Multiuso X",
    "descricao_curta":"Produto para remoção de gordura em superfícies laváveis",
    "publico_alvo":"cozinhas residenciais e pequenas lanchonetes",
    "canal_venda":"marketplace",
    "atributos_comuns":[{"k":"fragrancia","v":"neutra"}],
    "atributos_limpeza":{
      "superficie_alvo":"fogões, bancadas e azulejos",
      "diluicao":"pronto uso",
      "tempo_acao":"2 minutos",
      "compatibilidades":"superfícies laváveis",
      "incompatibilidades":"madeira não selada",
      "epi":"luvas",
      "observacoes":"testar em área pequena antes do uso contínuo"
    },
    "atributos_servico":{}
  }
}'

RAG_PAYLOAD='{
  "mode":"rag",
  "domain":"limpeza",
  "subcategory":"desengordurante",
  "doc_type":"TECNICO",
  "section":"Modo de uso (objetivo e conciso)",
  "top_k":3,
  "input_item":{
    "item_id":"case_0_deseng_001",
    "domain":"limpeza",
    "subcategory":"desengordurante",
    "risk_level":"medio",
    "nome":"Desengordurante Multiuso X",
    "descricao_curta":"Produto para remoção de gordura em superfícies laváveis",
    "publico_alvo":"cozinhas residenciais e pequenas lanchonetes",
    "canal_venda":"marketplace",
    "atributos_comuns":[{"k":"fragrancia","v":"neutra"}],
    "atributos_limpeza":{
      "superficie_alvo":"fogões, bancadas e azulejos",
      "diluicao":"pronto uso",
      "tempo_acao":"2 minutos",
      "compatibilidades":"superfícies laváveis",
      "incompatibilidades":"madeira não selada",
      "epi":"luvas",
      "observacoes":"testar em área pequena antes do uso contínuo"
    },
    "atributos_servico":{}
  }
}'

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
