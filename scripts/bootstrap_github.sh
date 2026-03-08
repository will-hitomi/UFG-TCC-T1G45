#!/usr/bin/env bash
set -euo pipefail

REPO="will-hitomi/UFG-TCC-T1G45"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Falta: $1"; exit 1; }; }
need gh
need python3

gh auth status >/dev/null 2>&1 || { echo "Faça login: gh auth login"; exit 1; }

# ----------------------------
# Helpers
# ----------------------------
milestone_get_or_create() {
  local title="$1"
  local due="$2"          # ISO: 2026-03-13T23:59:59Z
  local desc="$3"

  local json
  json="$(gh api "repos/$REPO/milestones?state=all&per_page=100")"

  local number
  number="$(python3 - <<PY
import json, sys
ms=json.loads(sys.stdin.read())
title="$title"
for m in ms:
  if m.get("title")==title:
    print(m.get("number"))
    sys.exit(0)
print("")
PY
<<<"$json")"

  if [[ -n "${number:-}" ]]; then
    echo "$number"
    return 0
  fi

  number="$(gh api -X POST "repos/$REPO/milestones" \
    -f title="$title" \
    -f description="$desc" \
    -f due_on="$due" \
    --jq '.number')"

  echo "$number"
}

label_create_if_missing() {
  local name="$1" color="$2" desc="$3"
  gh label create "$name" --repo "$REPO" --color "$color" --description "$desc" 2>/dev/null || true
}

issue_create_once() {
  local title="$1"
  local body="$2"
  local labels="$3"
  local milestone="$4"

  # evita duplicar: procura issue com mesmo título
  local existing
  existing="$(gh issue list --repo "$REPO" --search "\"$title\" in:title" --json number,title --limit 50 \
    --jq ".[] | select(.title==\"$title\") | .number" | head -n 1 || true)"
  if [[ -n "${existing:-}" ]]; then
    echo "[skip] Issue já existe (#$existing): $title"
    return 0
  fi

  gh issue create --repo "$REPO" \
    --title "$title" \
    --body "$body" \
    --label "$labels" \
    --milestone "$milestone" >/dev/null

  echo "[ok] Criada: $title"
}

# ----------------------------
# Labels
# ----------------------------
echo "[+] Criando labels (se faltarem)..."
label_create_if_missing "P0" "d73a4a" "Bloqueante"
label_create_if_missing "P1" "fbca04" "Alta"
label_create_if_missing "P2" "c2e0c6" "Média/Baixa"
label_create_if_missing "area:data" "1d76db" "Dados/KB"
label_create_if_missing "area:backend" "1d76db" "Backend/API/RAG"
label_create_if_missing "area:ui" "1d76db" "Interface"
label_create_if_missing "area:eval" "1d76db" "Avaliação/Resultados"
label_create_if_missing "area:ops" "1d76db" "Infra/Deploy"
label_create_if_missing "area:docs" "1d76db" "Documentação"
label_create_if_missing "scope:v1" "0e8a16" "Escopo v1"
label_create_if_missing "nice-to-have" "c5def5" "Opcional"

# ----------------------------
# Milestones
# ----------------------------
echo "[+] Criando milestones (se faltarem)..."

M1="$(milestone_get_or_create "M1 — MVP Dev" "2026-03-13T23:59:59Z" "UI+Batch+Dataset mínimo")"
M2="$(milestone_get_or_create "M2 — Dataset v2 + Batch + UX demo" "2026-03-29T23:59:59Z" "Dataset forte + batch/CSV + demo")"
M3="$(milestone_get_or_create "M3 — Freeze Dev + evidências" "2026-04-05T23:59:59Z" "Congelar features e gerar evidências")"
M4="$(milestone_get_or_create "M4 — Resultados consolidados" "2026-04-26T23:59:59Z" "Análise final de resultados")"
M5="$(milestone_get_or_create "M5 — Redação final" "2026-05-17T23:59:59Z" "Documento final")"

echo "Milestones: M1=$M1 M2=$M2 M3=$M3 M4=$M4 M5=$M5"

