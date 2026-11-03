# finops-agent

Autonomous AWS cost agent built on a personal account. Steps 1–4 of 6 are done:

1. `terraform/` – sandbox of deliberately planted waste (idle EC2, orphan EBS volume, orphan Elastic IP).
2. `mcp_server/` – read-only MCP server exposing waste finders to Claude.
3. `agent/` – Claude tool-use loop over that server; prints a ranked savings report (capped at 10 turns).
4. `agent/pr.py` – if `GITHUB_REPO` (owner/name) and `GITHUB_TOKEN` (contents + PR write) are set, opens a PR with the report under `finops-reports/`.

Next: MongoDB audit log → eval against the planted waste.

## Run
```bash
pip install -e '.[dev]' && pytest          # tests use moto, no AWS needed
python -m mcp_server.server                # stdio MCP server (uses your AWS creds)
ANTHROPIC_API_KEY=... python -m agent.agent  # run the agent (FINOPS_MODEL overrides the model)
```
Claude Code: `claude mcp add aws-finops -- python -m mcp_server.server`

## Sandbox (costs money; set an AWS Budget alert first)
```bash
cd terraform && terraform init && terraform apply
terraform destroy      # teardown
```
Tools: `list_unattached_volumes`, `list_unattached_eips`, `list_idle_ec2`, `get_cost_by_service` ($0.01/call).
The server never mutates anything; IAM needs only `ec2:Describe*`, `cloudwatch:GetMetricStatistics`, `ce:GetCostAndUsage`.
