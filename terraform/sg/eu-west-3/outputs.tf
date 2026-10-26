output "aws_security_group_rule_airflow_egress_all_id" {
  value = "${aws_security_group_rule.airflow_egress_all.id}"
}

output "aws_security_group_rule_airflow_ssh_admin_id" {
  value = "${aws_security_group_rule.airflow_ssh_admin.id}"
}

output "aws_security_group_rule_airflow_ui_admin_id" {
  value = "${aws_security_group_rule.airflow_ui_admin.id}"
}

output "aws_security_group_rule_airflow_ui_from_app_id" {
  value = "${aws_security_group_rule.airflow_ui_from_app.id}"
}

output "aws_security_group_tfer--airflow-ec2-sg_sg-0d34dad32a2811316_id" {
  value = "${aws_security_group.tfer--airflow-ec2-sg_sg-0d34dad32a2811316.id}"
}

output "aws_security_group_tfer--default_sg-0bbe212fba40c1945_id" {
  value = "${aws_security_group.tfer--default_sg-0bbe212fba40c1945.id}"
}

output "aws_security_group_tfer--launch-wizard-1_sg-0d141991cb2b70233_id" {
  value = "${aws_security_group.tfer--launch-wizard-1_sg-0d141991cb2b70233.id}"
}

output "aws_security_group_tfer--launch-wizard-2_sg-0b6915471f03058c1_id" {
  value = "${aws_security_group.tfer--launch-wizard-2_sg-0b6915471f03058c1.id}"
}

output "aws_security_group_tfer--launch-wizard-3_sg-0a3399d41fa305022_id" {
  value = "${aws_security_group.tfer--launch-wizard-3_sg-0a3399d41fa305022.id}"
}

output "aws_security_group_tfer--launch-wizard-4_sg-041b00dea87133085_id" {
  value = "${aws_security_group.tfer--launch-wizard-4_sg-041b00dea87133085.id}"
}

output "aws_security_group_tfer--mlflow-ec2-sg-v2_sg-06cdd4979e8928cf2_id" {
  value = "${aws_security_group.tfer--mlflow-ec2-sg-v2_sg-06cdd4979e8928cf2.id}"
}

output "aws_security_group_tfer--mlflow-ec2-sg_sg-0b61e357948375b5f_id" {
  value = "${aws_security_group.tfer--mlflow-ec2-sg_sg-0b61e357948375b5f.id}"
}

output "aws_security_group_tfer--nappecast-ec2-group_sg-068b0a101c18effad_id" {
  value = "${aws_security_group.tfer--nappecast-ec2-group_sg-068b0a101c18effad.id}"
}

output "aws_security_group_tfer--nappecast-lambda-trigger-sg_sg-065b0eaa02d80fb84_id" {
  value = "${aws_security_group.tfer--nappecast-lambda-trigger-sg_sg-065b0eaa02d80fb84.id}"
}

output "aws_security_group_tfer--nappecast-sg_sg-0052194108a4fd96e_id" {
  value = "${aws_security_group.tfer--nappecast-sg_sg-0052194108a4fd96e.id}"
}

output "aws_security_group_tfer--rds-nappecast-sg_sg-0775b4249e3eb9757_id" {
  value = "${aws_security_group.tfer--rds-nappecast-sg_sg-0775b4249e3eb9757.id}"
}
