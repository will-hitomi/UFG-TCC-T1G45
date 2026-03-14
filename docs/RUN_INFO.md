# RUN_INFO — Run Final (B-004)

## Identificação
- run_id: <timestamp_da_pasta>
- data/hora: <yyyy-mm-dd hh:mm:ss>
- branch: main
- commit hash: <git rev-parse HEAD>

## Configuração
- API_BASE_URL: http://127.0.0.1:8000
- LLM_MODEL: <valor do env>
- EMBEDDING_MODEL: <valor do env>
- CHROMA_COLLECTION: kb_sections
- top_k: 5
- RAG_MIN_SCORE: 0.30
- seções (escopo v1):
  - POP: Passo a passo; Cuidados e Segurança
  - COMERCIAL: Detalhes essenciais; Benefícios (bullets)

## Dataset
- KB: data/knowledge_base.jsonl (linhas: <wc -l>)
- casos: data/test_cases.jsonl (linhas: <wc -l>)
- limite usado: 20

## Outputs
- pasta: data/outputs/<timestamp>/
- arquivos gerados:
  - baseline_run.json / rag_run.json
  - baseline_run.md / rag_run.md
  - summary.csv / summary_wide.csv

## Como reproduzir
1) ./tcpopai-deploy.sh --reindex
2) python eval/run_batch_generate.py --limit 20 --top-k 5
3) python eval/aggregate_results.py --run-dir data/outputs/<run_id> --wide