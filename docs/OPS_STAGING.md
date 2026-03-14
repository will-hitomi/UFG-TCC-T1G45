
---

## 3.2 `docs/OPS_STAGING.md` (para você/admin)
Crie `docs/OPS_STAGING.md`:

```md
# OPS — Staging (Ubuntu + Cloudflare)

## Hostnames
- UI: https://tcpopai-app.krmn.online  -> http://127.0.0.1:8501
- API: https://tcpopai-api.krmn.online  -> http://127.0.0.1:8000
- Admin: /admin/* (Access restrito)

## Serviços (systemd)
- cloudflared
- tcpopai-api
- tcpopai-ui

### Checar status
```bash
sudo systemctl status cloudflared --no-pager
sudo systemctl status tcpopai-api --no-pager
sudo systemctl status tcpopai-ui --no-pager