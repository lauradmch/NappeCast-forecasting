output "aws_instance_tfer--i-017d82908629e09cd_app-server_id" {
  value = "${aws_instance.tfer--i-017d82908629e09cd_app-server.id}"
}

output "aws_instance_tfer--i-06b315e78fa277e77_mlflow-server-sqlite_id" {
  value = "${aws_instance.tfer--i-06b315e78fa277e77_mlflow-server-sqlite.id}"
}

output "aws_instance_tfer--i-0c770608e3877ec43_airflow-orchestrator_id" {
  value = "${aws_instance.tfer--i-0c770608e3877ec43_airflow-orchestrator.id}"
}
