resource "aws_iam_role_policy_attachment" "tfer--airflow-ec2-role_AmazonSSMManagedInstanceCore" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = "airflow-ec2-role"
}

resource "aws_iam_role_policy_attachment" "tfer--airflow-ec2-role_CloudWatchAgentServerPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
  role       = "airflow-ec2-role"
}

resource "aws_iam_role_policy_attachment" "tfer--mlflow-ec2-role2_AmazonSSMManagedInstanceCore" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = "mlflow-ec2-role2"
}

resource "aws_iam_role_policy_attachment" "tfer--nappecast-ec2-role_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = "nappecast-ec2-role"
}

resource "aws_iam_role_policy_attachment" "tfer--nappecast-ec2-role_AmazonS3FullAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
  role       = "nappecast-ec2-role"
}

resource "aws_iam_role_policy_attachment" "tfer--nappecast-ec2-role_AmazonSSMManagedInstanceCore" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = "nappecast-ec2-role"
}

resource "aws_iam_role_policy_attachment" "tfer--nappecast-trigger-lambda-role_AWSLambdaBasicExecutionRole" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = "nappecast-trigger-lambda-role"
}

resource "aws_iam_role_policy_attachment" "tfer--nappecast-trigger-lambda-role_AWSLambdaVPCAccessExecutionRole" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = "nappecast-trigger-lambda-role"
}

resource "aws_iam_role_policy_attachment" "tfer--rds-monitoring-role_AmazonRDSEnhancedMonitoringRole" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
  role       = "rds-monitoring-role"
}
