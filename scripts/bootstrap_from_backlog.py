#!/usr/bin/env python3
import argparse
import datetime as dt
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


REPO_DEFAULT = "will-hitomi/UFG-TCC-T1G45"


@dataclass
class Milestone:
    title: str
    due: Optional[str] = None  # YYYY-MM-DD


@dataclass
class Card:
    milestone: str
    card_id: str
    title: str
    owner: Optional[str] = None
    labels: List[str] = field(default_factory=list)
    branch: Optional[str] = None
    body_lines: List[str] = field(default_factory=list)


def run(cmd: List[str], check: bool = True) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def parse_backlog(md_text: str) -> Tuple[List[Milestone], List[Card]]:
    # Milestone header: "# M1 — ... (até 2026-03-13)"
    ms_re = re.compile(r"^#\s+(?P<title>.+?)(?:\s*\(até\s*(?P<due>\d{4}-\d{2}-\d{2})\))?\s*$")
    # Card header: "## [ ] A-001 — Title"
    card_re = re.compile(r"^##\s+\[\s*[x~ ]\s*\]\s+(?P<id>[A-Z]-\d{3})\s+—\s+(?P<title>.+?)\s*$")

    keyval_re = re.compile(r"^(Owner|Labels|Branch)\s*:\s*(.+?)\s*$", re.IGNORECASE)

    milestones: List[Milestone] = []
    cards: List[Card] = []

    current_ms: Optional[Milestone] = None
    current_card: Optional[Card] = None

    lines = md_text.splitlines()

    def flush_card():
        nonlocal current_card
        if current_card:
            cards.append(current_card)
            current_card = None

    for line in lines:
        ms_m = ms_re.match(line)
        if ms_m and line.startswith("# "):
            flush_card()
            title = ms_m.group("title").strip()
            due = ms_m.group("due")
            current_ms = Milestone(title=title, due=due)
            milestones.append(current_ms)
            continue

        c_m = card_re.match(line)
        if c_m:
            flush_card()
            if not current_ms:
                # cards outside a milestone are ignored
                continue
            current_card = Card(
                milestone=current_ms.title,
                card_id=c_m.group("id"),
                title=c_m.group("title").strip(),
            )
            continue

        if current_card:
            kv = keyval_re.match(line)
            if kv:
                k = kv.group(1).lower()
                v = kv.group(2).strip()
                if k == "owner":
                    current_card.owner = v
                elif k == "labels":
                    current_card.labels = [x.strip() for x in v.split(",") if x.strip()]
                elif k == "branch":
                    current_card.branch = v
                continue

            # collect body content as-is
            current_card.body_lines.append(line)

    flush_card()
    return milestones, cards


def iso_due(due_ymd: str) -> str:
    # Due date in UTC end-of-day
    d = dt.datetime.strptime(due_ymd, "%Y-%m-%d")
    d = d.replace(hour=23, minute=59, second=59, tzinfo=dt.timezone.utc)
    return d.isoformat().replace("+00:00", "Z")


def ensure_labels(repo: str, labels: List[str]):
    # Create labels if missing (best-effort).
    # Colors default by prefix if not specified in backlog.
    for name in labels:
        if not name:
            continue
        color = "1d76db"
        if name == "P0":
            color = "d73a4a"
        elif name == "P1":
            color = "fbca04"
        elif name == "P2":
            color = "c2e0c6"
        elif name.startswith("scope:"):
            color = "0e8a16"
        elif name == "nice-to-have":
            color = "c5def5"
        try:
            run(["gh", "label", "create", name, "--repo", repo, "--color", color, "--description", name], check=False)
        except Exception:
            pass


def get_milestone_number(repo: str, title: str) -> Optional[int]:
    out = run(["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100"])
    # simple regex parse to avoid json deps
    # safer: use gh --jq (but api output is JSON anyway; we will use jq via gh if available)
    try:
        num = run(["gh", "api", f"repos/{repo}/milestones?state=all&per_page=100",
                   "--jq", f'.[] | select(.title=="{title}") | .number'])
        return int(num) if num else None
    except Exception:
        return None


def ensure_milestone(repo: str, ms: Milestone) -> int:
    existing = get_milestone_number(repo, ms.title)
    if existing:
        return existing
    args = ["gh", "api", "-X", "POST", f"repos/{repo}/milestones", "-f", f"title={ms.title}"]
    if ms.due:
        args += ["-f", f"due_on={iso_due(ms.due)}"]
    created = run(args + ["--jq", ".number"])
    return int(created)


def issue_exists(repo: str, title: str) -> Optional[int]:
    try:
        num = run(["gh", "issue", "list", "--repo", repo, "--search", f"\"{title}\" in:title",
                   "--json", "number,title", "--limit", "50", "--jq", f'.[] | select(.title=="{title}") | .number'])
        return int(num) if num else None
    except Exception:
        return None


def create_or_update_issue(repo: str, card: Card, milestone_title: str, update: bool) -> int:
    full_title = f"{card.card_id} — {card.title}"
    body = []
    if card.owner:
        body.append(f"Owner: {card.owner}")
    if card.branch:
        body.append(f"Branch: {card.branch}")
    body.append("")
    body.extend(card.body_lines)
    body_text = "\n".join(body).strip() + "\n"

    existing = issue_exists(repo, full_title)
    if existing:
        if update:
            # update body, labels, milestone
            run(["gh", "issue", "edit", str(existing), "--repo", repo,
                 "--body", body_text,
                 "--milestone", milestone_title])
            if card.labels:
                run(["gh", "issue", "edit", str(existing), "--repo", repo,
                     "--add-label", ",".join(card.labels)])
        return existing

    ensure_labels(repo, card.labels)
    cmd = ["gh", "issue", "create", "--repo", repo,
           "--title", full_title,
           "--body", body_text,
           "--milestone", milestone_title]
    if card.labels:
        cmd += ["--label", ",".join(card.labels)]
    out = run(cmd)
    # gh returns URL; extract number from it
    m = re.search(r"/issues/(\d+)", out)
    if not m:
        # fallback: list again
        n = issue_exists(repo, full_title)
        if not n:
            raise RuntimeError(f"Could not determine issue number for: {full_title}")
        return n
    return int(m.group(1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO_DEFAULT, help="owner/repo")
    ap.add_argument("--backlog", default="BACKLOG.md")
    ap.add_argument("--update", action="store_true", help="Update existing issues (body/labels/milestone)")
    args = ap.parse_args()

    # prechecks
    run(["gh", "auth", "status"], check=True)

    md = Path(args.backlog).read_text(encoding="utf-8")
    milestones, cards = parse_backlog(md)

    ms_map: Dict[str, int] = {}
    for ms in milestones:
        ms_map[ms.title] = ensure_milestone(args.repo, ms)

    created_map: Dict[str, int] = {}
    for c in cards:
        ms_num = ms_map.get(c.milestone)
        if not ms_num:
            continue
        n = create_or_update_issue(args.repo, c, c.milestone, update=args.update)
        created_map[f"{c.card_id} — {c.title}"] = n

    print("OK. Issues:")
    for k, v in created_map.items():
        print(f"- #{v} {k}")


if __name__ == "__main__":
    main()
