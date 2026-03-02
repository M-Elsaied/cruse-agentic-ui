terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------- AMI (Ubuntu 24.04 LTS) ----------

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ---------- Security Group ----------

resource "aws_security_group" "cruse" {
  name        = "cruse-sg"
  description = "Allow HTTP and SSH for CRUSE demo"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "cruse-sg"
  }
}

# ---------- IAM Role (Secrets Manager access) ----------

resource "aws_iam_role" "cruse" {
  name = "cruse-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "cruse-ec2-role"
  }
}

resource "aws_iam_role_policy" "secrets_access" {
  name = "cruse-secrets-access"
  role = aws_iam_role.cruse.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = "*"
    }]
  })
}

resource "aws_iam_instance_profile" "cruse" {
  name = "cruse-ec2-profile"
  role = aws_iam_role.cruse.name
}

# ---------- EC2 Instance ----------

resource "aws_instance" "cruse" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.cruse.id]
  iam_instance_profile   = aws_iam_instance_profile.cruse.name

  root_block_device {
    volume_size = var.volume_size
    volume_type = "gp3"
  }

  user_data = file("${path.module}/../setup.sh")

  tags = {
    Name = "cruse-demo"
  }
}

# ---------- Elastic IP ----------

resource "aws_eip" "cruse" {
  domain = "vpc"

  tags = {
    Name = "cruse-eip"
  }
}

resource "aws_eip_association" "cruse" {
  instance_id   = aws_instance.cruse.id
  allocation_id = aws_eip.cruse.id
}
