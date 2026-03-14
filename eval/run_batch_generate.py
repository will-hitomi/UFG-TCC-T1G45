# eval/run_batch_generate.py
import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

SECTIONS = {
    "POP": ["Passo a passo", "Cuidados e Segurança"],
    "COMERCIAL": ["Detalhes essenciais", "Benefícios (bullets)"],
}

def load_jsonl(path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if limit and len(rows) >= limit:
                break
    return rows

def access_headers() -> Dict[str, str]:
    # Se você rodar de fora do servidor (Cloudflare Access), setar envs:
    # CF_ACCESS_CLIENT_ID e CF_ACCESS_CLIENT_SECRET
    cid = os.getenv("CF_ACCESS_CLIENT_ID", "").strip()
    csec = os.getenv("CF_ACCESS_CLIENT_SECRET", "").strip()
    if cid and csec:
        return {
            "CF-Access-Client-Id": cid,
            "CF-Access-Client-Secret": csec,
        }
    return {}

def post_generate(base_url: str, payload: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
    h = {"Content-Type": "application/json"}
    h.update(access_headers())
    r = requests.post(f"{base_url}/generate", json=payload, headers=h, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"/generate {r.status_code}: {r.text[:500]}")
    return r.json()

def render_md(run_name: str, mode: str, items: List[Dict[str, Any]]) -> str:
    lines = [f"# TCPOPAI — {run_name} — {mode.upper()}", ""]
    for it in items:
        item_id = it.get("item_id", "")
        nome = it.get("nome", "")
        lines.append(f"## {item_id} — {nome}".strip())
        lines.append("")
        for sec in it["sections"]:
            lines.append(f"### {sec['doc_type']} — {sec['section']}")
            lines.append(sec["text"].strip())
            lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).strip() + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="data/test_cases.jsonl")
    ap.add_argument("--base-url", default=os.getenv("API_BASE_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--out", default="data/outputs")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args()

    limit = args.limit if args.limit > 0 else None
    cases = load_jsonl(args.input, limit=limit)
    if not cases:
        raise SystemExit("Sem casos no input.")

    ts = dt.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    run_dir = Path(args.out) / ts
    run_dir.mkdir(parents=True, exist_ok=True)

    run_info = {
        "timestamp": ts,
        "base_url": args.base_url,
        "input": args.input,
        "limit": args.limit,
        "sections": SECTIONS,
        "top_k": args.top_k,
        "rag_min_score": os.getenv("RAG_MIN_SCORE", ""),
        "llm_model": os.getenv("LLM_MODEL", os.getenv("MISTRAL_MODEL", "")),
    }
    (run_dir / "run_info.json").write_text(json.dumps(run_info, ensure_ascii=False, indent=2), encoding="utf-8")

    baseline_items = []
    rag_items = []

    for item in cases:
        item_id = item.get("item_id", "")
        nome = item.get("nome", "")
        domain = item.get("domain", "limpeza")
        subcategory = item.get("subcategory")

        # cada “item” no output consolidado tem uma lista de seções geradas
        b_out = {"item_id": item_id, "nome": nome, "domain": domain, "subcategory": subcategory, "sections": []}
        r_out = {"item_id": item_id, "nome": nome, "domain": domain, "subcategory": subcategory, "sections": []}

        for doc_type, sections in SECTIONS.items():
            for section in sections:
                # Baseline
                payload_b = {
                    "mode": "baseline",
                    "domain": domain,
                    "subcategory": subcategory,
                    "doc_type": doc_type,
                    "section": section,
                    "input_item": item,
                    "top_k": args.top_k,
                }
                jb = post_generate(args.base_url, payload_b)
                b_out["sections"].append({
                    "doc_type": doc_type,
                    "section": section,
                    "text": jb["sections"][0]["text"],
                    "notes": jb.get("notes", []),
                    "debug": jb.get("debug", {}),
                })

                # RAG
                payload_r = dict(payload_b)
                payload_r["mode"] = "rag"
                jr = post_generate(args.base_url, payload_r)
                r_out["sections"].append({
                    "doc_type": doc_type,
                    "section": section,
                    "text": jr["sections"][0]["text"],
                    "notes": jr.get("notes", []),
                    "debug": jr.get("debug", {}),
                })

        baseline_items.append(b_out)
        rag_items.append(r_out)

    (run_dir / "baseline_run.json").write_text(json.dumps(baseline_items, ensure_ascii=False, indent=2), encoding="utf-8")
    (run_dir / "rag_run.json").write_text(json.dumps(rag_items, ensure_ascii=False, indent=2), encoding="utf-8")

    (run_dir / "baseline_run.md").write_text(render_md(ts, "baseline", baseline_items), encoding="utf-8")
    (run_dir / "rag_run.md").write_text(render_md(ts, "rag", rag_items), encoding="utf-8")

    print(f"OK. Run salvo em: {run_dir}")

if __name__ == "__main__":
    main()