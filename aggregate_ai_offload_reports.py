#!/usr/bin/env python3
"""
Aggregate multiple ai-offload-report.json files into a portfolio report.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

def money(v):
    return f"${v:,.2f}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reports", nargs="+", help="Per-repo ai-offload-report.json files")
    ap.add_argument("--out", default="ai-offload-portfolio.md")
    args = ap.parse_args()

    repos = []
    totals = {}
    spend = 0.0
    usage_rows = []

    for rp in args.reports:
        p = Path(rp)
        data = json.loads(p.read_text(encoding="utf-8"))
        name = Path(data.get("repo", p.stem)).name
        repo_spend = float(data.get("total_supplied_usage_cost_usd") or 0)
        spend += repo_spend
        summary = data.get("summary", {})
        for k, v in summary.items():
            totals[k] = totals.get(k, 0) + int(v)
        repos.append((name, repo_spend, summary, len(data.get("findings", []))))
        for row in data.get("usage", []):
            r = dict(row)
            r["repo"] = name
            usage_rows.append(r)

    usage_rows.sort(key=lambda x: (x.get("cost_usd") is not None, x.get("cost_usd") or 0), reverse=True)

    lines = ["# AI Offload Portfolio Report", ""]
    lines.append(f"Repositories assessed: **{len(repos)}**  ")
    lines.append(f"Token spend represented by supplied telemetry: **{money(spend)}**")
    lines.append("")
    lines.append("## Estate-level candidate counts")
    lines.append("")
    for tier in ["T0","T1","T2","T3","T4","HYBRID_REVIEW","MANUAL_REVIEW"]:
        if totals.get(tier):
            lines.append(f"- {tier}: **{totals[tier]}**")
    lines.append("")
    lines.append("## Repositories")
    lines.append("")
    lines.append("| Repo | AI call-site findings | Represented spend | Tier summary |")
    lines.append("|---|---:|---:|---|")
    for name, repo_spend, summary, count in sorted(repos, key=lambda x: x[1], reverse=True):
        s = ", ".join(f"{k}:{v}" for k,v in summary.items())
        lines.append(f"| `{name}` | {count} | {money(repo_spend)} | {s or '-'} |")
    lines.append("")
    if usage_rows:
        lines.append("## Highest-cost instrumented tasks")
        lines.append("")
        lines.append("| Repo | Task | Model | Calls | Cost |")
        lines.append("|---|---|---|---:|---:|")
        for r in usage_rows[:50]:
            c = r.get("cost_usd")
            cs = "pricing missing" if c is None else money(float(c))
            lines.append(f"| `{r.get('repo','-')}` | `{r.get('task_id','-')}` | `{r.get('model','-')}` | {r.get('calls',1)} | {cs} |")
        lines.append("")
    lines.append("## Portfolio priority")
    lines.append("")
    lines.append("1. Rank T0/T1 candidates by real monthly spend and call volume.")
    lines.append("2. Eliminate deterministic misuse first.")
    lines.append("3. Benchmark narrow classifiers/tiny models second.")
    lines.append("4. Consolidate duplicate capabilities used by multiple repos into shared services.")
    lines.append("5. Keep frontier use where it measurably outperforms cheaper tiers or where risk/novelty requires it.")
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
