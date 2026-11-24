"""Smoke eval runner (job 1 of 4: Run).

Runs every case in evals/smoke_cases.json through headless Claude Code
(claude -p) from the repo root, so the branch's CLAUDE.md is loaded,
and saves every case result as JSON in results/smoke_results.json.

No --bare flag on purpose: bare mode skips CLAUDE.md, and CLAUDE.md is
the configuration this gate is testing.
"""
import json
import os
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = json.loads((ROOT / "evals" / "smoke_cases.json").read_text(encoding="utf-8"))
MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-4-8")
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")  # override only for local testing
OUT = ROOT / "results" / "smoke_results.json"


def run_case(case):
    prompt = f"Triage this support ticket:\n\n{case['ticket']}"
    cmd = [
        CLAUDE_BIN, "-p", prompt,
        "--output-format", "json",
        "--model", MODEL,
        "--tools", "",          # no tools: the answer must come from CLAUDE.md, not from reading evals/
        "--max-turns", "1",
    ]
    started = time.time()
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=180)
    seconds = round(time.time() - started, 1)
    try:
        payload = json.loads(proc.stdout)
        answer = str(payload.get("result", ""))
        run_error = bool(payload.get("is_error")) or proc.returncode != 0
    except json.JSONDecodeError:
        answer, run_error = proc.stdout.strip() or proc.stderr.strip(), True

    passed = (not run_error) and answer.strip() == case["kind"]
    return {
        "id": case["id"],
        "kind": case["kind"],
        "answer": answer.strip(),
        "passed": passed,
        "run_error": run_error,
        "seconds": seconds,
    }


def main():
    results = []
    for case in CASES["cases"]:
        r = run_case(case)
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"{mark}  {r['id']:<24} expected={r['kind']:<8} got={r['answer'][:60]!r}")
        results.append(r)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"model": MODEL, "threshold": CASES["threshold"],
                               "results": results}, indent=2), encoding="utf-8")
    print(f"Saved {len(results)} case results to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
