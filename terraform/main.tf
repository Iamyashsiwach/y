# Deliberately wasteful sandbox: the agent's test fixture. Every resource is tagged
# planted_waste=true so the eval (step 6) can score findings. Destroy when done.
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

variable "region" { default = "us-east-1" }

provider "aws" {
  region = var.region
  default_tags { tags = { project = "finops-agent", planted_waste = "true" } }
}

data "aws_ami" "al2023" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }
}

# Waste 1: running instance that does nothing (free-tier size; ~0% CPU)
resource "aws_instance" "idle" {
  ami           = data.aws_ami.al2023.id
  instance_type = "t3.micro"
  tags          = { Name = "waste-idle-ec2" }
}

# Waste 2: EBS volume attached to nothing
resource "aws_ebs_volume" "orphan" {
  availability_zone = "${var.region}a"
  size              = 8
  type              = "gp3"
  tags              = { Name = "waste-orphan-volume" }
}

# Waste 3: Elastic IP not associated with anything (billed hourly)
resource "aws_eip" "orphan" {
  domain = "vpc"
  tags   = { Name = "waste-orphan-eip" }
}
