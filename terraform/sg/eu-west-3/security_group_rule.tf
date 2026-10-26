resource "aws_security_group_rule" "airflow_egress_all" {
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = "0"
  protocol          = "-1"
  security_group_id = aws_security_group.tfer--airflow-ec2-sg_sg-0d34dad32a2811316.id
  to_port           = "0"
  type              = "egress"
}

resource "aws_security_group_rule" "airflow_ssh_admin" {
  cidr_blocks       = [var.admin_cidr]
  from_port         = "22"
  protocol          = "tcp"
  security_group_id = aws_security_group.tfer--airflow-ec2-sg_sg-0d34dad32a2811316.id
  to_port           = "22"
  type              = "ingress"
}

resource "aws_security_group_rule" "airflow_ui_admin" {
  cidr_blocks       = [var.admin_cidr]
  from_port         = "8080"
  protocol          = "tcp"
  security_group_id = aws_security_group.tfer--airflow-ec2-sg_sg-0d34dad32a2811316.id
  to_port           = "8080"
  type              = "ingress"
}

resource "aws_security_group_rule" "airflow_ui_from_app" {
  from_port                = "8080"
  protocol                 = "tcp"
  security_group_id        = aws_security_group.tfer--airflow-ec2-sg_sg-0d34dad32a2811316.id
  source_security_group_id = aws_security_group.tfer--nappecast-ec2-group_sg-068b0a101c18effad.id
  to_port                  = "8080"
  type                     = "ingress"
}
