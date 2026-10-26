resource "aws_iam_role" "tfer--AWSServiceRoleForAmazonEKS" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "eks.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description          = "Allows Amazon EKS to call AWS services on your behalf."
  managed_policy_arns  = ["arn:aws:iam::aws:policy/aws-service-role/AmazonEKSServiceRolePolicy"]
  max_session_duration = "3600"
  name                 = "AWSServiceRoleForAmazonEKS"
  path                 = "/aws-service-role/eks.amazonaws.com/"
}

resource "aws_iam_role" "tfer--AWSServiceRoleForAmazonEKSNodegroup" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "eks-nodegroup.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description          = "This policy allows Amazon EKS to create and manage Nodegroups"
  managed_policy_arns  = ["arn:aws:iam::aws:policy/aws-service-role/AWSServiceRoleForAmazonEKSNodegroup"]
  max_session_duration = "3600"
  name                 = "AWSServiceRoleForAmazonEKSNodegroup"
  path                 = "/aws-service-role/eks-nodegroup.amazonaws.com/"
}

resource "aws_iam_role" "tfer--AWSServiceRoleForAutoScaling" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "autoscaling.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description          = "Default Service-Linked Role enables access to AWS Services and Resources used or managed by Auto Scaling"
  managed_policy_arns  = ["arn:aws:iam::aws:policy/aws-service-role/AutoScalingServiceRolePolicy"]
  max_session_duration = "3600"
  name                 = "AWSServiceRoleForAutoScaling"
  path                 = "/aws-service-role/autoscaling.amazonaws.com/"
}

resource "aws_iam_role" "tfer--AWSServiceRoleForRDS" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "rds.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description          = "Allows Amazon RDS to manage AWS resources on your behalf"
  managed_policy_arns  = ["arn:aws:iam::aws:policy/aws-service-role/AmazonRDSServiceRolePolicy"]
  max_session_duration = "3600"
  name                 = "AWSServiceRoleForRDS"
  path                 = "/aws-service-role/rds.amazonaws.com/"
}

resource "aws_iam_role" "tfer--AWSServiceRoleForResourceExplorer" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "resource-explorer-2.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  managed_policy_arns  = ["arn:aws:iam::aws:policy/aws-service-role/AWSResourceExplorerServiceRolePolicy"]
  max_session_duration = "3600"
  name                 = "AWSServiceRoleForResourceExplorer"
  path                 = "/aws-service-role/resource-explorer-2.amazonaws.com/"
}

resource "aws_iam_role" "tfer--AWSServiceRoleForSupport" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "support.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description          = "Enables resource access for AWS to provide billing, administrative and support services"
  managed_policy_arns  = ["arn:aws:iam::aws:policy/aws-service-role/AWSSupportServiceRolePolicy"]
  max_session_duration = "3600"
  name                 = "AWSServiceRoleForSupport"
  path                 = "/aws-service-role/support.amazonaws.com/"
}

resource "aws_iam_role" "tfer--AWSServiceRoleForTrustedAdvisor" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "trustedadvisor.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description          = "Access for the AWS Trusted Advisor Service to help reduce cost, increase performance, and improve security of your AWS environment."
  managed_policy_arns  = ["arn:aws:iam::aws:policy/aws-service-role/AWSTrustedAdvisorServiceRolePolicy"]
  max_session_duration = "3600"
  name                 = "AWSServiceRoleForTrustedAdvisor"
  path                 = "/aws-service-role/trustedadvisor.amazonaws.com/"
}

resource "aws_iam_role" "tfer--airflow-ec2-role" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description = "Rôle EC2 pour l'orchestrateur Airflow"

  inline_policy {
    name   = "GetSecretsManagerKey"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":\"secretsmanager:GetSecretValue\",\"Effect\":\"Allow\",\"Resource\":\"arn:aws:secretsmanager:eu-west-3:844099234486:secret:airflow/prod*\",\"Sid\":\"ReadSecret\"},{\"Action\":\"ecr:GetAuthorizationToken\",\"Effect\":\"Allow\",\"Resource\":\"*\",\"Sid\":\"EcrAuth\"},{\"Action\":[\"ecr:BatchGetImage\",\"ecr:GetDownloadUrlForLayer\"],\"Effect\":\"Allow\",\"Resource\":\"arn:aws:ecr:eu-west-3:844099234486:repository/airflow\",\"Sid\":\"EcrPull\"}]}"
  }

  inline_policy {
    name   = "airflow-permissions"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":[\"s3:GetObject\",\"s3:PutObject\",\"s3:DeleteObject\",\"s3:ListBucket\"],\"Effect\":\"Allow\",\"Resource\":[\"arn:aws:s3:::nappecast\",\"arn:aws:s3:::nappecast/airflow/*\"],\"Sid\":\"S3Sync\"},{\"Action\":[\"emr-serverless:StartJobRun\",\"emr-serverless:GetJobRun\"],\"Effect\":\"Allow\",\"Resource\":\"*\",\"Sid\":\"EMRServerlessTrigger\"},{\"Action\":[\"ec2:RunInstances\",\"ec2:TerminateInstances\",\"ec2:DescribeInstances\",\"ec2:CreateTags\"],\"Effect\":\"Allow\",\"Resource\":\"*\",\"Sid\":\"EC2SpotForTraining\"}]}"
  }

  managed_policy_arns  = ["arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore", "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"]
  max_session_duration = "3600"
  name                 = "airflow-ec2-role"
  path                 = "/"
}

