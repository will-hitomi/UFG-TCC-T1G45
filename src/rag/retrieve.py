import os
from typing import Any, Dict, List, Optional, Tuple

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


def _build_where(domain: str, doc_type: str, section: str,
                 subcategory: str | None = None,
                 filters: dict | None = None) -> dict:
    clauses = [
        {"domain": {"$eq": domain}},
        {"doc_type": {"$eq": doc_type}},
        {"section": {"$eq": section}},
    ]

    if subcategory:
        clauses.append({"subcategory": {"$eq": subcategory}})

    if filters:
        for k, v in filters.items():
            if v is None:
                continue
            if isinstance(v, list):
                clauses.append({k: {"$in": v}})
            else:
                clauses.append({k: {"$eq": v}})

    # Chroma espera um operador único no topo
    return {"$and": clauses} if len(clauses) > 1 else clauses[0]


def _get_min_score() -> float:
    raw = os.getenv("RAG_MIN_SCORE", "0.0")
    try:
        value = float(raw)
    except ValueError:
        value = 0.0
    return max(0.0, min(1.0, value))


def _apply_min_score(
    results: List[Dict[str, Any]],
    min_score: float,
) -> Tuple[List[Dict[str, Any]], int]:
    if min_score <= 0.0:
        return results, 0
    kept = [
        r for r in results
        if (r.get("score") is not None) and (float(r["score"]) >= min_score)
    ]
    return kept, len(results) - len(kept)


