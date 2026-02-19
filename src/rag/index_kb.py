import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

import chromadb
from sentence_transformers import SentenceTransformer


def _safe_tags(tags):
    if not tags:
        return ""
    if isinstance(tags, list):
        return ",".join([str(t).strip() for t in tags if str(t).strip()])
    return str(tags)


def load_kb_jsonl(kb_path: str) -> List[Dict[str, Any]]:
    path = Path(kb_path)
    if not path.exists():
        raise FileNotFoundError(f"KB não encontrado em: {kb_path}")

    rows = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                rows.append(obj)
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON inválido na linha {i}: {e}") from e
    return rows


def build_chroma_collection(chroma_path: str, collection_name: str, rebuild: bool):
    client = chromadb.PersistentClient(path=chroma_path)

    if rebuild:
        # delete se existir
        try:
            client.delete_collection(name=collection_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}  # bom default p/ embeddings normalizados
    )
    return collection


def index_kb(
    kb_path: str,
    chroma_path: str,
    embedding_model_name: str,
    collection_name: str = "kb_sections",
    rebuild: bool = True,
    batch_size: int = 64,
) -> int:
    rows = load_kb_jsonl(kb_path)

    # modelo de embeddings (CPU ok)
    model = SentenceTransformer(embedding_model_name)

    collection = build_chroma_collection(chroma_path, collection_name, rebuild=rebuild)

    total = 0
    ids_batch, docs_batch, metas_batch = [], [], []

    def flush_batch():
        nonlocal total, ids_batch, docs_batch, metas_batch
        if not ids_batch:
            return

        embeddings = model.encode(
            docs_batch,
            normalize_embeddings=True,
            show_progress_bar=False
        ).tolist()

        collection.upsert(
            ids=ids_batch,
            documents=docs_batch,
            metadatas=metas_batch,
            embeddings=embeddings
        )
        total += len(ids_batch)
        ids_batch, docs_batch, metas_batch = [], [], []

    # validação mínima de campos obrigatórios (pode trocar por Pydantic depois)
    required = ["id", "domain", "subcategory", "doc_type", "section", "text", "source", "lang"]

    for r in rows:
        for k in required:
            if k not in r or r[k] is None or str(r[k]).strip() == "":
                raise ValueError(f"Registro sem campo obrigatório '{k}': {r}")

        rid = str(r["id"]).strip()
        text = str(r["text"]).strip()

        meta = {
            "domain": str(r["domain"]).strip(),
            "subcategory": str(r["subcategory"]).strip(),
            "doc_type": str(r["doc_type"]).strip(),
            "section": str(r["section"]).strip(),
            "source": str(r["source"]).strip(),
            "lang": str(r["lang"]).strip(),
            "tags": _safe_tags(r.get("tags", [])),
        }

        ids_batch.append(rid)
        docs_batch.append(text)
        metas_batch.append(meta)

        if len(ids_batch) >= batch_size:
            flush_batch()

    flush_batch()
    return total
