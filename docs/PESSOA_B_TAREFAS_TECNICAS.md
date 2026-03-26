# Pessoa B — Tarefas Técnicas de Fechamento

## Objetivo

Este documento organiza o que a Pessoa B deve fazer daqui para frente para:
- fechar a parte técnica
- parar de abrir escopo
- entregar um pacote estável para análise, testes e redação por A e C

Regra principal:
- nenhuma feature nova fora do experimento
- apenas fechamento, estabilização, execução final e revisão técnica

## Papel da Pessoa B

A Pessoa B é responsável por:
- backend
- KB
- batch
- aggregate
- deploy
- staging
- reprodutibilidade
- revisão técnica final do TCC

A Pessoa B não deve assumir como tarefa principal:
- avaliação humana
- comparação qualitativa manual completa
- screenshots
- escrita integral de resultados
- escrita integral do capítulo do protótipo

## Estado Atual Resumido

Hoje já existe:
- API FastAPI funcional
- `/health`, `/index`, `/retrieve`, `/generate`
- modo `baseline` e modo `rag`
- UI com comparação lado a lado
- batch de geração em lote
- aggregate para `summary.csv` e `summary_wide.csv`
- deploy e smoke
- run válida com `rag_retrieved_ids` preenchido

## Pendências Técnicas Reais

### 1. Consolidar documentação de status
- revisar `docs/STATUS.md`
- decidir se esse arquivo será mantido e commitado
- alinhar `STATUS`, `RUN_INFO` e o recorte real do experimento

### 2. Confirmar configuração final do experimento
- validar `RAG_MIN_SCORE`
- validar `top_k`
- validar `API_BASE_URL`
- validar modelo LLM usado
- congelar essas decisões para a rodada final

### 3. Congelar o dataset do experimento
- decidir versão final de `data/knowledge_base.jsonl`
- decidir versão final de `data/test_cases.jsonl`
- garantir que ambos estejam coerentes com o escopo:
  - `POP`: `Passo a passo`, `Cuidados e Segurança`
  - `COMERCIAL`: `Detalhes essenciais`, `Benefícios (bullets)`

### 4. Validar pipeline ponta a ponta
- `scripts/smoke.sh`
- `POST /index`
- `POST /retrieve`
- `POST /generate`
- `eval/run_batch_generate.py`
- `eval/aggregate_results.py`

### 5. Rodar a execução final
- reindex
- batch final
- aggregate final
- salvar `run_id` oficial
- preservar outputs finais

### 6. Preparar pacote para A e C
- `summary_wide.csv`
- `baseline_run.md`
- `rag_run.md`
- `run_info.json`
- instruções mínimas de leitura e uso

### 7. Fechar ambiente de staging
- garantir que API e UI estejam acessíveis
- validar fluxo principal
- manter apenas bugfix crítico

### 8. Escrever e revisar a parte técnica do TCC
- metodologia técnica
- desenvolvimento do protótipo
- procedimento experimental
- reprodutibilidade
- revisão técnica dos textos dos demais

## Ordem Recomendada de Execução

### Etapa 1 — Congelamento técnico
1. Revisar branch atual e pendências locais
2. Commitar apenas o que for necessário para estabilização
3. Congelar:
   - escopo
   - dataset
   - parâmetros do experimento

### Etapa 2 — Validação
1. Rodar `scripts/smoke.sh`
2. Rodar `./tcpopai-deploy.sh --reindex`
3. Validar `/health`
4. Validar `retrieve` em pelo menos:
   - `limpeza / desengordurante / COMERCIAL`
   - `servicos_operacionais / cadastro_produtos / COMERCIAL`

### Etapa 3 — Execução final
1. Rodar batch final
2. Rodar aggregate final
3. Conferir:
   - número de linhas no `summary_wide.csv`
   - quantas linhas vieram com `rag_retrieved_ids`
   - se não houve falha de geração

### Etapa 4 — Entrega para A e C
1. Separar `run_id` final
2. Enviar para A:
   - `summary_wide.csv`
   - `baseline_run.md`
   - `rag_run.md`
3. Enviar para C:
   - link da UI
   - fluxo mínimo a testar
   - outputs exportados ou exemplos válidos

### Etapa 5 — Escrita técnica
1. Escrever metodologia técnica
2. Escrever desenvolvimento do protótipo
3. Escrever procedimento experimental
4. Escrever reprodutibilidade

### Etapa 6 — Revisão final
1. Revisar texto da Pessoa A
2. Revisar texto da Pessoa C
3. Conferir se tudo bate com o sistema real
4. Corrigir apenas inconsistência técnica ou bug crítico

## Checklist Operacional da Pessoa B

### Freeze
- [ ] escopo congelado
- [ ] KB congelada
- [ ] test cases congelados
- [ ] parâmetros do experimento congelados

### Técnica
- [ ] smoke passando
- [ ] deploy/reindex passando
- [ ] retrieve retornando documentos válidos
- [ ] generate baseline passando
- [ ] generate rag passando com `retrieved`

### Experimento
- [ ] batch final executado
- [ ] aggregate final executado
- [ ] `summary.csv` gerado
- [ ] `summary_wide.csv` gerado
- [ ] outputs finais organizados

### Entrega para o time
- [ ] pacote enviado para A
- [ ] pacote enviado para C
- [ ] instruções mínimas enviadas

### TCC
- [ ] metodologia técnica escrita
- [ ] desenvolvimento do protótipo escrito
- [ ] procedimento experimental escrito
- [ ] reprodutibilidade escrita
- [ ] revisão técnica final feita

## Comandos de Referência

### Smoke
```bash
./scripts/smoke.sh
```

### Reindex local
```bash
curl -sS -X POST http://127.0.0.1:8000/index \
  -H "Content-Type: application/json" \
  -d '{"kb_path":"data/knowledge_base.jsonl","rebuild":true}'
```

### Batch
```bash
python3 eval/run_batch_generate.py --limit 20 --top-k 5
```

### Aggregate
```bash
python3 eval/aggregate_results.py --run-dir data/outputs/<run_id> --wide
```

### Deploy
```bash
./tcpopai-deploy.sh --reindex
```

## Entregáveis Finais da Pessoa B

### Técnicos
- branch estável
- deploy estável
- staging estável
- pipeline reproduzível

### Experimentais
- `baseline_run.json`
- `rag_run.json`
- `baseline_run.md`
- `rag_run.md`
- `summary.csv`
- `summary_wide.csv`
- `run_info.json`

### Textuais
- metodologia técnica
- desenvolvimento do protótipo
- procedimento experimental
- reprodutibilidade

## Critério de Encerramento da Pessoa B

A parte da Pessoa B só deve ser considerada encerrada quando:
- o pipeline rodar sem intervenção manual extra
- o `run_id` final estiver definido
- A e C já tiverem material suficiente para trabalhar sem depender de você
- o restante do trabalho técnico for apenas revisão e bugfix crítico

## Regra Final

Se surgir uma tarefa nova, perguntar:

“Isso é necessário para fechar o experimento e permitir que A e C trabalhem?”

Se a resposta for:
- `sim`: fazer
- `não`: não abrir escopo
