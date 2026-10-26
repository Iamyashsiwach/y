"""Read-only AWS FinOps MCP server. Run: python -m mcp_server.server (stdio)."""
import boto3
from mcp.server.fastmcp import FastMCP

from mcp_server import waste

mcp = FastMCP("aws-finops")


@mcp.tool()
def list_unattached_volumes(region: str = "us-east-1") -> list[dict]:
    """EBS volumes attached to nothing, with estimated monthly cost."""
    return waste.unattached_volumes(boto3.client("ec2", region_name=region))


@mcp.tool()
def list_unattached_eips(region: str = "us-east-1") -> list[dict]:
    """Elastic IPs not associated with any instance or ENI."""
    return waste.unattached_eips(boto3.client("ec2", region_name=region))


@mcp.tool()
def list_idle_ec2(region: str = "us-east-1", cpu_threshold: float = 5.0, days: int = 7) -> list[dict]:
    """Running instances whose average CPU over `days` is below `cpu_threshold` percent."""
    return waste.idle_instances(
        boto3.client("ec2", region_name=region), boto3.client("cloudwatch", region_name=region), cpu_threshold, days
    )


@mcp.tool()
def get_cost_by_service(days: int = 30) -> list[dict]:
    """Spend per AWS service over the last `days`. Costs $0.01 per call; use sparingly."""
    return waste.cost_by_service(boto3.client("ce", region_name="us-east-1"), days)


if __name__ == "__main__":
    mcp.run()
