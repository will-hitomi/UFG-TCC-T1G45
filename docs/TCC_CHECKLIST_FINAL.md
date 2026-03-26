# TCC CHECKLIST FINAL — TCPOPAI

## Objetivo

Checklist único para acompanhar o fechamento do TCC, separando:
- entregas técnicas
- entregas de avaliação
- entregas de protótipo
- entregas de redação

## 1. Fechamento Técnico — Pessoa B

### Backend e pipeline
- [ ] API estável
- [ ] `/health` funcionando
- [ ] `/index` funcionando
- [ ] `/retrieve` funcionando
- [ ] `/generate` baseline funcionando
- [ ] `/generate` rag funcionando
- [ ] `scripts/smoke.sh` passando

### Dados e experimento
- [ ] `data/knowledge_base.jsonl` congelado
- [ ] `data/test_cases.jsonl` congelado
- [ ] parâmetros do experimento congelados
- [ ] batch final executado
- [ ] aggregate final executado
- [ ] `summary.csv` gerado
- [ ] `summary_wide.csv` gerado

### Deploy e staging
- [ ] deploy funcionando
- [ ] reindex funcionando
- [ ] UI no staging funcionando
- [ ] API no staging funcionando

### Entregáveis para o grupo
- [ ] `run_id` final definido
- [ ] outputs finais organizados
- [ ] pacote enviado para Pessoa A
- [ ] pacote enviado para Pessoa C

## 2. Avaliação e Resultados — Pessoa A

### Avaliação humana
- [ ] rubrica final definida
- [ ] planilha de avaliação criada
- [ ] amostra avaliada
- [ ] notas preenchidas
- [ ] observações qualitativas preenchidas

### Consolidação
- [ ] médias por seção calculadas
- [ ] exemplos bons separados
- [ ] exemplos ruins separados
- [ ] síntese comparativa baseline vs rag pronta

### Texto
- [ ] seção de resultados escrita
- [ ] seção de discussão escrita
- [ ] limitações observadas descritas

## 3. Protótipo e Evidências Visuais — Pessoa C

### Teste manual
- [ ] roteiro de teste manual definido
- [ ] fluxo principal testado
- [ ] erros observados registrados
- [ ] comportamento esperado registrado

### Evidências
- [ ] screenshots da tela inicial
- [ ] screenshots da geração
- [ ] screenshots da comparação baseline vs rag
- [ ] screenshots do export
- [ ] screenshots do debug/retrieved, quando aplicável

### Texto
- [ ] descrição do protótipo escrita
- [ ] fluxo do usuário escrito
- [ ] funcionalidades principais descritas
- [ ] limitações de uso escritas

## 4. Redação do TCC

### Parte técnica
- [ ] metodologia técnica escrita
- [ ] desenvolvimento do protótipo escrito
- [ ] procedimento experimental escrito
- [ ] reprodutibilidade escrita

### Parte analítica
- [ ] resultados escritos
- [ ] discussão escrita
- [ ] limitações escritas
- [ ] conclusão escrita

### Parte visual e estrutural
- [ ] figuras inseridas
- [ ] tabelas inseridas
- [ ] screenshots inseridas
- [ ] referências revisadas
- [ ] anexos organizados

## 5. Revisão Final

### Consistência
- [ ] texto bate com o sistema real
- [ ] texto bate com os outputs reais
- [ ] texto respeita o escopo reduzido
- [ ] não há funcionalidade inventada
- [ ] não há dado inventado

### Forma
- [ ] revisão ortográfica
- [ ] padronização acadêmica
- [ ] padronização ABNT
- [ ] nomes de arquivos e anexos revisados

### Entrega
- [ ] versão final consolidada
- [ ] arquivos finais salvos
- [ ] material para defesa organizado

## 6. Escopo Real Que Deve Aparecer No Texto

O TCC deve deixar claro:
- trata-se de um protótipo funcional
- o experimento foi conduzido em escopo reduzido
- as seções avaliadas foram:
  - `POP`: `Passo a passo`, `Cuidados e Segurança`
  - `COMERCIAL`: `Detalhes essenciais`, `Benefícios (bullets)`
- a avaliação foi comparativa entre `baseline` e `rag`
- houve validação humana

## 7. Regra de Controle

Antes de considerar qualquer etapa pronta, perguntar:

“Isso está sustentado por evidência real do projeto?”

Se a resposta for:
- `sim`: manter
- `não`: revisar ou remover
