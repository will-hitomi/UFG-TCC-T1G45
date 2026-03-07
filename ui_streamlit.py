import os
import json
import time
import requests
import streamlit as st

# ================= CONFIG ================= #

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="TCPOPAI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= CUSTOM CSS ================= #

st.markdown("""
<style>
.stApp {
    background-color: #0e1117;
    color: #ffffff;
}

.section-card {
    background-color: #161b22;
    padding: 25px;
    border-radius: 12px;
    border: 1px solid #30363d;
    margin-bottom: 20px;
}

.mode-indicator {
    font-size: 14px;
    font-weight: 600;
    color: #3fb950;
}

.json-toggle-on button {
    background-color: #2f81f7 !important;
    color: white !important;
}

.json-toggle-off button {
    background-color: #21262d !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ================= DATA ================= #

SECTIONS = {
    "POP": [
        "Objetivo", "Escopo/Contexto", "Materiais/Ferramentas", "Passo a passo",
        "Cuidados e Segurança", "Critérios de sucesso"
    ],
    "TECNICO": [
        "Descrição (o que é)", "Aplicações/Indicações", "Especificações/Características",
        "Modo de uso (objetivo e conciso)", "Restrições/Compatibilidade", "Segurança/Avisos essenciais"
    ],
    "COMERCIAL": [
        "Headline (benefício principal)", "Benefícios (bullets)", "Detalhes essenciais",
        "Como usar / Como funciona (resumo)", "Avisos essenciais", "CTA (chamada para ação)"
    ]
}

CASE0_LIMPEZA = {
    "item_id": "case_0_deseng_001",
    "domain": "limpeza",
    "subcategory": "desengordurante",
    "risk_level": "medio",
    "nome": "Desengordurante multiuso",
    "descricao_curta": "Removedor de gordura para cozinhas e superfícies laváveis.",
    "publico_alvo": "pequenos negócios e uso doméstico",
    "canal_venda": "marketplace",
    "atributos_limpeza": {
        "tempo_acao": "1 a 3 minutos",
        "compatibilidades": "inoxidável, azulejo, plástico rígido",
        "epi": "luvas; evitar contato com olhos"
    }
}

# ================= FUTURA INTEGRAÇÃO API ================= #

def api_post(path: str, payload: dict):
    return requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=60)


# ================= MOCK + GANCHO API ================= #

def generate_baseline(item, doc_type, section):

    payload = {
        "mode": "baseline",
        "domain": item.get("domain"),
        "subcategory": item.get("subcategory"),
        "doc_type": doc_type,
        "section": section,
        "input_item": item,
        "top_k": 0
    }

    # INCLUIR DEPOIS
    # response = api_post("/generate", payload)
    # return response.json()

    time.sleep(1)

    return {
        "mode": "baseline",
        "text": f"""
### {section}

**Produto:** {item['nome']}

**Descrição:** {item['descricao_curta']}

**Público-alvo:** {item['publico_alvo']}

Esta é uma geração BASELINE simulada (offline).
"""
    }


def generate_rag(item, doc_type, section, top_k):

    payload = {
        "mode": "rag",
        "domain": item.get("domain"),
        "subcategory": item.get("subcategory"),
        "doc_type": doc_type,
        "section": section,
        "input_item": item,
        "top_k": top_k
    }

    # INCLUIR DEPOIS
    # response = api_post("/generate", payload)
    # return response.json()

    time.sleep(1)

    retrieved = [
        {"source": "kb_limpeza_001.md", "score": 0.88},
        {"source": "kb_segurança_002.md", "score": 0.83}
    ][:top_k]

    return {
        "mode": "rag",
        "text": f"""
### {section}

**Produto:** {item['nome']}

Baseado em boas práticas do setor:

- Tempo de ação: {item['atributos_limpeza']['tempo_acao']}
- Compatibilidades: {item['atributos_limpeza']['compatibilidades']}
- EPI: {item['atributos_limpeza']['epi']}

Geração RAG simulada (offline).
""",
        "debug": {"retrieved": retrieved}
    }


# ================= HEADER ================= #

col_title, col_mode = st.columns([6, 1])
with col_title:
    st.title("TCPOPAI")
with col_mode:
    st.markdown('<div class="mode-indicator">🟢 Modo Offline</div>', unsafe_allow_html=True)

st.divider()

# ================= SIDEBAR ================= #

with st.sidebar:
    st.header("Configuração")

    doc_type = st.selectbox("Doc Type", ["POP", "TECNICO", "COMERCIAL"])
    section = st.selectbox("Seção", SECTIONS[doc_type])
    top_k = st.slider("top_k (RAG)", 1, 5, 2)

    if st.button("Carregar Caso 0 (Limpeza)"):
        st.session_state["item"] = CASE0_LIMPEZA

    # Inicializa estado toggle
    if "show_json" not in st.session_state:
        st.session_state["show_json"] = False

    # Toggle manual
    if st.session_state["show_json"]:
        toggle_class = "json-toggle-on"
    else:
        toggle_class = "json-toggle-off"

    st.markdown(f'<div class="{toggle_class}">', unsafe_allow_html=True)
    if st.button("Exibir Json"):
        st.session_state["show_json"] = not st.session_state["show_json"]
    st.markdown('</div>', unsafe_allow_html=True)

# ================= MAIN AREA ================= #

item = st.session_state.get("item", CASE0_LIMPEZA)

# -------- JSON EDITOR TOGGLE -------- #

if st.session_state["show_json"]:
    st.subheader("Edite se quiser:")
    json_text = st.text_area(
        "",
        value=json.dumps(item, ensure_ascii=False, indent=2),
        height=350
    )

    try:
        st.session_state["item"] = json.loads(json_text)
    except:
        st.error("JSON inválido")

    st.divider()

# ================= TABS ================= #

tabs = st.tabs(["Baseline", "RAG"])

# ================= BASELINE ================= #

with tabs[0]:

    if st.button("Gerar Baseline"):
        with st.spinner("Gerando conteúdo..."):
            st.session_state["baseline"] = generate_baseline(
                st.session_state.get("item", CASE0_LIMPEZA),
                doc_type,
                section
            )

    if "baseline" in st.session_state:
        result = st.session_state["baseline"]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(result["text"])
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="⬇ Download Resultado",
            data=result["text"],
            file_name="baseline_resultado.md"
        )

# ================= RAG ================= #

with tabs[1]:

    if st.button("Gerar RAG"):
        with st.spinner("Gerando conteúdo com RAG..."):
            st.session_state["rag"] = generate_rag(
                st.session_state.get("item", CASE0_LIMPEZA),
                doc_type,
                section,
                top_k
            )

    if "rag" in st.session_state:
        result = st.session_state["rag"]

        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(result["text"])
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("Debug - Retrieved Data"):
            st.json(result["debug"]["retrieved"])

        st.download_button(
            label="⬇ Download Resultado",
            data=result["text"],
            file_name="rag_resultado.md"
        )
            