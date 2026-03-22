import json
from pathlib import Path

DATA_PATH = Path("data/knowledge_base.jsonl")

def ingest():
    if not DATA_PATH.exists():
        print("Arquivo knowledge_base.jsonl não encontrado")
        return

    docs = []

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))

    print(f"{len(docs)} documentos carregados")

    # Aqui você poderia enviar para embeddings ou vector store
    for doc in docs[:5]:
        print(doc)

if __name__ == "__main__":
    ingest()