def _single_retrieve(
    query: str,
    where: Dict[str, Any],
    top_k: int,
    min_score: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    collection_name = os.getenv("CHROMA_COLLECTION", "kb_sections")

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=collection_name)

    model = _get_model()
    q_emb = model.encode([query], normalize_embeddings=True, show_progress_bar=False).tolist()

    res = collection.query(
        query_embeddings=q_emb,
        n_results=top_k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    out = []
    for doc, meta, dist in zip(docs, metas, dists):
        score = 1.0 - float(dist) if dist is not None else None
        if score is not None:
            score = max(0.0, min(1.0, score))
        out.append({"text": doc, "metadata": meta, "score": score})
    applied_min_score = _get_min_score() if min_score is None else min_score
    return _apply_min_score(out, applied_min_score)

def retrieve_by_section(query: str, domain: str, doc_type: str, section: str,
                        subcategory: Optional[str] = None, top_k: int = 5,
                        filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    where = _build_where(domain, doc_type, section, subcategory=subcategory, filters=filters)
    results, _ = _single_retrieve(query, where, top_k)
    return results

def _normalize_results(
    res: Dict[str, Any],
    min_score: Optional[float] = None,
) -> Tuple[List[Dict[str, Any]], int]:
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
    applied_min_score = _get_min_score() if min_score is None else min_score
    return _apply_min_score(results, applied_min_score)

def retrieve_with_fallback(
    query: str,
    domain: str,
    doc_type: str,
    section: str,
    subcategory: Optional[str] = None,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
    max_top_k: int = 10,
    min_results: int = 1,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Retorna (results, debug)
    fallback_level:
      0 = tentativa normal
      1 = remove subcategory
      2 = remove filters
      3 = aumenta top_k
    """
    attempts = []
    min_score = _get_min_score()
    total_filtered = 0

    # tentativa 0
    where0 = _build_where(domain, doc_type, section, subcategory=subcategory, filters=filters)
    r0, f0 = _single_retrieve(query, where0, top_k, min_score=min_score)
    total_filtered += f0
    attempts.append({"level": 0, "top_k": top_k, "subcategory": bool(subcategory), "filters": bool(filters), "count": len(r0)})

    if len(r0) >= min_results:
        return r0, {
            "used_fallback_level": 0,
            "attempts": attempts,
            "min_score_applied": min_score,
            "filtered_count": total_filtered,
        }

    # tentativa 1: remove subcategory
    where1 = _build_where(domain, doc_type, section, subcategory=None, filters=filters)
    r1, f1 = _single_retrieve(query, where1, top_k, min_score=min_score)
    total_filtered += f1
    attempts.append({"level": 1, "top_k": top_k, "subcategory": False, "filters": bool(filters), "count": len(r1)})

    if len(r1) >= min_results:
        return r1, {
            "used_fallback_level": 1,
            "attempts": attempts,
            "min_score_applied": min_score,
            "filtered_count": total_filtered,
        }

    # tentativa 2: remove filters
    where2 = _build_where(domain, doc_type, section, subcategory=None, filters=None)
    r2, f2 = _single_retrieve(query, where2, top_k, min_score=min_score)
    total_filtered += f2
    attempts.append({"level": 2, "top_k": top_k, "subcategory": False, "filters": False, "count": len(r2)})

    if len(r2) >= min_results:
        return r2, {
            "used_fallback_level": 2,
            "attempts": attempts,
            "min_score_applied": min_score,
            "filtered_count": total_filtered,
        }

    # tentativa 3: aumenta top_k
    k = top_k
    best = r2
    while k < max_top_k:
        k = min(max_top_k, k + 3)
        r3, f3 = _single_retrieve(query, where2, k, min_score=min_score)
        total_filtered += f3
        attempts.append({"level": 3, "top_k": k, "subcategory": False, "filters": False, "count": len(r3)})
        if len(r3) > len(best):
            best = r3
        if len(r3) >= min_results:
            return r3, {
                "used_fallback_level": 3,
                "attempts": attempts,
                "min_score_applied": min_score,
                "filtered_count": total_filtered,
            }

    return best, {
        "used_fallback_level": 3,
        "attempts": attempts,
        "min_score_applied": min_score,
        "filtered_count": total_filtered,
    }

def _run_query(
    collection: Any,
    q_emb: List[List[float]],
    domain: str,
    doc_type: str,
    section: str,
    subcategory: Optional[str],
    filters: Optional[Dict[str, Any]],
    n_results: int,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any], int]:
    where = _build_where(
        domain=domain,
        doc_type=doc_type,
        section=section,
        subcategory=subcategory,
        filters=filters,
    )

    res = collection.query(
        query_embeddings=q_emb,
        n_results=n_results,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    results, filtered_count = _normalize_results(res)
    return results, where, filtered_count


def retrieve_by_section_with_debug(
    query: str,
    domain: str,
    doc_type: str,
    section: str,
    subcategory: Optional[str] = None,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    chroma_path = os.getenv("CHROMA_PATH", "./chroma_db")
    collection_name = os.getenv("CHROMA_COLLECTION", "kb_sections")
    max_top_k = 10
    requested_top_k = max(1, int(top_k))

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=collection_name)

    model = _get_model()
    q_emb = model.encode([query], normalize_embeddings=True, show_progress_bar=False).tolist()

    attempts: List[Dict[str, Any]] = []
    used_fallback_level = 0
    total_filtered = 0
    min_score = _get_min_score()

    results, where, filtered_count = _run_query(
        collection=collection,
        q_emb=q_emb,
        domain=domain,
        doc_type=doc_type,
        section=section,
        subcategory=subcategory,
        filters=filters,
        n_results=requested_top_k,
    )
    total_filtered += filtered_count
    attempts.append(
        {
            "level": 0,
            "top_k": requested_top_k,
            "used_subcategory": bool(subcategory),
            "used_filters": bool(filters),
            "result_count": len(results),
            "where": where,
        }
    )

    if (len(results) < requested_top_k) and subcategory:
        level1_results, where, filtered_count = _run_query(
            collection=collection,
            q_emb=q_emb,
            domain=domain,
            doc_type=doc_type,
            section=section,
            subcategory=None,
            filters=filters,
            n_results=requested_top_k,
        )
        total_filtered += filtered_count
        attempts.append(
            {
                "level": 1,
                "top_k": requested_top_k,
                "used_subcategory": False,
                "used_filters": bool(filters),
                "result_count": len(level1_results),
                "where": where,
            }
        )
        if len(level1_results) > len(results):
            results = level1_results
            used_fallback_level = 1

    if (len(results) < requested_top_k) and filters:
        level2_results, where, filtered_count = _run_query(
            collection=collection,
            q_emb=q_emb,
            domain=domain,
            doc_type=doc_type,
            section=section,
            subcategory=None,
            filters=None,
            n_results=requested_top_k,
        )
        total_filtered += filtered_count
        attempts.append(
            {
                "level": 2,
                "top_k": requested_top_k,
                "used_subcategory": False,
                "used_filters": False,
                "result_count": len(level2_results),
                "where": where,
            }
        )
        if len(level2_results) > len(results):
            results = level2_results
            used_fallback_level = 2

    expanded_top_k = max_top_k
    if (len(results) < requested_top_k) and (expanded_top_k > requested_top_k):
        level3_results, where, filtered_count = _run_query(
            collection=collection,
            q_emb=q_emb,
            domain=domain,
            doc_type=doc_type,
            section=section,
            subcategory=None,
            filters=None,
            n_results=expanded_top_k,
        )
        total_filtered += filtered_count
        attempts.append(
            {
                "level": 3,
                "top_k": expanded_top_k,
                "used_subcategory": False,
                "used_filters": False,
                "result_count": len(level3_results),
                "where": where,
            }
        )
        if len(level3_results) > len(results):
            results = level3_results
            used_fallback_level = 3

    return results, {
        "attempts": attempts,
        "used_fallback_level": used_fallback_level,
        "min_score_applied": min_score,
        "filtered_count": total_filtered,
    }
