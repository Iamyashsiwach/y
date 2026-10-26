"""Read-only AWS waste finders. Clients are passed in so tests can use moto."""
from datetime import datetime, timedelta, timezone

# Rough us-east-1 list prices (USD/month); the agent treats these as estimates.
GP3_PER_GB = 0.08
EIP_PER_MONTH = 3.65


def unattached_volumes(ec2) -> list[dict]:
    pages = ec2.get_paginator("describe_volumes").paginate(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )
    return [
        {"id": v["VolumeId"], "size_gb": v["Size"], "est_monthly_usd": round(v["Size"] * GP3_PER_GB, 2)}
        for p in pages
        for v in p["Volumes"]
    ]


def unattached_eips(ec2) -> list[dict]:
    return [
        {"allocation_id": a["AllocationId"], "ip": a["PublicIp"], "est_monthly_usd": EIP_PER_MONTH}
        for a in ec2.describe_addresses()["Addresses"]
        if "AssociationId" not in a
    ]


def idle_instances(ec2, cloudwatch, cpu_threshold: float = 5.0, days: int = 7) -> list[dict]:
    end = datetime.now(timezone.utc)
    pages = ec2.get_paginator("describe_instances").paginate(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )
    out = []
    for p in pages:
        for r in p["Reservations"]:
            for i in r["Instances"]:
                points = cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": i["InstanceId"]}],
                    StartTime=end - timedelta(days=days),
                    EndTime=end,
                    Period=3600 * 24,
                    Statistics=["Average"],
                )["Datapoints"]
                if not points:  # no data yet (new instance): don't guess
                    continue
                avg = sum(d["Average"] for d in points) / len(points)
                if avg < cpu_threshold:
                    out.append({"id": i["InstanceId"], "type": i["InstanceType"], "avg_cpu_pct": round(avg, 2)})
    return out


def cost_by_service(ce, days: int = 30) -> list[dict]:
    end = datetime.now(timezone.utc).date()
    r = ce.get_cost_and_usage(  # each call costs $0.01
        TimePeriod={"Start": str(end - timedelta(days=days)), "End": str(end)},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )
    totals: dict[str, float] = {}
    for period in r["ResultsByTime"]:
        for g in period["Groups"]:
            totals[g["Keys"][0]] = totals.get(g["Keys"][0], 0) + float(g["Metrics"]["UnblendedCost"]["Amount"])
    return sorted(({"service": k, "usd": round(v, 2)} for k, v in totals.items()), key=lambda x: -x["usd"])
