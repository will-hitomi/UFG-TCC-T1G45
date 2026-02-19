# API_CONTRACT.md — Contrato da API (v0.2)

Este documento congela o **formato das rotas** e o **shape do JSON**.
Regra: não mudar payloads sem “SPEC CHANGE”.

Base URL (local/dev): `http://localhost:8000`

---

## 1) Convenções

### 1.1 Enums oficiais
- `mode`: `baseline` | `rag`
- `doc_type`: `POP` | `TECNICO` | `COMERCIAL`
- `language`: `pt-BR`

### 1.2 Headers (recomendado)
- `Content-Type: application/json`
- (opcional) `X-Request-Id: <uuid>` para rastreio

### 1.3 Status codes
- `200` OK
- `400` erro de validação (payload inválido / enum inválido)
- `500` erro interno (LLM endpoint indisponível, etc.)

---

## 2) Endpoints

## 2.1 GET /health
Verifica se o serviço está de pé.

### Response 200
```json
{"status":"ok"}

