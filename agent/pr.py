"""Open a GitHub PR containing the agent's report. Stdlib only; token comes from the environment."""
import base64
import json
import urllib.request
from datetime import datetime, timezone


def api(method: str, path: str, token: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


# ponytail: PR carries the report only; Terraform edits are suggestions in it. Add file edits when the agent emits patches.
def open_pr(repo: str, report: str, token: str, call=api) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    base = call("GET", f"/repos/{repo}", token)["default_branch"]
    sha = call("GET", f"/repos/{repo}/git/ref/heads/{base}", token)["object"]["sha"]
    branch = f"finops/report-{stamp}"
    call("POST", f"/repos/{repo}/git/refs", token, {"ref": f"refs/heads/{branch}", "sha": sha})
    call("PUT", f"/repos/{repo}/contents/finops-reports/{stamp}.md", token, {
        "message": f"FinOps report {stamp}",
        "content": base64.b64encode(report.encode()).decode(),
        "branch": branch,
    })
    pr = call("POST", f"/repos/{repo}/pulls", token, {
        "title": f"FinOps report {stamp}", "head": branch, "base": base,
        "body": report + "\n\n_Proposed by the finops agent (read-only); review before applying any change._",
    })
    return pr["html_url"]
