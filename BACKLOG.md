# BACKLOG — UFG-TCC-T1G45 (TCPOPAI)

## Escopo congelado (v1)
- Domínio: **limpeza**
- Doc types: **POP** + **COMERCIAL**
- Seções (2 por doc):
  - POP: **Passo a passo**, **Cuidados e Segurança**
  - Comercial: **Detalhes essenciais**, **Benefícios (bullets)**

## Regras
- `main` sempre verde.
- 1 card = 1 branch = 1 PR pequeno.
- Mudança de contrato só via “SPEC CHANGE”.
- Reindex é admin-only (`/admin/index`) após merge que altera KB.

---

# Como usar este backlog
Status padrão por card:
- [ ] TODO
- [~] DOING
- [x] DONE

Sugestão de branch:
- `feat/<Owner>-<ID>-<slug-curto>`

---

# Milestones (datas sugeridas)
- **M1 — MVP Dev** (até 2026-03-13)
- **M2 — Dataset v2 + Batch + UX demo** (até 2026-03-29)
- **M3 — Freeze Dev + evidências** (até 2026-04-05)
- **M4 — Resultados consolidados** (até 2026-04-26)
- **M5 — Redação final** (até 2026-05-17)

---

# M1 — MVP Dev (até 13/03)

## [ ] A-001 — KB v1 (limpeza, 4 seções-alvo)
Owner: A  
Labels: P0,area:data  
Branch: feat/A-A-001-kb-v1

**Objetivo**
Expandir `data/knowledge_base.jsonl` para cobrir as 4 seções do escopo no domínio limpeza.

**Entradas**
- `docs/SECTIONS.md`
- exemplos de textos/boas práticas (interno)

Outputs:
- `data/knowledge_base.jsonl`

**Critérios de aceite**
- KB com **≥ 120 linhas JSONL**
- Cada linha tem: `id, domain, subcategory, doc_type, section, text, source, lang`
- Apenas `domain=limpeza` e `doc_type` ∈ {POP, COMERCIAL}
- Seções somente do escopo (4 seções)

DoD:
- `python -c "import json; [json.loads(l) for l in open('data/knowledge_base.jsonl',encoding='utf-8') if l.strip()]; print('OK KB')"`
- PR aberto para `main`
- Após merge: B roda `/admin/index`

---

## [ ] A-002 — Test cases v1 (limpeza)
Owner: A  
Labels: P0,area:data  
Branch: feat/A-A-002-testcases-v1

**Objetivo**
Criar `data/test_cases.jsonl` para batch e UI.

Outputs:
- `data/test_cases.jsonl`

**Critérios de aceite**
- **≥ 15 itens** no domínio limpeza
- Formato compatível com `InputItem` do SPEC
- Campos mínimos preenchidos para qualidade (nome, descrição curta, superfície alvo, diluição/pronto uso, EPI/cuidados, incompatibilidades)

DoD:
- validação JSONL OK
- PR para `main`

---

## [ ] B-001 — Batch runner v1 (baseline vs rag)
Owner: B  
Labels: P0,area:backend/eval  
Branch: feat/B-B-001-batch-runner

**Objetivo**
Gerar outputs em lote (baseline vs rag) para as 4 seções do escopo e salvar em `data/outputs/<timestamp>/`.

Outputs:
- `eval/run_batch_generate.py`
- `docs/EVAL.md` (como rodar)
- `data/outputs/` (gitignored)

**Critérios de aceite**
- Um comando roda e gera outputs para N itens do `test_cases.jsonl`
- Gera baseline e rag para:
  - POP: Passo a passo / Cuidados e Segurança
  - COMERCIAL: Detalhes essenciais / Benefícios (bullets)
- Salva `baseline.md`, `rag.md`, `baseline.json`, `rag.json` (por item ou consolidado por run)

DoD:
- `python eval/run_batch_generate.py --limit 5` funciona
- outputs criados em `data/outputs/...`
- PR para `main`

Dependencies:
- A-002

---

## [ ] C-001 — UI v1 (lado a lado + multisseção + export)
Owner: C  
Labels: P0,area:ui  
Branch: feat/C-C-001-ui-v1

**Objetivo**
UI Streamlit para comparar baseline vs rag lado a lado, gerar múltiplas seções (loop) e exportar MD/JSON.

Outputs:
- `src/app/ui_streamlit.py`
- `requirements.txt` (streamlit + requests)

**Critérios de aceite**
- Baseline vs RAG lado a lado
- Multiselect das 4 seções do escopo
- Export em `data/outputs/<timestamp>/`
- Carregar casos (dropdown do `test_cases.jsonl` OU botão “carregar caso” mínimo)

DoD:
- roda local: `streamlit run src/app/ui_streamlit.py`
- staging no Ubuntu via systemd `tcpopai-ui` (ou instrução documentada)
- PR para `main`