resource "aws_iam_role" "tfer--github-actions-deploy" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:lauradmch@280640877/NappeCast-forecasting@1304105848:environment:production"
        }
      },
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::844099234486:oidc-provider/token.actions.githubusercontent.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  inline_policy {
    name   = "github-actions-ecr"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":\"ecr:GetAuthorizationToken\",\"Effect\":\"Allow\",\"Resource\":\"*\"},{\"Action\":[\"ecr:DescribeImages\",\"ecr:BatchCheckLayerAvailability\",\"ecr:BatchGetImage\",\"ecr:GetDownloadUrlForLayer\",\"ecr:InitiateLayerUpload\",\"ecr:UploadLayerPart\",\"ecr:CompleteLayerUpload\",\"ecr:PutImage\"],\"Effect\":\"Allow\",\"Resource\":\"arn:aws:ecr:eu-west-3:844099234486:repository/mlflow\"}]}"
  }

  inline_policy {
    name   = "github-actions-ecr-airflow"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":\"ecr:GetAuthorizationToken\",\"Effect\":\"Allow\",\"Resource\":\"*\"},{\"Action\":[\"ecr:DescribeImages\",\"ecr:BatchCheckLayerAvailability\",\"ecr:BatchGetImage\",\"ecr:GetDownloadUrlForLayer\",\"ecr:InitiateLayerUpload\",\"ecr:UploadLayerPart\",\"ecr:CompleteLayerUpload\",\"ecr:PutImage\"],\"Effect\":\"Allow\",\"Resource\":\"arn:aws:ecr:eu-west-3:844099234486:repository/airflow\"}]}"
  }

  inline_policy {
    name   = "github-actions-ecr-streamlit"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":\"ecr:GetAuthorizationToken\",\"Effect\":\"Allow\",\"Resource\":\"*\",\"Sid\":\"EcrAuth\"},{\"Action\":[\"ecr:DescribeImages\",\"ecr:BatchCheckLayerAvailability\",\"ecr:GetDownloadUrlForLayer\",\"ecr:BatchGetImage\",\"ecr:InitiateLayerUpload\",\"ecr:UploadLayerPart\",\"ecr:CompleteLayerUpload\",\"ecr:PutImage\"],\"Effect\":\"Allow\",\"Resource\":[\"arn:aws:ecr:eu-west-3:844099234486:repository/streamlit\",\"arn:aws:ecr:eu-west-3:844099234486:repository/api\"],\"Sid\":\"EcrPushApiapp\"}]}"
  }

  inline_policy {
    name   = "sg-ssh"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":[\"ec2:AuthorizeSecurityGroupIngress\",\"ec2:RevokeSecurityGroupIngress\"],\"Effect\":\"Allow\",\"Resource\":[\"arn:aws:ec2:eu-west-3:844099234486:security-group/sg-06cdd4979e8928cf2\",\"arn:aws:ec2:eu-west-3:844099234486:security-group/sg-0d34dad32a2811316\",\"arn:aws:ec2:eu-west-3:844099234486:security-group/sg-068b0a101c18effad\"],\"Sid\":\"SshTemporaireRunner\"},{\"Action\":\"ecr:DescribeImages\",\"Effect\":\"Allow\",\"Resource\":\"arn:aws:ecr:eu-west-3:844099234486:repository/mlflow\",\"Sid\":\"VerifTagECR\"}]}"
  }

  max_session_duration = "3600"
  name                 = "github-actions-deploy"
  path                 = "/"
}

resource "aws_iam_role" "tfer--mlflow-ec2-role" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  max_session_duration = "3600"
  name                 = "mlflow-ec2-role"
  path                 = "/"
}

