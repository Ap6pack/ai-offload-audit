#!/usr/bin/env python3
"""AI Offload Audit: local static triage for unnecessary model usage."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

DEFAULT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".cs",
    ".sh", ".bash", ".zsh", ".yml", ".yaml", ".json", ".toml", ".md",
}
DEFAULT_EXCLUDE = {
    ".git", ".venv", "venv", "node_modules", "vendor", "dist", "build",
    ".next", "coverage", "__pycache__", "target", ".idea", ".vscode",
}

AI_PATTERNS = [
    r"\bopenai\b", r"\banthropic\b", r"\bbedrock\b", r"\bbedrockruntime\b",
    r"\bgenerativeai\b", r"\bgenai\b", r"\blitellm\b", r"\bollama\b",
    r"\bvllm\b", r"\btransformers\b", r"\bpipeline\s*\(",
    r"\bChatOpenAI\b", r"\bChatAnthropic\b", r"\bBedrockChat\b",
    r"\binvoke_model\b", r"\bconverse\s*\(", r"\bchat\.completions\b",
    r"\bresponses\.create\b", r"\bmessages\.create\b",
    r"/v1/chat/completions", r"/v1/responses", r"\bllm\.invoke\b",
    r"\bmodel\.invoke\b", r"\bagenerate\b", r"\bainvoke\b",
    r"\bgenerate_content\b",
]

SIGNALS = {
    "T0": {
        "weight": 5,
        "groups": {
            "parse_validate": [r"\bparse\b", r"\bvalidate\b", r"\bvalidation\b", r"\bschema\b", r"\bjson\b", r"\bxml\b", r"\byaml\b", r"\bcsv\b", r"\buuid\b", r"\btimestamp\b", r"\bsemver\b"],
            "identifiers": [r"\bip(address)?\b", r"\bcidr\b", r"\bipv4\b", r"\bipv6\b", r"\burl\b", r"\bfqdn\b", r"\bhostname\b", r"\bmac address\b", r"\bhash\b", r"\bmd5\b", r"\bsha(1|256|512)\b", r"\bcve-\d{4}-\d+\b", r"\bcwe-\d+\b"],
            "encoding_crypto": [r"\bbase64\b", r"\bhex\b", r"\bdecode\b", r"\bencode\b", r"\bchecksum\b", r"\bsignature\b", r"\bverify\b"],
            "lookup_query": [r"\blookup\b", r"\bquery\b", r"\bsql\b", r"\bselect\b", r"\bgraphql\b", r"\bcypher\b", r"\bsearch index\b", r"\bapi lookup\b"],
            "transform": [r"\bnormalize\b", r"\bcanonicali[sz]e\b", r"\btransform\b", r"\bconvert\b", r"\bsort\b", r"\bfilter\b", r"\bjoin\b", r"\bmerge\b", r"\bdedup"],
            "rules_math": [r"\bthreshold\b", r"\bscore\b", r"\bformula\b", r"\bcalculate\b", r"\bpolicy\b", r"\brule engine\b", r"\ballowlist\b", r"\bdenylist\b", r"\bstate machine\b"],
            "format": [r"\btemplate\b", r"\brender\b", r"\bstrict json\b", r"\bjson output\b", r"\bdiff\b", r"\bexact match\b"],
        },
    },
    "T1": {
        "weight": 4,
        "groups": {
            "classification": [r"\bclassif(y|ication)\b", r"\blabel\b", r"\btag\b", r"\bcategory\b", r"\bbinary\b", r"\bmulticlass\b"],
            "routing": [r"\broute\b", r"\brouting\b", r"\bintent\b", r"\bdispatch\b", r"\bselect tool\b", r"\btriage\b"],
            "bounded_extraction": [r"\bextract\b", r"\bentity\b", r"\bfields?\b", r"\bstructured output\b"],
            "relevance": [r"\brelevance\b", r"\bsimilarity\b", r"\brank\b", r"\bembedding\b", r"\brerank\b"],
        },
    },
    "T2": {
        "weight": 3,
        "groups": {
            "summarization": [r"\bsummari[sz]e\b", r"\bsummary\b", r"\bcondense\b"],
            "domain_work": [r"\binterpret\b", r"\bmap .* attack\b", r"\bmap .* cwe\b", r"\bmap .* cve\b", r"\bsecurity finding\b", r"\brewrite\b", r"\bgenerate report\b"],
            "retrieval": [r"\brag\b", r"\bretrieval\b", r"\bknowledge base\b", r"\bquestion answering\b"],
        },
    },
    "T3": {
        "weight": 2,
        "groups": {
            "reasoning": [r"\bcorrelat(e|ion)\b", r"\bcross[- ]source\b", r"\bsynthesi[sz]e\b", r"\banaly[sz]e\b", r"\breason\b", r"\broot cause\b", r"\bdebug\b"],
        },
    },
    "T4": {
        "weight": 1,
        "groups": {
            "frontier": [r"\bplan\b", r"\bstrategy\b", r"\barchitecture\b", r"\bdesign\b", r"\bnovel\b", r"\bambiguous\b", r"\bconflicting\b", r"\bhigh[- ]impact\b"],
        },
    },
}

FUNCTION_PATTERNS = [
    re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\("),
    re.compile(r"^\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\("),
    re.compile(r"^\s*func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\("),
]

@dataclass
class Finding:
    file: str
    line: int
    symbol: Optional[str]
    matched_ai_pattern: str
    candidate_tier: str
    confidence: float
    signals: List[str]
    rationale: str
    context: str
    task_id_hint: str


def iter_files(root: Path, extensions: set[str], exclude: set[str], max_bytes: int):
    for path in root.rglob("*"):
        if not path.is_file() or any(part in exclude for part in path.parts):
            continue
        if path.suffix.lower() not in extensions:
            continue
        try:
            if path.stat().st_size <= max_bytes:
                yield path
        except OSError:
            pass


def nearest_symbol(lines: List[str], idx: int) -> Optional[str]:
    for pos in range(idx, max(-1, idx - 120), -1):
        for pattern in FUNCTION_PATTERNS:
            match = pattern.search(lines[pos])
            if match:
                return match.group(1)
    return None


def detect_ai(line: str) -> Optional[str]:
    for pattern in AI_PATTERNS:
        if re.search(pattern, line, re.I):
            return pattern
    return None


def score_context(context: str) -> Tuple[str, float, List[str], str]:
    scores: Dict[str, int] = {tier: 0 for tier in SIGNALS}
    hits: List[str] = []
    for tier, spec in SIGNALS.items():
        for group, patterns in spec["groups"].items():
            count = sum(bool(re.search(pattern, context, re.I)) for pattern in patterns)
            if count:
                scores[tier] += spec["weight"] * min(count, 3)
                hits.append(f"{tier}:{group}({count})")

    if not any(scores.values()):
        return "MANUAL_REVIEW", 0.20, [], "No strong capability signal near the model call."

    order = ["T0", "T1", "T2", "T3", "T4"]
    best = max(order, key=lambda tier: (scores[tier], -order.index(tier)))
    total = max(sum(scores.values()), 1)
    confidence = min(0.95, 0.45 + (scores[best] / total) * 0.50)

    if best in {"T0", "T1"} and scores["T3"] + scores["T4"] >= scores[best]:
        return (
            "HYBRID_REVIEW", min(confidence, 0.70), hits,
            "Low-tier signals exist, but reasoning/planning signals are comparably strong. Split the capability into cheaper substeps plus an escalation path.",
        )

    rationales = {
        "T0": "The surrounding capability appears deterministic: parsing, validation, lookup, transformation, rules, calculation, or existing tooling may be sufficient.",
        "T1": "The surrounding capability appears narrow and semantic, such as classification, routing, labeling, relevance, or bounded extraction.",
        "T2": "The surrounding capability appears to need domain-specific summarization, interpretation, retrieval, mapping, or constrained generation.",
        "T3": "The surrounding capability appears to require correlation, synthesis, debugging, or more involved reasoning.",
        "T4": "The surrounding capability contains planning, architecture, novelty, ambiguity, conflict, or other frontier-level reasoning signals.",
    }
    return best, confidence, hits, rationales[best]


def scan_repo(root: Path, context_lines: int, max_bytes: int, extensions: set[str], exclude: set[str]) -> List[Finding]:
    findings: List[Finding] = []
    seen = set()
    for path in iter_files(root, extensions, exclude, max_bytes):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines):
            matched = detect_ai(line)
            if not matched:
                continue
            if re.match(r"^\s*(from|import|using|use)\b", line):
                nearby = "\n".join(lines[idx:min(len(lines), idx + 8)])
                if not any(re.search(pattern, nearby, re.I) for pattern in AI_PATTERNS[10:]):
                    continue
            symbol = nearest_symbol(lines, idx)
            key = (str(path), symbol, idx // max(context_lines, 1))
            if key in seen:
                continue
            seen.add(key)
            start, end = max(0, idx - context_lines), min(len(lines), idx + context_lines + 1)
            context = "\n".join(lines[start:end])
            tier, confidence, signals, rationale = score_context(context)
            rel = str(path.relative_to(root))
            findings.append(Finding(
                file=rel,
                line=idx + 1,
                symbol=symbol,
                matched_ai_pattern=matched,
                candidate_tier=tier,
                confidence=round(confidence, 2),
                signals=signals,
                rationale=rationale,
                context=context[:5000],
                task_id_hint=f"{path.stem}:{symbol or 'line_' + str(idx + 1)}",
            ))
    return findings


def load_usage(path: Optional[str]) -> List[dict]:
    if not path:
        return []
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def calculate_spend(usage: List[dict], pricing: Optional[dict]) -> Tuple[List[dict], float]:
    if not usage or not pricing:
        return [], 0.0
    rows, total = [], 0.0
    for row in usage:
        enriched = dict(row)
        price = pricing.get(row.get("model"))
        if not price:
            enriched.update(cost_usd=None, pricing_status="missing")
        else:
            calls = float(row.get("calls", 1))
            cost = calls * (
                float(row.get("input_tokens", 0)) * float(price.get("input_per_million_usd", 0)) / 1_000_000
                + float(row.get("output_tokens", 0)) * float(price.get("output_per_million_usd", 0)) / 1_000_000
            )
            enriched.update(cost_usd=round(cost, 4), pricing_status="priced")
            total += cost
        rows.append(enriched)
    return rows, round(total, 4)


def tier_summary(findings: List[Finding]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for finding in findings:
        summary[finding.candidate_tier] = summary.get(finding.candidate_tier, 0) + 1
    return summary


def render_markdown(root: Path, findings: List[Finding], usage: List[dict], spend: float) -> str:
    summary = tier_summary(findings)
    out = ["# AI Offload Audit Report", "", f"Repository: `{root.resolve()}`", "", "## Executive summary", ""]
    out.append(f"- Likely AI/model call sites reviewed: **{len(findings)}**")
    for tier in ["T0", "T1", "T2", "T3", "T4", "HYBRID_REVIEW", "MANUAL_REVIEW"]:
        if summary.get(tier):
            out.append(f"- {tier}: **{summary[tier]}**")
    if usage:
        out.append(f"- Token spend represented by supplied usage file: **${spend:,.2f}**")
    out += ["", "> Candidate tiers are review hints, not automatic migration approvals. Benchmark quality before changing traffic.", "", "## Findings", "", "| File | Line | Symbol | Candidate | Confidence | Signals |", "|---|---:|---|---|---:|---|"]
    for finding in findings:
        signals = ", ".join(finding.signals[:6]).replace("|", "\\|")
        out.append(f"| `{finding.file}` | {finding.line} | `{finding.symbol or '-'}` | **{finding.candidate_tier}** | {finding.confidence:.2f} | {signals} |")
    if not findings:
        out.append("| _No likely AI call sites found_ | | | | | |")
    for idx, finding in enumerate(findings, 1):
        out += ["", f"### {idx}. `{finding.file}:{finding.line}` — {finding.candidate_tier}", "", f"**Task ID hint:** `{finding.task_id_hint}`  ", f"**Rationale:** {finding.rationale}"]
    if usage:
        out += ["", "## Supplied token spend", "", "| Task | Model | Calls | Cost |", "|---|---|---:|---:|"]
        for row in usage:
            cost = row.get("cost_usd")
            out.append(f"| `{row.get('task_id','-')}` | `{row.get('model','-')}` | {row.get('calls',1)} | {'pricing missing' if cost is None else f'${cost:,.2f}'} |")
    return "\n".join(out) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Audit a repository for AI offload opportunities.")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    parser.add_argument("repo", nargs="?", default=".")
    parser.add_argument("--out", default="ai-offload-report.md")
    parser.add_argument("--json", dest="json_out", default="ai-offload-report.json")
    parser.add_argument("--usage", help="Optional JSONL token usage file")
    parser.add_argument("--pricing", help="Optional pricing JSON")
    parser.add_argument("--context-lines", type=int, default=18)
    parser.add_argument("--max-file-bytes", type=int, default=2_000_000)
    args = parser.parse_args()

    root = Path(args.repo).resolve()
    findings = scan_repo(root, args.context_lines, args.max_file_bytes, DEFAULT_EXTENSIONS, DEFAULT_EXCLUDE)
    usage = load_usage(args.usage)
    pricing = json.loads(Path(args.pricing).read_text(encoding="utf-8")) if args.pricing else None
    spend_rows, total = calculate_spend(usage, pricing)
    report = {
        "repo": str(root),
        "tier_model": {"T0": "deterministic software/native tools", "T1": "tiny local model/classifier", "T2": "specialized local SLM", "T3": "larger local reasoning model", "T4": "frontier model"},
        "summary": tier_summary(findings),
        "findings": [asdict(finding) for finding in findings],
        "usage": spend_rows,
        "total_supplied_usage_cost_usd": total,
    }
    Path(args.out).write_text(render_markdown(root, findings, spend_rows, total), encoding="utf-8")
    Path(args.json_out).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.json_out}")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
