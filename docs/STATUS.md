# STATUS — Sprint Dev (v0.2)

- Contrato do projeto: docs/API_CONTRACT.md e docs/SECTIONS.md (não mudar sem SPEC CHANGE).
- API FastAPI ativa: /health, /index, /retrieve.
- Vector store: Chroma (persistente via CHROMA_PATH) + embeddings SentenceTransformers.
- LLM remoto configurado e funcionando (Mistral via endpoint OpenAI-like).
- Base de conhecimento: data/knowledge_base.jsonl (JSONL) e indexação via POST /index.
- RAG por seção: retrieve filtra por domain + doc_type + section (+ subcategory opcional).
- Próximo passo: implementar POST /generate usando LangChain (create_stuff_documents_chain).
- /generate deve suportar mode=baseline e mode=rag e gerar 1 seção por chamada.
- Incluir debug.retrieved no modo rag.
- Adicionar/atualizar scripts/smoke.sh: index -> generate baseline -> generate rag.
