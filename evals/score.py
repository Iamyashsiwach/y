"""Score an agent report against the planted waste.
Usage: python -m evals.score report.md   (ground truth from `terraform output -json planted_ids` in ./terraform)
"""
import json
import re
import subprocess
import sys

ID = re.compile(r"\b(?:i|vol|eipalloc)-[0-9a-f]{8,17}\b")


def score(report: str, planted: set[str]) -> dict:
    found = set(ID.findall(report))
    return {
        "recall": len(found & planted) / len(planted),
        "missed": sorted(planted - found),
        "false_positives": sorted(found - planted),  # real findings outside the sandbox also land here; review by hand
    }


if __name__ == "__main__":
    planted = set(json.loads(subprocess.check_output(["terraform", "output", "-json", "planted_ids"], cwd="terraform")))
    result = score(open(sys.argv[1]).read(), planted)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["recall"] == 1 and not result["false_positives"] else 1)
