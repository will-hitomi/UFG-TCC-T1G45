# AGENTS.md — Regras do projeto

- Não altere docs/API_CONTRACT.md e docs/SECTIONS.md sem um PR “SPEC CHANGE”.
- Respeite o contrato: /generate retorna exatamente 1 seção por request.
- Preferir mudanças pequenas e rastreáveis (mostrar diff).
- Sempre rodar: scripts/smoke.sh (ou, no mínimo, curl /health, /index e /retrieve).
- Evitar adicionar dependências novas sem justificar.
