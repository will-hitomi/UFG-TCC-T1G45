# STATUS — Projeto TCPOPAI

## Estado Atual

- Contrato oficial: `docs/API_CONTRACT.md` e `docs/SECTIONS.md`.
- API FastAPI ativa com `/health`, `/index`, `/retrieve` e `/generate`.
- `/generate` suporta `mode=baseline` e `mode=rag`, com 1 seção por request.
- RAG por seção usa filtro por `domain + doc_type + section + subcategory`.
- KB atual alinhada ao escopo reduzido do experimento:
  - `POP`: `Passo a passo`, `Cuidados e Segurança`
  - `COMERCIAL`: `Detalhes essenciais`, `Benefícios (bullets)`
- Batch e agregação já existem:
  - `eval/run_batch_generate.py`
  - `eval/aggregate_results.py`
- UI mínima disponível em `src/app/ui_streamlit.py`, com comparação baseline vs rag.
- Staging ativo:
  - UI: `https://tcpopai-app.krmn.online`
  - API: `https://tcpopai-api.krmn.online`

## Escopo Reduzido Vigente

- Domínios priorizados:
  - `limpeza`
  - `servicos_operacionais`
- Subcategorias cobertas de forma prioritária no ciclo atual:
  - `desengordurante`
  - `cadastro_produtos`
- Objetivo do ciclo:
  - estabilizar pipeline
  - fechar rodada de batch
  - consolidar resultados para relatório

## Cronograma Reorganizado Por Pessoa

### 07/03–15/03

**Pessoa A — Dados**
- Definir lista de 15–20 itens de limpeza, cobrindo subcategorias variadas.
- Criar ou expandir `data/knowledge_base.jsonl` focando apenas nas 4 seções do escopo:
  - `POP`: `Passo a passo`, `Cuidados e Segurança`
  - `COMERCIAL`: `Detalhes essenciais`, `Benefícios (bullets)`
- Criar `data/test_cases.jsonl` com 10 itens para a primeira rodada de batch.
- Criar rubrica v1 (1–5): clareza, completude, aderência ao input, padronização.

**Pessoa B — Backend/Experimento**
- Garantir que `/generate` esteja estável para essas seções, em `baseline` e `rag`.
- Criar script de geração em lote que:
  - lê `data/test_cases.jsonl`
  - gera baseline vs rag para as 4 seções
  - salva outputs em JSON e MD por timestamp
- Padronizar `RAG_MIN_SCORE` no ambiente e na documentação.

**Pessoa C — UI**
- Entregar UI v1 com:
  - baseline vs rag lado a lado
  - multiselect para as 4 seções
  - export MD/JSON em `data/outputs/`
  - formulário guiado de `InputItem` para limpeza
- Extra opcional:
  - botão `Gerar título` fora do experimento

**Entrega do período**
- Pipeline completo rodando: UI + batch + export.

### 16/03–29/03

**Pessoa A — Dados + Preparar avaliação**
- Expandir a KB para 200–400 linhas, com meta realista de 25–50 exemplos por seção.
- Ajustar `data/test_cases.jsonl` para 20 itens; se possível, 30.
- Definir amostra de avaliação humana, por exemplo:
  - 10 itens x 4 seções = 40 comparações baseline vs rag

**Pessoa B — Consolidação de resultados**
- Rodar batch em 20–30 itens.
- Gerar agregador simples em CSV com:
  - `item_id`
  - `section`
  - `baseline_text`
  - `rag_text`
  - `retrieved_ids`
  - `retrieved_scores`
- Preparar pacote de evidências:
  - prints
  - logs
  - outputs

**Pessoa C — UX mínima para demo**
- Implementar `Carregar caso` lendo `data/test_cases.jsonl`.
- Exibir painel colapsável com `debug.retrieved`.
- Ajustar robustez:
  - timeouts
  - mensagens de erro por seção
  - status e progresso

**Entrega do período**
- Dataset bom + primeira rodada de resultados gerados e organizados.

### 30/03–05/04

**Pessoa A**
- Rodar avaliação humana da amostra e salvar `eval/human_scores.csv` ou planilha equivalente.
- Escrever 1 página de observações qualitativas por seção.

**Pessoa B**
- Congelar features, mantendo apenas bugfix.
- Rodar batch final com configuração estável.
- Garantir reprodutibilidade com execução em 1 comando.

**Pessoa C**
- Deixar UI estável no staging Ubuntu.
- Garantir export consistente.
- Capturar screenshots para o relatório.

**Entrega do período**
- Protótipo e experimento fechados.

### 06/04–26/04

**Resultados**

**Pessoa A**
- Consolidar notas, médias por seção e exemplos qualitativos bons e ruins.

**Pessoa B**
- Produzir tabelas e gráficos simples.
- Escrever análise baseline vs rag.
- Registrar quando o RAG ajudou, quando não ajudou e por quê.

**Pessoa C**
- Escrever seção do protótipo:
  - fluxo do usuário
  - screenshots
  - limitações

### 27/04–17/05

**Redação**

- Montar capítulo por capítulo.
- Ajustar formatação ABNT.
- Fazer revisão final.
- Preparar anexos:
  - outputs
  - rubrica
  - prints
- Fechar checklist de reprodução:
  - como rodar
  - qual ambiente
  - quais variáveis de configuração

## Observações

- O cronograma acima substitui o entendimento anterior de sprint curto.
- O foco atual é concluir com qualidade o escopo reduzido, em vez de ampliar features fora do experimento.
- Alterações de contrato continuam proibidas sem `SPEC CHANGE`.
