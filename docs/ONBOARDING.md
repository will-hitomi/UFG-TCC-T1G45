# ONBOARDING — UFG-TCC-T1G45 (TCPOPAI)

## Links
- Repo: https://github.com/will-hitomi/UFG-TCC-T1G45
- UI (staging): https://tcpopai-app.krmn.online
- API (staging): https://tcpopai-api.krmn.online

> A UI e a API são protegidas por Cloudflare Access.

---

## O que cada pessoa faz
- Pessoa A (dados): atualiza `data/knowledge_base.jsonl` e `data/test_cases.jsonl`.
- Pessoa C (UI): melhora `src/app/ui_streamlit.py`.

---

## 1) Instalar o básico
Você precisa de:
- Git
- Python 3.11+
- (Opcional) VS Code

Teste no terminal:
- `git --version`
- `python --version` (Windows: `py --version`)

---

## 2) Clonar o projeto
```bash
git clone https://github.com/will-hitomi/UFG-TCC-T1G45
cd UFG-TCC-T1G45