resource "aws_iam_role" "tfer--mlflow-ec2-role2" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  inline_policy {
    name   = "GetSecretsManagerKey"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":\"secretsmanager:GetSecretValue\",\"Effect\":\"Allow\",\"Resource\":\"arn:aws:secretsmanager:eu-west-3:844099234486:secret:mlflow/prod*\",\"Sid\":\"ReadSecret\"},{\"Action\":\"ecr:GetAuthorizationToken\",\"Effect\":\"Allow\",\"Resource\":\"*\",\"Sid\":\"EcrAuth\"},{\"Action\":[\"ecr:BatchGetImage\",\"ecr:GetDownloadUrlForLayer\"],\"Effect\":\"Allow\",\"Resource\":\"arn:aws:ecr:eu-west-3:844099234486:repository/mlflow\",\"Sid\":\"EcrPull\"},{\"Action\":[\"s3:GetObject\",\"s3:PutObject\",\"s3:DeleteObject\"],\"Effect\":\"Allow\",\"Resource\":\"arn:aws:s3:::nappecast/mlflow-artifacts/*\",\"Sid\":\"MlflowArtifacts\"},{\"Action\":\"s3:ListBucket\",\"Condition\":{\"StringLike\":{\"s3:prefix\":[\"mlflow-artifacts/*\"]}},\"Effect\":\"Allow\",\"Resource\":\"arn:aws:s3:::nappecast\",\"Sid\":\"MlflowArtifactsList\"}]}"
  }

  inline_policy {
    name   = "s3-mlflow-artifacts2"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":[\"s3:GetObject\",\"s3:PutObject\",\"s3:ListBucket\"],\"Effect\":\"Allow\",\"Resource\":[\"arn:aws:s3:::nappecast\",\"arn:aws:s3:::nappecast/mlflow-artifacts/*\",\"arn:aws:s3:::nappecast/app/docker/mlflow/*\"]}]}"
  }

  managed_policy_arns  = ["arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"]
  max_session_duration = "3600"
  name                 = "mlflow-ec2-role2"
  path                 = "/"
}

resource "aws_iam_role" "tfer--nappecast-ec2-role" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  inline_policy {
    name   = "GetSecretsManagerKey"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":\"secretsmanager:GetSecretValue\",\"Effect\":\"Allow\",\"Resource\":\"arn:aws:secretsmanager:eu-west-3:844099234486:secret:appapi/prod-latest-*\",\"Sid\":\"ReadSecret\"},{\"Action\":\"ecr:GetAuthorizationToken\",\"Effect\":\"Allow\",\"Resource\":\"*\",\"Sid\":\"EcrAuth\"},{\"Action\":[\"ecr:BatchGetImage\",\"ecr:GetDownloadUrlForLayer\"],\"Effect\":\"Allow\",\"Resource\":\"arn:aws:ecr:eu-west-3:844099234486:repository/appapi\",\"Sid\":\"EcrPull\"}]}"
  }

  managed_policy_arns  = ["arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly", "arn:aws:iam::aws:policy/AmazonS3FullAccess", "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"]
  max_session_duration = "3600"
  name                 = "nappecast-ec2-role"
  path                 = "/"
}

resource "aws_iam_role" "tfer--nappecast-scheduler-ec2-role" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "scheduler.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  inline_policy {
    name   = "nappecast-start-stop-instances"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":[\"ec2:StartInstances\",\"ec2:StopInstances\"],\"Effect\":\"Allow\",\"Resource\":[\"arn:aws:ec2:eu-west-3:844099234486:instance/i-017d82908629e09cd\",\"arn:aws:ec2:eu-west-3:844099234486:instance/i-06b315e78fa277e77\"]}]}"
  }

  max_session_duration = "3600"
  name                 = "nappecast-scheduler-ec2-role"
  path                 = "/"
}

resource "aws_iam_role" "tfer--nappecast-scheduler-invoke-trigger-role" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "scheduler.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  inline_policy {
    name   = "nappecast-invoke-trigger-lambda"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":\"lambda:InvokeFunction\",\"Effect\":\"Allow\",\"Resource\":\"arn:aws:lambda:eu-west-3:844099234486:function:nappecast-trigger-collect\"}]}"
  }

  max_session_duration = "3600"
  name                 = "nappecast-scheduler-invoke-trigger-role"
  path                 = "/"
}

resource "aws_iam_role" "tfer--nappecast-trigger-lambda-role" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  description          = "Role d'execution du Lambda declencheur NappeCast (VPC)"
  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole", "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"]
  max_session_duration = "3600"
  name                 = "nappecast-trigger-lambda-role"
  path                 = "/"
}

resource "aws_iam_role" "tfer--rds-monitoring-role" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "monitoring.rds.amazonaws.com"
      },
      "Sid": ""
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  managed_policy_arns  = ["arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"]
  max_session_duration = "3600"
  name                 = "rds-monitoring-role"
  path                 = "/"
}

resource "aws_iam_role" "tfer--scheduler-stop-ec2-role" {
  assume_role_policy = <<POLICY
{
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Effect": "Allow",
      "Principal": {
        "Service": "scheduler.amazonaws.com"
      }
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  inline_policy {
    name   = "scheduler-stop-ec2-role"
    policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Action\":\"ec2:StopInstances\",\"Effect\":\"Allow\",\"Resource\":\"arn:aws:ec2:eu-west-3:*:instance/i-017d82908629e09cd\"}]}"
  }

  max_session_duration = "3600"
  name                 = "scheduler-stop-ec2-role"
  path                 = "/"
}
