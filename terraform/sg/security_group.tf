resource "aws_security_group" "tfer--airflow-ec2-sg_sg-0d34dad32a2811316" {
  description = "AirFlow server"
  name        = "airflow-ec2-sg"
  vpc_id      = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--default_sg-0bbe212fba40c1945" {
  description = "default VPC security group"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks     = ["86.213.23.196/32"]
    from_port       = "5432"
    protocol        = "tcp"
    security_groups = ["${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--mlflow-ec2-sg_sg-0b61e357948375b5f_id}"]
    self            = "false"
    to_port         = "5432"
  }

  ingress {
    from_port = "0"
    protocol  = "-1"
    self      = "true"
    to_port   = "0"
  }

  name   = "default"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--launch-wizard-1_sg-0d141991cb2b70233" {
  description = "launch-wizard-1 created 2026-05-19T11:38:09.551Z"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["86.213.23.196/32"]
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  name   = "launch-wizard-1"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--launch-wizard-2_sg-0b6915471f03058c1" {
  description = "launch-wizard-2 created 2026-06-28T10:08:21.283Z"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  name   = "launch-wizard-2"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--launch-wizard-3_sg-0a3399d41fa305022" {
  description = "launch-wizard-3 created 2026-06-30T08:18:46.677Z"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  name   = "launch-wizard-3"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--launch-wizard-4_sg-041b00dea87133085" {
  description = "launch-wizard-4 created 2026-06-30T09:13:12.827Z"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  name   = "launch-wizard-4"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--mlflow-ec2-sg-v2_sg-06cdd4979e8928cf2" {
  description = "MLflow server"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks     = ["83.114.10.235/32", "86.213.23.196/32", "89.2.16.76/32"]
    from_port       = "5000"
    protocol        = "tcp"
    security_groups = ["${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--nappecast-ec2-group_sg-068b0a101c18effad_id}"]
    self            = "false"
    to_port         = "5000"
  }

  ingress {
    cidr_blocks = ["86.213.23.196/32"]
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  name   = "mlflow-ec2-sg-v2"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--mlflow-ec2-sg_sg-0b61e357948375b5f" {
  description = "MLflow server"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["86.213.23.196/32"]
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  ingress {
    cidr_blocks     = ["86.213.23.196/32"]
    from_port       = "5000"
    protocol        = "tcp"
    security_groups = ["${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--nappecast-ec2-group_sg-068b0a101c18effad_id}"]
    self            = "false"
    to_port         = "5000"
  }

  ingress {
    cidr_blocks     = ["86.213.23.196/32"]
    from_port       = "5432"
    protocol        = "tcp"
    security_groups = ["${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--nappecast-ec2-group_sg-068b0a101c18effad_id}"]
    self            = "true"
    to_port         = "5432"
  }

  name   = "mlflow-ec2-sg"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--nappecast-ec2-group_sg-068b0a101c18effad" {
  description = "Streamlit + API"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "443"
    protocol    = "tcp"
    self        = "false"
    to_port     = "443"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "80"
    protocol    = "tcp"
    self        = "false"
    to_port     = "80"
  }

  ingress {
    cidr_blocks = ["86.213.23.196/32"]
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  ingress {
    description     = "Lambda trigger pipeline"
    from_port       = "8000"
    protocol        = "tcp"
    security_groups = ["${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--nappecast-lambda-trigger-sg_sg-065b0eaa02d80fb84_id}"]
    self            = "false"
    to_port         = "8000"
  }

  ingress {
    from_port       = "8000"
    protocol        = "tcp"
    security_groups = ["${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--airflow-ec2-sg_sg-0d34dad32a2811316_id}"]
    self            = "false"
    to_port         = "8000"
  }

  name   = "nappecast-ec2-group"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--nappecast-lambda-trigger-sg_sg-065b0eaa02d80fb84" {
  description = "SG du Lambda declencheur du pipeline NappeCast"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  name   = "nappecast-lambda-trigger-sg"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--nappecast-sg_sg-0052194108a4fd96e" {
  description = "Streamlit + API"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "443"
    protocol    = "tcp"
    self        = "false"
    to_port     = "443"
  }

  ingress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "80"
    protocol    = "tcp"
    self        = "false"
    to_port     = "80"
  }

  ingress {
    cidr_blocks = ["86.213.23.196/32"]
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  name   = "nappecast-sg"
  vpc_id = "vpc-0400adbbc2bdd55be"
}

resource "aws_security_group" "tfer--rds-nappecast-sg_sg-0775b4249e3eb9757" {
  description = "Acces au serveur RDS NappeCast"

  egress {
    cidr_blocks = ["0.0.0.0/0"]
    from_port   = "0"
    protocol    = "-1"
    self        = "false"
    to_port     = "0"
  }

  ingress {
    cidr_blocks = ["86.213.23.196/32"]
    description = "Postgre"
    from_port   = "5432"
    protocol    = "tcp"
    self        = "false"
    to_port     = "5432"
  }

  ingress {
    cidr_blocks = ["86.213.23.196/32"]
    description = "SSH"
    from_port   = "22"
    protocol    = "tcp"
    self        = "false"
    to_port     = "22"
  }

  ingress {
    cidr_blocks = ["86.213.23.196/32"]
    from_port   = "5000"
    protocol    = "tcp"
    self        = "false"
    to_port     = "5000"
  }

  ingress {
    description     = "Airflow"
    from_port       = "5432"
    protocol        = "tcp"
    security_groups = ["${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--airflow-ec2-sg_sg-0d34dad32a2811316_id}"]
    self            = "false"
    to_port         = "5432"
  }

  name   = "rds-nappecast-sg"
  vpc_id = "vpc-0400adbbc2bdd55be"
}
