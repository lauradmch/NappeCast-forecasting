resource "aws_security_group_rule" "tfer--sg-0d34dad32a2811316_egress_-1_-1_-1_0-002E-0-002E-0-002E-0-002F-0" {
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = "0"
  protocol          = "-1"
  security_group_id = "${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--airflow-ec2-sg_sg-0d34dad32a2811316_id}"
  to_port           = "0"
  type              = "egress"
}

resource "aws_security_group_rule" "tfer--sg-0d34dad32a2811316_ingress_tcp_22_22_86-002E-213-002E-23-002E-196-002F-32" {
  cidr_blocks       = ["86.213.23.196/32"]
  from_port         = "22"
  protocol          = "tcp"
  security_group_id = "${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--airflow-ec2-sg_sg-0d34dad32a2811316_id}"
  to_port           = "22"
  type              = "ingress"
}

resource "aws_security_group_rule" "tfer--sg-0d34dad32a2811316_ingress_tcp_8080_8080_86-002E-213-002E-23-002E-196-002F-32" {
  cidr_blocks       = ["86.213.23.196/32"]
  from_port         = "8080"
  protocol          = "tcp"
  security_group_id = "${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--airflow-ec2-sg_sg-0d34dad32a2811316_id}"
  to_port           = "8080"
  type              = "ingress"
}

resource "aws_security_group_rule" "tfer--sg-0d34dad32a2811316_ingress_tcp_8080_8080_86-002E-213-002E-23-002E-196-002F-32_sg-068b0a101c18effad" {
  from_port                = "8080"
  protocol                 = "tcp"
  security_group_id        = "${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--airflow-ec2-sg_sg-0d34dad32a2811316_id}"
  source_security_group_id = "${data.terraform_remote_state.sg.outputs.aws_security_group_tfer--nappecast-ec2-group_sg-068b0a101c18effad_id}"
  to_port                  = "8080"
  type                     = "ingress"
}
