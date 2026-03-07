import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests
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


def generate_baseline(payload: dict):
    req = dict(payload)
    req["mode"] = "baseline"
    return api_post("/generate", req)


def generate_rag(payload: dict):
    req = dict(payload)
    req["mode"] = "rag"
    return api_post("/generate", req)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    return cleaned.strip("_") or "output"


def save_outputs(payload: dict, response_data: dict) -> tuple[Path, Path]:
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)

    item_id = response_data.get("item_id") or payload.get("input_item", {}).get("item_id", "item")
    doc_type = response_data.get("doc_type", payload.get("doc_type", "DOC"))
    section = response_data.get("sections", [{}])[0].get("name", payload.get("section", "secao"))
    text = response_data.get("sections", [{}])[0].get("text", "")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = f"{timestamp}_{slugify(str(item_id))}_{slugify(str(doc_type))}_{slugify(str(section))}"

    md_path = out_dir / f"{stem}.md"
    json_path = out_dir / f"{stem}.json"

    md_content = (
        f"# {section}\n\n"
        f"- item_id: {item_id}\n"
        f"- doc_type: {doc_type}\n"
        f"- language: {response_data.get('language', 'pt-BR')}\n\n"
        f"{text}\n"
    )
    md_path.write_text(md_content, encoding="utf-8")
    json_path.write_text(json.dumps(response_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return md_path, json_path


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
        try:
            item = json.loads(input_item_text)
        except json.JSONDecodeError as e:
            st.error(f"JSON inválido no InputItem: {e}")
            st.stop()

        payload = {
            "mode": mode,
            "domain": item.get("domain"),
            "subcategory": item.get("subcategory"),
            "doc_type": doc_type,
            "section": section,
            "input_item": item,
            "top_k": top_k
        }
        response = generate_baseline(payload) if mode == "baseline" else generate_rag(payload)
        st.write("Status:", response.status_code)

        if response.status_code != 200:
            st.error("Falha ao gerar seção. Verifique os detalhes retornados pela API.")
            st.code(response.text)
            st.stop()

        try:
            data = response.json()
        except ValueError:
            st.error("Resposta da API não está em JSON válido.")
            st.code(response.text)
            st.stop()

        generated_text = data.get("sections", [{}])[0].get("text", "")
        st.subheader("Texto gerado")
        st.write(generated_text if generated_text else "(vazio)")

        debug = data.get("debug") or {}
        if debug.get("retrieved"):
            st.subheader("debug.retrieved")
            st.json(debug.get("retrieved"))

        st.session_state["last_generate_payload"] = payload
        st.session_state["last_generate_response"] = data

    if st.button("Salvar em data/outputs/"):
        payload = st.session_state.get("last_generate_payload")
        response_data = st.session_state.get("last_generate_response")
        if not payload or not response_data:
            st.warning("Gere uma seção primeiro para salvar o resultado.")
        else:
            md_path, json_path = save_outputs(payload, response_data)
            st.success(f"Arquivos salvos: {md_path} e {json_path}")
