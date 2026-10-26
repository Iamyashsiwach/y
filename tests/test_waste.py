import boto3
from datetime import datetime, timedelta, timezone
from moto import mock_aws

from mcp_server import waste

R = "us-east-1"


@mock_aws
def test_unattached_volumes_only_reports_available():
    ec2 = boto3.client("ec2", region_name=R)
    ec2.create_volume(AvailabilityZone=f"{R}a", Size=10)
    vid = ec2.create_volume(AvailabilityZone=f"{R}a", Size=20)["VolumeId"]
    iid = ec2.run_instances(ImageId="ami-12345678", MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
    ec2.attach_volume(VolumeId=vid, InstanceId=iid, Device="/dev/sdh")
    found = waste.unattached_volumes(ec2)
    assert [v["size_gb"] for v in found] == [10]
    assert found[0]["est_monthly_usd"] == 0.8


@mock_aws
def test_unattached_eips_skips_associated():
    ec2 = boto3.client("ec2", region_name=R)
    orphan = ec2.allocate_address(Domain="vpc")["AllocationId"]
    used = ec2.allocate_address(Domain="vpc")["AllocationId"]
    iid = ec2.run_instances(ImageId="ami-12345678", MinCount=1, MaxCount=1)["Instances"][0]["InstanceId"]
    ec2.associate_address(AllocationId=used, InstanceId=iid)
    assert [a["allocation_id"] for a in waste.unattached_eips(ec2)] == [orphan]


@mock_aws
def test_idle_instances_uses_cpu_and_skips_no_data():
    ec2 = boto3.client("ec2", region_name=R)
    cw = boto3.client("cloudwatch", region_name=R)
    ids = [i["InstanceId"] for i in ec2.run_instances(ImageId="ami-12345678", MinCount=3, MaxCount=3)["Instances"]]
    for iid, cpu in zip(ids[:2], (1.0, 80.0)):  # third has no datapoints
        cw.put_metric_data(
            Namespace="AWS/EC2",
            MetricData=[{
                "MetricName": "CPUUtilization",
                "Dimensions": [{"Name": "InstanceId", "Value": iid}],
                "Timestamp": datetime.now(timezone.utc) - timedelta(days=1),
                "Value": cpu,
            }],
        )
    assert [i["id"] for i in waste.idle_instances(ec2, cw)] == [ids[0]]
