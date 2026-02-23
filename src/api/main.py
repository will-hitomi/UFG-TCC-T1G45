import os
import json
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Any, Dict, Literal, Optional

from src.rag.index_kb import index_kb
from src.rag.retrieve import retrieve_by_section

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain

from src.llm.llm_client import get_llm

from pathlib import Path
from dotenv import load_dotenv
ROOT = Path(__file__).resolve().parents[2]  # .../TCPOPAI
load_dotenv(ROOT / ".env")

print("LLM_BASE_URL =", os.getenv("LLM_BASE_URL"))
print("LLM_MODEL    =", os.getenv("LLM_MODEL"))
print("LLM_API_KEY  =", "OK" if os.getenv("LLM_API_KEY") else "MISSING")

app = FastAPI()

PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "Você escreve em pt-BR. Gere SOMENTE a seção solicitada. "
     "Não invente números, certificações, composição ou compatibilidades. "
     "Se faltar dado, escreva 'não informado' e liste pendências em notas."),
    ("user",
     "Tarefa: gerar a seção '{section}' do documento '{doc_type}'.\n\n"
     "DADOS DO ITEM (JSON):\n{input_item}\n\n"
     "EXEMPLOS RECUPERADOS:\n{context}\n\n"
     "Use os EXEMPLOS recuperados como referência de estrutura e estilo.\n"
     "Entregue apenas o texto da seção, sem título extra."
     "Não adicione etapas, avisos ou características que não estejam no input_item ou nos documentos recuperados. "
     "Se faltar informação, escreva 'não informado' (sem inventar)."
    )
])


class IndexRequest(BaseModel):
    kb_path: str = "data/knowledge_base.jsonl"
    rebuild: bool = True

class RetrieveRequest(BaseModel):
    query: str
    domain: str
    subcategory: Optional[str] = None
    doc_type: str
    section: str
    top_k: int = 5
    filters: Optional[Dict[str, Any]] = None

 
class LLMParams(BaseModel):
    temperature: float = 0.2
    max_tokens: int = 700


class GenerateRequest(BaseModel):
    mode: Literal["baseline", "rag"]
    domain: str
    subcategory: Optional[str] = None
    doc_type: Literal["POP", "TECNICO", "COMERCIAL"]
    section: str
    input_item: Dict[str, Any]
    top_k: int = 5
    llm: Optional[LLMParams] = None
   
def build_retrieve_query(input_item: Dict[str, Any], section: str) -> str:
    # Mantém simples e robusto: nome + desc + seção + campos relevantes por domínio
    domain = input_item.get("domain", "")
    nome = input_item.get("nome", "")
    desc = input_item.get("descricao_curta", "")
    publico = input_item.get("publico_alvo", "")

    parts = [section, nome, desc, publico]

    if domain == "limpeza":
        a = input_item.get("atributos_limpeza", {}) or {}
        parts += [
            a.get("superficie_alvo",""),
            a.get("diluicao",""),
            a.get("tempo_acao",""),
            a.get("epi",""),
            a.get("incompatibilidades",""),
        ]
    elif domain == "servicos_operacionais":
        a = input_item.get("atributos_servico", {}) or {}
        parts += [
            a.get("escopo",""),
            a.get("o_que_inclui",""),
            a.get("pre_requisitos",""),
            a.get("prazo_sla",""),
            a.get("politica_privacidade",""),
        ]

    return ". ".join([p for p in parts if p and str(p).strip()])


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/retrieve")
def retrieve(req: RetrieveRequest):
    try:
        results = retrieve_by_section(
            query=req.query,
            domain=req.domain,
            subcategory=req.subcategory,
            doc_type=req.doc_type,
            section=req.section,
            top_k=req.top_k,
            filters=req.filters,
        )
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"runtime_error: {e}")


@app.post("/index")
def index(req: IndexRequest, request: Request):
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    embedding_model = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    client_ip = request.client.host
    if client_ip not in ("127.0.0.1", "::1"):
        raise HTTPException(status_code=403, detail="forbidden")

    try:
        n = index_kb(
            kb_path=req.kb_path,
            chroma_path=chroma_path,
            embedding_model_name=embedding_model,
            rebuild=req.rebuild
        )
        return {"status": "indexed", "kb_path": req.kb_path, "records_indexed": n}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"runtime_error: {e}")
    
@app.post("/admin/index")
def admin_index(req: IndexRequest):
    return index(req)   # reaproveita a mesma função do /index, mas sem expor o endpoint publicamente

@app.post("/generate")
def generate(req: GenerateRequest):
    try:
        llm_temperature = req.llm.temperature if req.llm else 0.2
        llm_max_tokens = req.llm.max_tokens if req.llm else 700
        llm = get_llm(temperature=llm_temperature, max_tokens=llm_max_tokens)

        retrieved = []
        docs = []

        if req.mode == "rag":
            query = build_retrieve_query(req.input_item, req.section)
            results = retrieve_by_section(
                query=query,
                domain=req.domain,
                subcategory=req.subcategory,
                doc_type=req.doc_type,
                section=req.section,
                top_k=req.top_k,
                filters=None,
            )
            retrieved = [{"id": r["metadata"].get("id"), "score": r["score"]} for r in results]

            docs = [
                Document(
                    page_content=r["text"],
                    metadata={**(r.get("metadata") or {}), "score": r.get("score")}
                )
                for r in results
            ]

        # "stuff chain": concatena docs no contexto
        chain = create_stuff_documents_chain(llm, PROMPT)

        input_item_str = json.dumps(req.input_item, ensure_ascii=False, indent=2)

        # Mesmo no baseline, passamos docs vazios; contexto fica vazio e gera com input_item
        text = chain.invoke({
            "context": docs,
            "section": req.section,
            "doc_type": req.doc_type,
            "input_item": input_item_str
        })

        # notes simples: se o usuário deixou algo como "não informado", a seção pode precisar revisão
        notes = []
        if "não informado" in str(text).lower():
            notes.append("Há campos marcados como 'não informado'. Recomenda-se revisar e completar dados do item.")

        return {
            "item_id": req.input_item.get("item_id", ""),
            "doc_type": req.doc_type,
            "language": "pt-BR",
            "sections": [{"name": req.section, "text": text}],
            "notes": notes,
            "debug": {
                "mode": req.mode,
                "top_k": req.top_k,
                "retrieved": retrieved
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"runtime_error: {e}")