# ----------------------------
# Issues (escopo reduzido)
# ----------------------------
echo "[+] Criando issues principais..."

issue_create_once \
  "A-001 — KB v1 (limpeza, 4 seções-alvo)" \
  $'**Owner:** A\n\nObjetivo: Expandir `data/knowledge_base.jsonl` para o domínio **limpeza** cobrindo as seções do escopo.\n\n**Aceite**\n- >= 120 linhas JSONL\n- Campos obrigatórios por linha: id, domain, subcategory, doc_type, section, text, source, lang\n- doc_type: POP e COMERCIAL\n- seções: Passo a passo; Cuidados e Segurança; Detalhes essenciais; Benefícios (bullets)\n\n**DoD**\n- validação JSONL ok\n- PR para main\n- reindex pós-merge (admin)\n' \
  "P0,area:data,scope:v1" \
  "$M1"

issue_create_once \
  "A-002 — Test cases v1 (limpeza)" \
  $'**Owner:** A\n\nObjetivo: Criar `data/test_cases.jsonl` com >= 15 itens de limpeza.\n\n**Aceite**\n- >= 15 itens\n- campos mínimos preenchidos: nome, descricao_curta, superficie_alvo, diluicao/pronto uso, epi/cuidados, incompatibilidades\n\n**DoD**\n- validação JSONL ok\n- PR para main\n' \
  "P0,area:data,scope:v1" \
  "$M1"

issue_create_once \
  "B-001 — Batch runner v1 (baseline vs rag)" \
  $'**Owner:** B\n\nObjetivo: `eval/run_batch_generate.py` lê `data/test_cases.jsonl` e gera baseline vs rag em lote para:\n- POP: Passo a passo; Cuidados e Segurança\n- COMERCIAL: Detalhes essenciais; Benefícios (bullets)\n\n**DoD**\n- roda em 1 comando e salva em `data/outputs/<timestamp>/`\n- `docs/EVAL.md` com instruções\n- PR para main\n\n**Dependência:** A-002\n' \
  "P0,area:backend,area:eval,scope:v1" \
  "$M1"

issue_create_once \
  "C-001 — UI v1 (lado a lado + multisseção + export)" \
  $'**Owner:** C\n\nObjetivo: UI Streamlit com baseline vs rag lado a lado, multiselect das 4 seções do escopo e export MD/JSON.\n\n**DoD**\n- roda local\n- roda no staging (Ubuntu)\n- PR para main\n' \
  "P0,area:ui,scope:v1" \
  "$M1"

issue_create_once \
  "A-003 — KB v2 (>= 300 linhas, variedade)" \
  $'**Owner:** A\n\nObjetivo: aumentar KB para >= 300 linhas, com 3–5 exemplos por seção por subcategoria.\n\n**DoD**\n- validação JSONL\n- PR + reindex pós-merge\n' \
  "P0,area:data,scope:v1" \
  "$M2"

issue_create_once \
  "B-003 — Aggregator (summary.csv)" \
  $'**Owner:** B\n\nObjetivo: `eval/aggregate_results.py` consolida outputs do batch e gera `summary.csv`.\n\n**Aceite**\n- colunas: item_id, doc_type, section, mode, text, retrieved_ids, retrieved_scores\n' \
  "P0,area:eval,scope:v1" \
  "$M2"

issue_create_once \
  "A-004 — Avaliação humana (amostra 40 comparações)" \
  $'**Owner:** A\n\nObjetivo: avaliar 10 itens × 4 seções = 40 comparações baseline vs rag.\n\n**Saídas**\n- eval/rubric.md\n- eval/human_scores.csv (ou .xlsx)\n' \
  "P0,area:eval,scope:v1" \
  "$M3"

issue_create_once \
  "B-004 — Run final + RUN_INFO.md" \
  $'**Owner:** B\n\nObjetivo: rodar batch final e registrar parâmetros (LLM, top_k, RAG_MIN_SCORE, commit hash do dataset).\n\n**Saída**\n- docs/RUN_INFO.md\n' \
  "P0,area:eval,scope:v1" \
  "$M3"

echo "[+] Pronto. Milestones e issues principais criados."
