import os, json, requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

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
  "item_id":"case_0_deseng_001",
  "domain":"limpeza",
  "subcategory":"desengordurante",
  "risk_level":"medio",
  "nome":"Desengordurante multiuso",
  "descricao_curta":"Removedor de gordura para cozinhas e superfícies laváveis.",
  "publico_alvo":"pequenos negócios e uso doméstico",
  "canal_venda":"marketplace",
  "atributos_comuns":[{"k":"volume","v":"500 mL"},{"k":"forma","v":"líquido em borrifador"}],
  "atributos_limpeza":{
    "superficie_alvo":"azulejo, inox e superfícies laváveis",
    "diluicao":"pronto uso",
    "tempo_acao":"1 a 3 minutos",
    "compatibilidades":"inoxidável, azulejo, plástico rígido",
    "incompatibilidades":"madeira não selada e superfícies sensíveis",
    "epi":"luvas; evitar contato com olhos",
    "observacoes":"não informado"
  },
  "atributos_servico":{
    "escopo":"","o_que_inclui":"","o_que_nao_inclui":"","pre_requisitos":"",
    "prazo_sla":"","canal_atendimento":"","sistemas_ferramentas":"",
    "politica_privacidade":"","observacoes":""
  }
}

def api_get(path: str):
    return requests.get(f"{API_BASE_URL}{path}", timeout=20)

def api_post(path: str, payload: dict):
    return requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=60)

st.set_page_config(page_title="TCPOPAI", layout="wide")
st.title("TCPOPAI — UI mínima (geração por seção)")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Conexão")
    st.write("API_BASE_URL:", API_BASE_URL)
    if st.button("Testar /health"):
        r = api_get("/health")
        st.code(r.text)

    st.subheader("Config de geração")
    mode = st.selectbox("Mode", ["baseline", "rag"], index=1)
    doc_type = st.selectbox("Doc type", ["POP", "TECNICO", "COMERCIAL"], index=1)
    section = st.selectbox("Seção", SECTIONS[doc_type], index=SECTIONS[doc_type].index("Modo de uso (objetivo e conciso)") if doc_type=="TECNICO" else 0)
    top_k = st.slider("top_k", 1, 8, 3)

with col2:
    st.subheader("InputItem (JSON)")
    if st.button("Carregar Caso 0 (Limpeza)"):
        st.session_state["input_item"] = CASE0_LIMPEZA

    input_item = st.session_state.get("input_item", CASE0_LIMPEZA)
    input_item_text = st.text_area("Edite se quiser:", value=json.dumps(input_item, ensure_ascii=False, indent=2), height=360)

    st.subheader("Ação")
    if st.button("Gerar seção"):
        item = json.loads(input_item_text)
        payload = {
            "mode": mode,
            "domain": item.get("domain"),
            "subcategory": item.get("subcategory"),
            "doc_type": doc_type,
            "section": section,
            "input_item": item,
            "top_k": top_k
        }
        r = api_post("/generate", payload)
        st.write("Status:", r.status_code)
        st.code(r.text)