Dependencies:
- A-002 (para dropdown) e API ok

---

## [ ] B-002 — Ops: deploy manual + serviços (API/UI) documentados
Owner: B  
Labels: P1,area:ops/docs  
Branch: chore/B-B-002-ops-docs

**Objetivo**
Garantir que staging é confiável: systemd + deploy script + docs.

Outputs:
- `tcpopai-deploy.sh`
- `docs/ONBOARDING.md`

**Critérios de aceite**
- `tcpopai-api` e `tcpopai-ui` sobem via systemd
- `./tcpopai-deploy.sh --reindex` funciona
- onboarding para iniciantes completo

DoD:
- serviços ativos
- docs revisadas
- PR para `main`

---

# M2 — Dataset v2 + Batch final + UX demo (até 29/03)

## [ ] A-003 — KB v2 (volume e variedade)
Owner: A  
Labels: P0,area:data  
Branch: feat/A-A-003-kb-v2

**Objetivo**
Aumentar KB para “fazer RAG brilhar” nas 4 seções do escopo.

**Critérios de aceite**
- KB com **≥ 300 linhas**
- Pelo menos **3–5 exemplos por seção** por subcategoria (limpeza)

DoD:
- validação JSONL
- PR + merge
- reindex pós-merge

---

## [ ] B-003 — Aggregator (summary.csv)
Owner: B  
Labels: P0,area:eval  
Branch: feat/B-B-003-aggregate

**Objetivo**
Consolidar outputs do batch em um CSV único para análise e gráficos.

Outputs:
- `eval/aggregate_results.py`
- `data/outputs/<run>/summary.csv`

**Critérios de aceite**
- CSV com colunas: `item_id, doc_type, section, mode, text, retrieved_ids, retrieved_scores`

DoD:
- roda após batch
- PR para `main`

Dependencies:
- B-001

---

## [ ] C-002 — UI: carregar casos + debug limpo
Owner: C  
Labels: P1,area:ui  
Branch: feat/C-C-002-ui-cases-debug

**Objetivo**
Dropdown de casos + painel colapsável de debug.

DoD:
- dropdown lendo `data/test_cases.jsonl`
- debug.retrieved exibido de forma clara
- PR para `main`

Dependencies:
- A-002, C-001

---

# M3 — Freeze Dev + evidências (até 05/04)

## [ ] A-004 — Avaliação humana (amostra) + rubrica
Owner: A  
Labels: P0,area:eval  
Branch: feat/A-A-004-human-eval

**Objetivo**
Avaliar baseline vs rag com rubrica simples.

Outputs:
- `eval/rubric.md`
- `eval/human_scores.csv` (ou `.xlsx`)

**Critérios de aceite**
- Amostra mínima: **10 itens × 4 seções = 40 comparações**
- Notas 1–5 + comentário curto (quando necessário)

DoD:
- arquivo no repo
- PR para `main`

Dependencies:
- B-001, A-003

---

## [ ] B-004 — Run final + RUN_INFO.md
Owner: B  
Labels: P0,area:eval  
Branch: feat/B-B-004-final-run

**Objetivo**
Rodar batch final com config congelada e registrar parâmetros.

Outputs:
- `data/outputs/<timestamp_final>/...` (armazenar fora do git se necessário)
- `docs/RUN_INFO.md` (modelo LLM, top_k, min_score, dataset commit hash)

DoD:
- run gerada
- summary.csv ok
- RUN_INFO.md completo

Dependencies:
- B-003

---

## [ ] C-003 — Capturas e guia de uso do protótipo
Owner: C  
Labels: P1,area:docs/ui  
Branch: feat/C-C-003-screenshots

Outputs:
- `docs/assets/` (imagens)
- `docs/PROTOTYPE_GUIDE.md`

DoD:
- prints: baseline vs rag, export, debug
- PR para `main`

---

# M4 — Resultados (até 26/04)

## [ ] A-005 — Análise da avaliação humana (texto + tabela)
Owner: A  
Labels: P0,area:results  
Branch: feat/A-A-005-results-human
Outputs: `docs/RESULTS_HUMAN.md`
DoD:
- PR para `main`

## [ ] B-005 — Resultados técnicos (tabelas/gráficos)
Owner: B  
Labels: P0,area:results  
Branch: feat/B-B-005-results-tech
Outputs: `docs/RESULTS_TECH.md`
DoD:
- PR para `main`

## [ ] C-004 — Seção protótipo (fluxo + limitações)
Owner: C  
Labels: P1,area:docs  
Branch: feat/C-C-004-prototype-section
Outputs: `docs/PROTOTYPE_SECTION.md`
DoD:
- PR para `main`

---

# M5 — Redação (até 17/05)
Cards de redação serão criados na virada do M4.
