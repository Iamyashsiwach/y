import base64

from agent.pr import open_pr


def test_open_pr_creates_branch_file_then_pr():
    calls = []

    def fake(method, path, token, body=None):
        calls.append((method, path, body))
        return {
            "default_branch": "main", "object": {"sha": "abc"}, "html_url": "https://github.com/o/r/pull/1",
        }

    assert open_pr("o/r", "# report", "tok", call=fake) == "https://github.com/o/r/pull/1"
    assert [(m, p.split("/")[-1] if "contents" not in p else "contents") for m, p, _ in calls] == [
        ("GET", "r"), ("GET", "main"), ("POST", "refs"), ("PUT", "contents"), ("POST", "pulls"),
    ]
    branch = calls[2][2]["ref"].removeprefix("refs/heads/")
    assert calls[2][2]["sha"] == "abc" and calls[3][2]["branch"] == branch == calls[4][2]["head"]
    assert base64.b64decode(calls[3][2]["content"]) == b"# report"
