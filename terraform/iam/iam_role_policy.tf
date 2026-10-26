resource "aws_iam_role_policy" "tfer--airflow-ec2-role_GetSecretsManagerKey" {
  name = "GetSecretsManagerKey"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "secretsmanager:GetSecretValue",
      "Effect": "Allow",
      "Resource": "arn:aws:secretsmanager:eu-west-3:844099234486:secret:airflow/prod*",
      "Sid": "ReadSecret"
    },
    {
      "Action": "ecr:GetAuthorizationToken",
      "Effect": "Allow",
      "Resource": "*",
      "Sid": "EcrAuth"
    },
    {
      "Action": [
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:eu-west-3:844099234486:repository/airflow",
      "Sid": "EcrPull"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "airflow-ec2-role"
}

resource "aws_iam_role_policy" "tfer--airflow-ec2-role_airflow-permissions" {
  name = "airflow-permissions"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::nappecast",
        "arn:aws:s3:::nappecast/airflow/*"
      ],
      "Sid": "S3Sync"
    },
    {
      "Action": [
        "emr-serverless:StartJobRun",
        "emr-serverless:GetJobRun"
      ],
      "Effect": "Allow",
      "Resource": "*",
      "Sid": "EMRServerlessTrigger"
    },
    {
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:DescribeInstances",
        "ec2:CreateTags"
      ],
      "Effect": "Allow",
      "Resource": "*",
      "Sid": "EC2SpotForTraining"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "airflow-ec2-role"
}

resource "aws_iam_role_policy" "tfer--github-actions-deploy_github-actions-ecr" {
  name = "github-actions-ecr"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "ecr:GetAuthorizationToken",
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Action": [
        "ecr:DescribeImages",
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:eu-west-3:844099234486:repository/mlflow"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "github-actions-deploy"
}

resource "aws_iam_role_policy" "tfer--github-actions-deploy_github-actions-ecr-airflow" {
  name = "github-actions-ecr-airflow"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "ecr:GetAuthorizationToken",
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Action": [
        "ecr:DescribeImages",
        "ecr:BatchCheckLayerAvailability",
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:eu-west-3:844099234486:repository/airflow"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "github-actions-deploy"
}

resource "aws_iam_role_policy" "tfer--github-actions-deploy_github-actions-ecr-streamlit" {
  name = "github-actions-ecr-streamlit"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "ecr:GetAuthorizationToken",
      "Effect": "Allow",
      "Resource": "*",
      "Sid": "EcrAuth"
    },
    {
      "Action": [
        "ecr:DescribeImages",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:ecr:eu-west-3:844099234486:repository/streamlit",
        "arn:aws:ecr:eu-west-3:844099234486:repository/api"
      ],
      "Sid": "EcrPushApiapp"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "github-actions-deploy"
}

resource "aws_iam_role_policy" "tfer--github-actions-deploy_sg-ssh" {
  name = "sg-ssh"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "ec2:AuthorizeSecurityGroupIngress",
        "ec2:RevokeSecurityGroupIngress"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:ec2:eu-west-3:844099234486:security-group/sg-06cdd4979e8928cf2",
        "arn:aws:ec2:eu-west-3:844099234486:security-group/sg-0d34dad32a2811316",
        "arn:aws:ec2:eu-west-3:844099234486:security-group/sg-068b0a101c18effad"
      ],
      "Sid": "SshTemporaireRunner"
    },
    {
      "Action": "ecr:DescribeImages",
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:eu-west-3:844099234486:repository/mlflow",
      "Sid": "VerifTagECR"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "github-actions-deploy"
}

resource "aws_iam_role_policy" "tfer--mlflow-ec2-role2_GetSecretsManagerKey" {
  name = "GetSecretsManagerKey"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "secretsmanager:GetSecretValue",
      "Effect": "Allow",
      "Resource": "arn:aws:secretsmanager:eu-west-3:844099234486:secret:mlflow/prod*",
      "Sid": "ReadSecret"
    },
    {
      "Action": "ecr:GetAuthorizationToken",
      "Effect": "Allow",
      "Resource": "*",
      "Sid": "EcrAuth"
    },
    {
      "Action": [
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:eu-west-3:844099234486:repository/mlflow",
      "Sid": "EcrPull"
    },
    {
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::nappecast/mlflow-artifacts/*",
      "Sid": "MlflowArtifacts"
    },
    {
      "Action": "s3:ListBucket",
      "Condition": {
        "StringLike": {
          "s3:prefix": [
            "mlflow-artifacts/*"
          ]
        }
      },
      "Effect": "Allow",
      "Resource": "arn:aws:s3:::nappecast",
      "Sid": "MlflowArtifactsList"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "mlflow-ec2-role2"
}

resource "aws_iam_role_policy" "tfer--mlflow-ec2-role2_s3-mlflow-artifacts2" {
  name = "s3-mlflow-artifacts2"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:s3:::nappecast",
        "arn:aws:s3:::nappecast/mlflow-artifacts/*",
        "arn:aws:s3:::nappecast/app/docker/mlflow/*"
      ]
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "mlflow-ec2-role2"
}

resource "aws_iam_role_policy" "tfer--nappecast-ec2-role_GetSecretsManagerKey" {
  name = "GetSecretsManagerKey"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "secretsmanager:GetSecretValue",
      "Effect": "Allow",
      "Resource": "arn:aws:secretsmanager:eu-west-3:844099234486:secret:appapi/prod-latest-*",
      "Sid": "ReadSecret"
    },
    {
      "Action": "ecr:GetAuthorizationToken",
      "Effect": "Allow",
      "Resource": "*",
      "Sid": "EcrAuth"
    },
    {
      "Action": [
        "ecr:BatchGetImage",
        "ecr:GetDownloadUrlForLayer"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:ecr:eu-west-3:844099234486:repository/appapi",
      "Sid": "EcrPull"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "nappecast-ec2-role"
}

resource "aws_iam_role_policy" "tfer--nappecast-scheduler-ec2-role_nappecast-start-stop-instances" {
  name = "nappecast-start-stop-instances"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "ec2:StartInstances",
        "ec2:StopInstances"
      ],
      "Effect": "Allow",
      "Resource": [
        "arn:aws:ec2:eu-west-3:844099234486:instance/i-017d82908629e09cd",
        "arn:aws:ec2:eu-west-3:844099234486:instance/i-06b315e78fa277e77"
      ]
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "nappecast-scheduler-ec2-role"
}

resource "aws_iam_role_policy" "tfer--nappecast-scheduler-invoke-trigger-role_nappecast-invoke-trigger-lambda" {
  name = "nappecast-invoke-trigger-lambda"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "lambda:InvokeFunction",
      "Effect": "Allow",
      "Resource": "arn:aws:lambda:eu-west-3:844099234486:function:nappecast-trigger-collect"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "nappecast-scheduler-invoke-trigger-role"
}

resource "aws_iam_role_policy" "tfer--scheduler-stop-ec2-role_scheduler-stop-ec2-role" {
  name = "scheduler-stop-ec2-role"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": "ec2:StopInstances",
      "Effect": "Allow",
      "Resource": "arn:aws:ec2:eu-west-3:*:instance/i-017d82908629e09cd"
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  role = "scheduler-stop-ec2-role"
}
