resource "aws_iam_instance_profile" "tfer--airflow-ec2-profil" {
  name = "airflow-ec2-profil"
  path = "/"
  role = "airflow-ec2-role"
}

resource "aws_iam_instance_profile" "tfer--mlflow-ec2-profil" {
  name = "mlflow-ec2-profil"
  path = "/"
  role = "mlflow-ec2-role"
}

resource "aws_iam_instance_profile" "tfer--mlflow-ec2-profil2" {
  name = "mlflow-ec2-profil2"
  path = "/"
  role = "mlflow-ec2-role2"
}

resource "aws_iam_instance_profile" "tfer--nappecast-ec2-profil" {
  name = "nappecast-ec2-profil"
  path = "/"
  role = "nappecast-ec2-role"
}
