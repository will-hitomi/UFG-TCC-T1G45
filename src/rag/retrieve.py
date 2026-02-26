import os
from typing import Any, Dict, List, Optional

import chromadb
from sentence_transformers import SentenceTransformer


# Cache simples do modelo (evita recarregar a cada request)
_MODEL: Optional[SentenceTransformer] = None


def _get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        _MODEL = SentenceTransformer(name)
    return _MODEL


def _build_where(
    domain: str,
    doc_type: str,
    section: str,
    subcategory: Optional[str] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Monta o 'where' do Chroma.
    - domain/doc_type/section: obrigatórios
    - subcategory: opcional
    - filters: ex. {"source": ["autores","manual"]}
    """
    clauses: List[Dict[str, Any]] = [
        {"domain": {"$eq": domain}},
        {"doc_type": {"$eq": doc_type}},
        {"section": {"$eq": section}},
    ]
    if subcategory:
        clauses.append({"subcategory": {"$eq": subcategory}})

    if filters:
        # exemplo suportado: source: ["autores","manual"]
        for k, v in filters.items():
            if v is None:
                continue
            if isinstance(v, list):
                clauses.append({k: {"$in": v}})
            else:
                clauses.append({k: {"$eq": v}})

    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


def retrieve_by_section(
    query: str,
    domain: str,
    doc_type: str,
    section: str,
    subcategory: Optional[str] = None,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    collection_name = os.getenv("CHROMA_COLLECTION", "kb_sections")

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=collection_name)

    model = _get_model()
    q_emb = model.encode([query], normalize_embeddings=True, show_progress_bar=False).tolist()

    where = _build_where(
        domain=domain,
        doc_type=doc_type,
        section=section,
        subcategory=subcategory,
        filters=filters,
    )

    res = collection.query(
        query_embeddings=q_emb,
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma retorna listas aninhadas (1 query -> index 0)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    results: List[Dict[str, Any]] = []
    for doc, meta, dist in zip(docs, metas, dists):
        # Para cosine, distância costuma ser (1 - similaridade) quando embeddings normalizados
        score = 1.0 - float(dist) if dist is not None else None
        if score is not None:
            score = max(0.0, min(1.0, score))
        results.append(
            {
                "text": doc,
                "metadata": meta,
                "score": score,
            }
        )

    return results
