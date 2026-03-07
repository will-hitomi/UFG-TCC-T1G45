import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
CF_ACCESS_CLIENT_ID = os.getenv("CF_ACCESS_CLIENT_ID", "")
CF_ACCESS_CLIENT_SECRET = os.getenv("CF_ACCESS_CLIENT_SECRET", "")

SECTIONS = {
    "POP": [
        "Objetivo",
        "Escopo/Contexto",
        "Materiais/Ferramentas",
        "Passo a passo",
        "Cuidados e Segurança",
        "Critérios de sucesso",
    ],
    "TECNICO": [
        "Descricao (o que e)",
        "Aplicacoes/Indicacoes",
        "Especificacoes/Caracteristicas",
        "Modo de uso (objetivo e conciso)",
        "Restricoes/Compatibilidade",
        "Seguranca/Avisos essenciais",
    ],
    "COMERCIAL": [
        "Headline (beneficio principal)",
        "Beneficios (bullets)",
        "Detalhes essenciais",
        "Como usar / Como funciona (resumo)",
        "Avisos essenciais",
        "CTA (chamada para acao)",
    ],
}

CASE0_LIMPEZA = {
    "item_id": "case_0_deseng_001",
    "domain": "limpeza",
    "subcategory": "desengordurante",
    "risk_level": "medio",
    "nome": "Desengordurante multiuso",
    "descricao_curta": "Removedor de gordura para cozinhas e superficies lavaveis.",
    "publico_alvo": "pequenos negocios e uso domestico",
    "canal_venda": "marketplace",
    "atributos_comuns": [{"k": "volume", "v": "500 mL"}, {"k": "forma", "v": "liquido em borrifador"}],
    "atributos_limpeza": {
        "superficie_alvo": "azulejo, inox e superficies lavaveis",
        "diluicao": "pronto uso",
        "tempo_acao": "1 a 3 minutos",
        "compatibilidades": "inoxidavel, azulejo, plastico rigido",
        "incompatibilidades": "madeira nao selada e superficies sensiveis",
        "epi": "luvas; evitar contato com olhos",
        "observacoes": "nao informado",
    },
    "atributos_servico": {
        "escopo": "",
        "o_que_inclui": "",
        "o_que_nao_inclui": "",
        "pre_requisitos": "",
        "prazo_sla": "",
        "canal_atendimento": "",
        "sistemas_ferramentas": "",
        "politica_privacidade": "",
        "observacoes": "",
    },
}


if "input_item" not in st.session_state:
    st.session_state["input_item"] = deepcopy(CASE0_LIMPEZA)
if "input_item_text" not in st.session_state:
    st.session_state["input_item_text"] = json.dumps(st.session_state["input_item"], ensure_ascii=False, indent=2)


def get_auth_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {}
    if CF_ACCESS_CLIENT_ID and CF_ACCESS_CLIENT_SECRET:
        headers["CF-Access-Client-Id"] = CF_ACCESS_CLIENT_ID
        headers["CF-Access-Client-Secret"] = CF_ACCESS_CLIENT_SECRET
    return headers


def api_get(path: str):
    return requests.get(f"{API_BASE_URL}{path}", timeout=20, headers=get_auth_headers())


def api_post(path: str, payload: dict):
    return requests.post(f"{API_BASE_URL}{path}", json=payload, timeout=120, headers=get_auth_headers())


