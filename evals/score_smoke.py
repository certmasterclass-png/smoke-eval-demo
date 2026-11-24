"""Smoke eval scorer (job 2 of 4: Score).

Reads results/smoke_results.json, compares the pass count with the
threshold the team agreed on, and writes results/summary.md for the
pull request comment. Writes passed=true or passed=false to
GITHUB_OUTPUT so the last workflow step can fail the check.
This script itself always exits 0, so the comment step still runs.
"""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "results" / "smoke_results.json").read_text(encoding="utf-8"))
results = data["results"]
threshold = data["threshold"]
passed_count = sum(1 for r in results if r["passed"])
gate_passed = passed_count >= threshold

lines = [
    f"## Smoke eval: {'PASSED' if gate_passed else 'FAILED'} ({passed_count} of {len(results)}, threshold {threshold})",
    "",
    f"Model: `{data['model']}`",
    "",
]
failed = [r for r in results if not r["passed"]]
if failed:
    lines += ["**Failed cases**", "", "| Case | Expected | Got |", "|---|---|---|"]
    for r in failed:
        got = r["answer"].replace("\n", " ").replace("|", "/")[:80]
        lines.append(f"| `{r['id']}` | `{r['kind']}` | {got} |")
else:
    lines.append("All cases passed.")

summary = "\n".join(lines) + "\n"
(ROOT / "results" / "summary.md").write_text(summary, encoding="utf-8")
print(summary)

gh_out = os.environ.get("GITHUB_OUTPUT")
if gh_out:
    with open(gh_out, "a", encoding="utf-8") as f:
        f.write(f"passed={'true' if gate_passed else 'false'}\n")
