# SPEC.md — TCC IA Generativa (Gate 3/Dev) — v0.2 (Limpeza + Serviços Operacionais)

## 0) Objetivo
Construir um protótipo que gere, a partir de um cadastro estruturado:
- **POP**
- **Texto técnico / técnico-comercial**
- **Descrição comercial**

Usando:
- **RAG por seção** (recuperação semântica segmentada)
- **LLM** para geração
- **validação humana** como etapa final

Avaliação comparativa:
- **Humano** vs **LLM baseline (sem RAG)** vs **App (RAG por seção)**

Domínios iniciais:
1) **Limpeza (produtos)**  
2) **Serviços operacionais (processos)**

---

## 1) Papéis e entregáveis (Definition of Done)

### Pessoa A — Base de conhecimento + Gold standard + Avaliação
**DoD A**
- Dataset `data/knowledge_base.jsonl` (seções) cobrindo os 2 domínios (mínimo 40 itens equivalentes)
- `data/test_cases.jsonl` (mínimo 12 casos de teste)
- Rubrica v1 (1–5) + script `eval/evaluate.py` (lote) + relatório simples (CSV/JSON)

### Pessoa B — RAG (embeddings + Chroma + orquestração)
**DoD B**
- Indexador `src/rag/index_kb.py` (JSONL → embeddings → Chroma persistente)
- `src/rag/retrieve.py` com `retrieve_by_section(...)` estável
- Config por `.env` + logs mínimos

### Pessoa C — LLM + prompts + interface
**DoD C**
- `src/llm/generate.py` com `generate_section(...)` (baseline vs rag)
- Prompts por doc_type/section (e variações por domínio quando necessário)
- UI Streamlit: cadastrar item, gerar (baseline/rag), editar, exportar JSON+MD

---

## 2) Estrutura do repositório

repo/
SPEC.md
data/
knowledge_base.jsonl
test_cases.jsonl
outputs/
src/
common/
schemas.py
utils.py
rag/
index_kb.py
retrieve.py
llm/
prompts/
pop.yaml
tecnico.yaml
comercial.yaml
generate.py
app/
ui_streamlit.py
eval/
rubric.md
evaluate.py
chroma_db/ # persistência local (gitignored)
.env.example
requirements.txt


---

## 3) Taxonomia (domínios, categorias e risco)

### 3.1 Domínios (obrigatório)
- `domain`: `limpeza` | `servicos_operacionais`

### 3.2 Subcategorias iniciais (v1)
**Limpeza**
- `desengordurante`
- `desinfetante`
- `detergente`
- `limpa_vidros`
- `tira_manchas`

**Serviços operacionais**
- `cadastro_produtos`
- `atendimento_whatsapp`
- `pos_venda_troca_devolucao`
- `integracao_marketplace`
- `suporte_operacional_basico`

### 3.3 Nível de risco (recomendado)
- `risk_level`: `baixo` | `medio` | `alto`
> Útil sobretudo em limpeza para reforçar seção de segurança.

---

## 4) Contrato de dados (Entrada / Saída)

### 4.1 InputItem (entrada do usuário)
Formato canônico:

```json
{
  "item_id": "string",
  "domain": "limpeza",
  "subcategory": "desengordurante",
  "risk_level": "medio",

  "nome": "string",
  "descricao_curta": "string",
  "publico_alvo": "string",
  "canal_venda": "marketplace",

  "atributos_comuns": [{"k":"string","v":"string"}],

  "atributos_limpeza": {
    "superficie_alvo": "string",
    "diluicao": "string",
    "tempo_acao": "string",
    "compatibilidades": "string",
    "incompatibilidades": "string",
    "epi": "string",
    "observacoes": "string"
  },

  "atributos_servico": {
    "escopo": "string",
    "o_que_inclui": "string",
    "o_que_nao_inclui": "string",
    "pre_requisitos": "string",
    "prazo_sla": "string",
    "canal_atendimento": "string",
    "sistemas_ferramentas": "string",
    "politica_privacidade": "string",
    "observacoes": "string"
  }
}