def call_generate(mode: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    req_payload = dict(payload)
    req_payload["mode"] = mode
    try:
        response = api_post("/generate", req_payload)
    except requests.RequestException as e:
        return {"ok": False, "status": None, "error": str(e), "raw": None}

    if response.status_code != 200:
        return {"ok": False, "status": response.status_code, "error": response.text, "raw": None}

    try:
        data = response.json()
    except ValueError:
        return {"ok": False, "status": response.status_code, "error": response.text, "raw": None}

    return {"ok": True, "status": response.status_code, "error": None, "raw": data}


def extract_section_text(result: Dict[str, Any]) -> str:
    if not result.get("ok"):
        return ""
    raw = result.get("raw") or {}
    sections = raw.get("sections") or []
    if not sections:
        return ""
    return sections[0].get("text", "")


def render_markdown(doc_type: str, item_name: str, results_by_section: Dict[str, Dict[str, Any]]) -> str:
    lines: List[str] = [f"# {doc_type} - {item_name}", ""]
    for section_name, section_result in results_by_section.items():
        lines.append(f"## {section_name}")
        text = extract_section_text(section_result)
        if text:
            lines.append(text)
        else:
            err = section_result.get("error") or "Erro ao gerar secao."
            lines.append(f"_Erro: {err}_")
        lines.append("")
    return "\n".join(lines)


def build_input_item_from_form(form_vals: Dict[str, Any]) -> Dict[str, Any]:
    domain = form_vals["domain"]
    base = {
        "item_id": form_vals["item_id"].strip() or "item_sem_id",
        "domain": domain,
        "subcategory": form_vals["subcategory"].strip(),
        "risk_level": form_vals.get("risk_level", "medio"),
        "nome": form_vals["nome"].strip(),
        "descricao_curta": form_vals["descricao_curta"].strip(),
        "publico_alvo": form_vals["publico_alvo"].strip(),
        "canal_venda": form_vals["canal_venda"].strip(),
        "atributos_comuns": form_vals.get("atributos_comuns", []),
        "atributos_limpeza": {
            "superficie_alvo": form_vals.get("superficie_alvo", "").strip(),
            "diluicao": form_vals.get("diluicao", "").strip(),
            "tempo_acao": form_vals.get("tempo_acao", "").strip(),
            "compatibilidades": form_vals.get("compatibilidades", "").strip(),
            "incompatibilidades": form_vals.get("incompatibilidades", "").strip(),
            "epi": form_vals.get("epi", "").strip(),
            "observacoes": form_vals.get("observacoes_limpeza", "").strip(),
        },
        "atributos_servico": {
            "escopo": form_vals.get("escopo", "").strip(),
            "o_que_inclui": form_vals.get("o_que_inclui", "").strip(),
            "o_que_nao_inclui": form_vals.get("o_que_nao_inclui", "").strip(),
            "pre_requisitos": form_vals.get("pre_requisitos", "").strip(),
            "prazo_sla": form_vals.get("prazo_sla", "").strip(),
            "canal_atendimento": form_vals.get("canal_atendimento", "").strip(),
            "sistemas_ferramentas": form_vals.get("sistemas_ferramentas", "").strip(),
            "politica_privacidade": form_vals.get("politica_privacidade", "").strip(),
            "observacoes": form_vals.get("observacoes_servico", "").strip(),
        },
    }
    return base


def export_outputs(
    doc_type: str,
    input_item: Dict[str, Any],
    baseline_results: Dict[str, Any],
    rag_results: Dict[str, Any],
    baseline_md: str,
    rag_md: str,
) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path("data/outputs") / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_json = {
        "mode": "baseline",
        "doc_type": doc_type,
        "item_id": input_item.get("item_id", ""),
        "input_item": input_item,
        "results_by_section": baseline_results,
    }
    rag_json = {
        "mode": "rag",
        "doc_type": doc_type,
        "item_id": input_item.get("item_id", ""),
        "input_item": input_item,
        "results_by_section": rag_results,
    }

    (out_dir / "baseline.json").write_text(json.dumps(baseline_json, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "rag.json").write_text(json.dumps(rag_json, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "baseline.md").write_text(baseline_md, encoding="utf-8")
    (out_dir / "rag.md").write_text(rag_md, encoding="utf-8")
    return out_dir


st.set_page_config(page_title="TCPOPAI", layout="wide")
st.title("TCPOPAI - Comparacao Baseline x RAG (multiplas secoes)")

st.subheader("Conexao")
st.write("API_BASE_URL:", API_BASE_URL)
if st.button("Testar /health"):
    try:
        r = api_get("/health")
        st.write("Status:", r.status_code)
        st.code(r.text)
    except requests.RequestException as e:
        st.error(f"Falha de conexao com API: {e}")

st.subheader("Configuracao")
doc_type = st.selectbox("Doc type", ["POP", "TECNICO", "COMERCIAL"], index=1)
default_section = "Modo de uso (objetivo e conciso)" if doc_type == "TECNICO" else SECTIONS[doc_type][0]
sections_selected = st.multiselect("Secoes", SECTIONS[doc_type], default=[default_section])
top_k = st.slider("top_k", 1, 10, 3)

st.subheader("InputItem")
if st.button("Carregar Caso 0 (Limpeza)"):
    st.session_state["input_item"] = deepcopy(CASE0_LIMPEZA)
    st.session_state["input_item_text"] = json.dumps(st.session_state["input_item"], ensure_ascii=False, indent=2)

item_from_state = st.session_state.get("input_item", deepcopy(CASE0_LIMPEZA))

with st.expander("Modo padrao (formulario guiado)", expanded=True):
    domain = st.selectbox("domain", ["limpeza", "servicos_operacionais"], index=0 if item_from_state.get("domain") == "limpeza" else 1)
    subcategory = st.text_input("subcategory", value=item_from_state.get("subcategory", ""))
    item_id = st.text_input("item_id", value=item_from_state.get("item_id", ""))
    nome = st.text_input("nome", value=item_from_state.get("nome", ""))
    descricao_curta = st.text_area("descricao_curta", value=item_from_state.get("descricao_curta", ""), height=80)
    publico_alvo = st.text_input("publico_alvo", value=item_from_state.get("publico_alvo", ""))
    canal_venda = st.text_input("canal_venda", value=item_from_state.get("canal_venda", ""))

    atributos_limpeza = item_from_state.get("atributos_limpeza", {})
    atributos_servico = item_from_state.get("atributos_servico", {})

    if domain == "limpeza":
        st.markdown("**Campos de limpeza**")
        superficie_alvo = st.text_input("superficie_alvo", value=atributos_limpeza.get("superficie_alvo", ""))
        diluicao = st.text_input("diluicao", value=atributos_limpeza.get("diluicao", ""))
        tempo_acao = st.text_input("tempo_acao", value=atributos_limpeza.get("tempo_acao", ""))
        incompatibilidades = st.text_input("incompatibilidades", value=atributos_limpeza.get("incompatibilidades", ""))
        epi = st.text_input("epi", value=atributos_limpeza.get("epi", ""))
        compatibilidades = st.text_input("compatibilidades", value=atributos_limpeza.get("compatibilidades", ""))
        observacoes_limpeza = st.text_input("observacoes_limpeza", value=atributos_limpeza.get("observacoes", ""))

        escopo = o_que_inclui = o_que_nao_inclui = pre_requisitos = ""
        prazo_sla = canal_atendimento = sistemas_ferramentas = politica_privacidade = ""
        observacoes_servico = ""
    else:
        st.markdown("**Campos de servicos**")
        escopo = st.text_input("escopo", value=atributos_servico.get("escopo", ""))
        o_que_inclui = st.text_input("o_que_inclui", value=atributos_servico.get("o_que_inclui", ""))
        o_que_nao_inclui = st.text_input("o_que_nao_inclui", value=atributos_servico.get("o_que_nao_inclui", ""))
        pre_requisitos = st.text_input("pre_requisitos", value=atributos_servico.get("pre_requisitos", ""))
        prazo_sla = st.text_input("prazo_sla", value=atributos_servico.get("prazo_sla", ""))
        canal_atendimento = st.text_input("canal_atendimento", value=atributos_servico.get("canal_atendimento", ""))
        politica_privacidade = st.text_input("politica_privacidade", value=atributos_servico.get("politica_privacidade", ""))
        sistemas_ferramentas = st.text_input("sistemas_ferramentas", value=atributos_servico.get("sistemas_ferramentas", ""))
        observacoes_servico = st.text_input("observacoes_servico", value=atributos_servico.get("observacoes", ""))

        superficie_alvo = diluicao = tempo_acao = incompatibilidades = epi = ""
        compatibilidades = observacoes_limpeza = ""

    if st.button("Atualizar JSON"):
        form_vals = {
            "domain": domain,
            "subcategory": subcategory,
            "item_id": item_id,
            "nome": nome,
            "descricao_curta": descricao_curta,
            "publico_alvo": publico_alvo,
            "canal_venda": canal_venda,
            "superficie_alvo": superficie_alvo,
            "diluicao": diluicao,
            "tempo_acao": tempo_acao,
            "incompatibilidades": incompatibilidades,
            "epi": epi,
            "compatibilidades": compatibilidades,
            "observacoes_limpeza": observacoes_limpeza,
            "escopo": escopo,
            "o_que_inclui": o_que_inclui,
            "o_que_nao_inclui": o_que_nao_inclui,
            "pre_requisitos": pre_requisitos,
            "prazo_sla": prazo_sla,
            "canal_atendimento": canal_atendimento,
            "politica_privacidade": politica_privacidade,
            "sistemas_ferramentas": sistemas_ferramentas,
            "observacoes_servico": observacoes_servico,
        }
        built = build_input_item_from_form(form_vals)
        st.session_state["input_item"] = built
        st.session_state["input_item_text"] = json.dumps(built, ensure_ascii=False, indent=2)
        st.success("JSON atualizado com base no formulario.")

st.markdown("**Modo avancado (JSON)**")
st.text_area("InputItem JSON", key="input_item_text", height=320)

if st.button("Gerar secoes selecionadas"):
    if not sections_selected:
        st.error("Selecione ao menos uma secao.")
        st.stop()

    try:
        input_item = json.loads(st.session_state["input_item_text"])
    except json.JSONDecodeError as e:
        st.error(f"JSON invalido no InputItem: {e}")
        st.stop()

    base_payload = {
        "domain": input_item.get("domain"),
        "subcategory": input_item.get("subcategory"),
        "doc_type": doc_type,
        "input_item": input_item,
        "top_k": top_k,
    }

    baseline_results: Dict[str, Dict[str, Any]] = {}
    rag_results: Dict[str, Dict[str, Any]] = {}
    progress = st.progress(0)

    with st.status("Gerando secoes...", expanded=True) as status:
        total = len(sections_selected)
        for i, section in enumerate(sections_selected, start=1):
            status.update(label=f"Gerando secao {i}/{total}: {section}", state="running")
            payload = dict(base_payload)
            payload["section"] = section

            baseline_results[section] = call_generate("baseline", payload)
            rag_results[section] = call_generate("rag", payload)

            if not baseline_results[section]["ok"]:
                st.warning(f"Baseline falhou em '{section}': {baseline_results[section]['error']}")
            if not rag_results[section]["ok"]:
                st.warning(f"RAG falhou em '{section}': {rag_results[section]['error']}")

            progress.progress(i / total)

        status.update(label="Geracao concluida.", state="complete")

    success_baseline = sum(1 for r in baseline_results.values() if r.get("ok"))
    success_rag = sum(1 for r in rag_results.values() if r.get("ok"))

    baseline_md = render_markdown(doc_type, input_item.get("nome", "Item sem nome"), baseline_results)
    rag_md = render_markdown(doc_type, input_item.get("nome", "Item sem nome"), rag_results)

    st.session_state["generated"] = {
        "doc_type": doc_type,
        "sections_selected": sections_selected,
        "input_item": input_item,
        "baseline_results": baseline_results,
        "rag_results": rag_results,
        "success_baseline": success_baseline,
        "success_rag": success_rag,
        "baseline_md": baseline_md,
        "rag_md": rag_md,
    }

if "generated" in st.session_state:
    gen = st.session_state["generated"]
    st.subheader("Resumo")
    st.write(
        f"Secoes com sucesso - Baseline: {gen['success_baseline']}/{len(gen['sections_selected'])} | "
        f"RAG: {gen['success_rag']}/{len(gen['sections_selected'])}"
    )

    st.subheader("Comparacao por secao")
    left_col, right_col = st.columns(2)

    for section in gen["sections_selected"]:
        baseline_result = gen["baseline_results"].get(section, {})
        rag_result = gen["rag_results"].get(section, {})

        with left_col:
            st.markdown(f"### Baseline - {section}")
            if baseline_result.get("ok"):
                st.write(extract_section_text(baseline_result))
            else:
                st.error(f"Erro ({baseline_result.get('status')}): {baseline_result.get('error')}")

        with right_col:
            st.markdown(f"### RAG - {section}")
            if rag_result.get("ok"):
                st.write(extract_section_text(rag_result))
                retrieved = ((rag_result.get("raw") or {}).get("debug") or {}).get("retrieved")
                if retrieved:
                    st.caption("debug.retrieved")
                    st.json(retrieved)
            else:
                st.error(f"Erro ({rag_result.get('status')}): {rag_result.get('error')}")

    st.subheader("Markdown final (sem LLM extra)")
    md_left, md_right = st.columns(2)
    with md_left:
        st.markdown("#### Baseline MD")
        st.code(gen["baseline_md"], language="markdown")
    with md_right:
        st.markdown("#### RAG MD")
        st.code(gen["rag_md"], language="markdown")

    if st.button("Exportar"):
        out_dir = export_outputs(
            doc_type=gen["doc_type"],
            input_item=gen["input_item"],
            baseline_results=gen["baseline_results"],
            rag_results=gen["rag_results"],
            baseline_md=gen["baseline_md"],
            rag_md=gen["rag_md"],
        )
        st.success(f"Export concluido em: {out_dir}")
