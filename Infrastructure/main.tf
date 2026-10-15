terraform {
  required_version = ">= 1.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# --- Providers ---
provider "aws" {
  alias  = "mumbai"
  region = "ap-south-1"
}

provider "aws" {
  alias  = "virginia"
  region = "us-east-1"
}

# --- AMIs ---
data "aws_ami" "mumbai_ubuntu" {
  provider    = aws.mumbai
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"]
}

data "aws_ami" "virginia_ubuntu" {
  provider    = aws.virginia
  most_recent = true
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
  owners = ["099720109477"]
}

# --- Key Pairs & TLS ---
resource "tls_private_key" "mumbai_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "mumbai_auth" {
  provider   = aws.mumbai
  key_name   = "agcp-key"
  public_key = tls_private_key.mumbai_key.public_key_openssh
}

resource "local_file" "mumbai_pem" {
  content         = tls_private_key.mumbai_key.private_key_pem
  filename        = "agcp-key.pem"
  file_permission = "0400"
}

resource "tls_private_key" "virginia_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "virginia_auth" {
  provider   = aws.virginia
  key_name   = "agcp-key-virginia"
  public_key = tls_private_key.virginia_key.public_key_openssh
}

resource "local_file" "virginia_pem" {
  content         = tls_private_key.virginia_key.private_key_pem
  filename        = "agcp-key-virginia.pem"
  file_permission = "0400"
}

# --- Security Groups ---
resource "aws_security_group" "mumbai_sg" {
  provider    = aws.mumbai
  name        = "agcp-mumbai-sg"
  description = "Allow SSH and Node Exporter"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "virginia_sg" {
  provider    = aws.virginia
  name        = "agcp-virginia-sg"
  description = "Allow SSH and Node Exporter"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 9100
    to_port     = 9100
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# --- EC2 Worker Nodes with Node Exporter User Data ---
locals {
  node_exporter_user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update -y
              sudo useradd --no-create-home --shell /bin/false node_exporter
              cd /tmp
              wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
              tar xvf node_exporter-1.7.0.linux-amd64.tar.gz
              sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
              sudo chown node_exporter:node_exporter /usr/local/bin/node_exporter
              
              sudo bash -c 'cat << 'EOT' > /etc/systemd/system/node_exporter.service
              [Unit]
              Description=Node Exporter
              After=network.target

              [Service]
              User=node_exporter
              Group=node_exporter
              Type=simple
              ExecStart=/usr/local/bin/node_exporter

              [Install]
              WantedBy=multi-user.target
              EOT'

              sudo systemctl daemon-reload
              sudo systemctl start node_exporter
              sudo systemctl enable node_exporter
              EOF
}

resource "aws_instance" "mumbai_worker" {
  provider               = aws.mumbai
  ami                    = data.aws_ami.mumbai_ubuntu.id
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.mumbai_auth.key_name
  vpc_security_group_ids = [aws_security_group.mumbai_sg.id]
  user_data              = local.node_exporter_user_data

  tags = {
    Name = "Mumbai-Worker"
  }
}

resource "aws_instance" "virginia_worker" {
  provider               = aws.virginia
  ami                    = data.aws_ami.virginia_ubuntu.id
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.virginia_auth.key_name
  vpc_security_group_ids = [aws_security_group.virginia_sg.id]
  user_data              = local.node_exporter_user_data

  tags = {
    Name = "Virginia-Worker"
  }
}

# --- Output JSON File for Instance IPs ---
resource "local_file" "instance_ips_json" {
  content = jsonencode({
    mumbai = {
      instance_id = aws_instance.mumbai_worker.id
      public_ip   = aws_instance.mumbai_worker.public_ip
    }
    virginia = {
      instance_id = aws_instance.virginia_worker.id
      public_ip   = aws_instance.virginia_worker.public_ip
    }
  })
  filename = "instance_ips.json"
}

# --- Teammate IAM User & Access Keys ---
resource "aws_iam_user" "teammate" {
  name = "agcp-teammate"
  path = "/"
}

resource "aws_iam_user_policy_attachment" "teammate_power_user" {
  user       = aws_iam_user.teammate.name
  policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}

resource "aws_iam_access_key" "teammate_key" {
  user = aws_iam_user.teammate.name
}

resource "local_file" "teammate_credentials_json" {
  content = jsonencode({
    access_key_id     = aws_iam_access_key.teammate_key.id
    secret_access_key = aws_iam_access_key.teammate_key.secret
    created_at        = timestamp()
  })
  filename = "teammate_credentials.json"
}
