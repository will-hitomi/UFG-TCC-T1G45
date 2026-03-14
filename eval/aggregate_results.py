# eval/aggregate_results.py
import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

def newest_run_dir(outputs_dir: Path) -> Path:
    runs = [p for p in outputs_dir.iterdir() if p.is_dir()]
    if not runs:
        raise SystemExit(f"Sem runs em {outputs_dir}")
    return sorted(runs, key=lambda p: p.name)[-1]

def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def extract_rows(run_id: str, mode: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for it in items:
        item_id = it.get("item_id", "")
        nome = it.get("nome", "")
        for sec in it.get("sections", []):
            doc_type = sec.get("doc_type", "")
            section = sec.get("section", "")
            text = (sec.get("text") or "").strip()

            debug = sec.get("debug") or {}
            retrieved = debug.get("retrieved") or []

            # retrieved pode estar no formato [{id,score}] ou ter metadata
            ids = []
            scores = []
            for r in retrieved:
                rid = r.get("id") or (r.get("metadata", {}) or {}).get("id")
                sc = r.get("score")
                if rid is not None:
                    ids.append(str(rid))
                if sc is not None:
                    try:
                        scores.append(f"{float(sc):.4f}")
                    except Exception:
                        scores.append(str(sc))

            rows.append({
                "run_id": run_id,
                "item_id": item_id,
                "nome": nome,
                "doc_type": doc_type,
                "section": section,
                "mode": mode,
                "text": text,
                "retrieved_ids": "|".join(ids),
                "retrieved_scores": "|".join(scores),
            })
    return rows

def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def build_wide(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # junta baseline e rag na mesma linha por (run_id,item_id,doc_type,section)
    key = lambda r: (r["run_id"], r["item_id"], r["doc_type"], r["section"])
    grouped: Dict[Tuple[str,str,str,str], Dict[str, Any]] = {}

    for r in rows:
        k = key(r)
        if k not in grouped:
            grouped[k] = {
                "run_id": r["run_id"],
                "item_id": r["item_id"],
                "nome": r["nome"],
                "doc_type": r["doc_type"],
                "section": r["section"],
                "baseline_text": "",
                "rag_text": "",
                "rag_retrieved_ids": "",
                "rag_retrieved_scores": "",
            }
        if r["mode"] == "baseline":
            grouped[k]["baseline_text"] = r["text"]
        else:
            grouped[k]["rag_text"] = r["text"]
            grouped[k]["rag_retrieved_ids"] = r["retrieved_ids"]
            grouped[k]["rag_retrieved_scores"] = r["retrieved_scores"]

    return list(grouped.values())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs-dir", default="data/outputs")
    ap.add_argument("--run-dir", default="", help="ex: data/outputs/2026-03-08_023012")
    ap.add_argument("--wide", action="store_true", help="gera também summary_wide.csv")
    args = ap.parse_args()

    outputs_dir = Path(args.outputs_dir)
    run_dir = Path(args.run_dir) if args.run_dir else newest_run_dir(outputs_dir)
    run_id = run_dir.name

    baseline_path = run_dir / "baseline_run.json"
    rag_path = run_dir / "rag_run.json"

    if not baseline_path.exists() or not rag_path.exists():
        raise SystemExit(f"Faltam arquivos baseline/rag em {run_dir}")

    baseline_items = load_json(baseline_path)
    rag_items = load_json(rag_path)

    rows = []
    rows += extract_rows(run_id, "baseline", baseline_items)
    rows += extract_rows(run_id, "rag", rag_items)

    fieldnames = ["run_id","item_id","nome","doc_type","section","mode","text","retrieved_ids","retrieved_scores"]
    out_csv = run_dir / "summary.csv"
    write_csv(out_csv, rows, fieldnames)
    print(f"OK: {out_csv}")

    if args.wide:
        wide_rows = build_wide(rows)
        wide_fields = ["run_id","item_id","nome","doc_type","section","baseline_text","rag_text","rag_retrieved_ids","rag_retrieved_scores"]
        out_wide = run_dir / "summary_wide.csv"
        write_csv(out_wide, wide_rows, wide_fields)
        print(f"OK: {out_wide}")

if __name__ == "__main__":
    main()