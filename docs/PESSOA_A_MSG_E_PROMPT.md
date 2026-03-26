# Pessoa A — Mensagem e Prompt

## Mensagem de WhatsApp

```text
Oi. Ajustei a divisão do TCC para eu assumir toda a parte técnica e você ficar focado só na parte de avaliação e resultados.

Sua responsabilidade agora é:
1. avaliar os outputs baseline vs rag
2. aplicar a rubrica
3. consolidar notas e observações
4. escrever a parte de resultados e discussão

O que eu vou te entregar:
- summary_wide.csv
- baseline_run.md
- rag_run.md
- outputs finais do experimento

O que eu preciso de você:
- planilha de avaliação humana
- médias por seção
- exemplos bons/ruins
- texto de resultados
- texto de discussão

Você não precisa mexer em código, deploy, API, KB nem scripts.
Seu foco é análise e escrita.

Quero que você use o chat compartilhado para acelerar isso, mas sem inventar dado. Trabalhe só em cima dos outputs reais que eu te passar.
```

## Prompt Para o GPT Compartilhado

```text
Estou trabalhando na parte de avaliação e resultados do TCC.

Contexto:
- Tema: uso de LLM + RAG para gerar POPs e textos comerciais para negócios online
- Comparação principal: baseline vs rag
- Escopo do experimento:
  - POP: Passo a passo / Cuidados e Segurança
  - COMERCIAL: Detalhes essenciais / Benefícios (bullets)

Minha função:
- avaliar os outputs
- comparar baseline vs rag
- escrever resultados e discussão

Quero ajuda para:
1. montar ou revisar a rubrica
2. estruturar a avaliação humana
3. escrever observações qualitativas
4. transformar isso em texto acadêmico

Importante:
- não inventar dados
- usar apenas as evidências que eu enviar
- respeitar o escopo reduzido do experimento
- escrever em português acadêmico, claro e objetivo
```
