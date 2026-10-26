output "aws_iam_group_policy_attachment_tfer--ec2-admin_AmazonEC2ContainerRegistryFullAccess_id" {
  value = aws_iam_group_policy_attachment.tfer--ec2-admin_AmazonEC2ContainerRegistryFullAccess.id
}

output "aws_iam_group_policy_attachment_tfer--ec2-admin_AmazonEC2FullAccess_id" {
  value = aws_iam_group_policy_attachment.tfer--ec2-admin_AmazonEC2FullAccess.id
}

output "aws_iam_group_policy_attachment_tfer--ec2-admin_AmazonEventBridgeSchedulerFullAccess_id" {
  value = aws_iam_group_policy_attachment.tfer--ec2-admin_AmazonEventBridgeSchedulerFullAccess.id
}

output "aws_iam_group_policy_attachment_tfer--ec2-admin_AmazonSSMFullAccess_id" {
  value = aws_iam_group_policy_attachment.tfer--ec2-admin_AmazonSSMFullAccess.id
}

output "aws_iam_group_policy_attachment_tfer--ec2-admin_CloudWatchFullAccessV2_id" {
  value = aws_iam_group_policy_attachment.tfer--ec2-admin_CloudWatchFullAccessV2.id
}

output "aws_iam_group_policy_attachment_tfer--ec2-admin_CloudWatchFullAccess_id" {
  value = aws_iam_group_policy_attachment.tfer--ec2-admin_CloudWatchFullAccess.id
}

output "aws_iam_group_policy_attachment_tfer--ec2-admin_IAMFullAccess_id" {
  value = aws_iam_group_policy_attachment.tfer--ec2-admin_IAMFullAccess.id
}

output "aws_iam_group_policy_attachment_tfer--s3-admin_AmazonS3FullAccess_id" {
  value = aws_iam_group_policy_attachment.tfer--s3-admin_AmazonS3FullAccess.id
}

output "aws_iam_group_tfer--ec2-admin_id" {
  value = aws_iam_group.tfer--ec2-admin.id
}

output "aws_iam_group_tfer--s3-admin_id" {
  value = aws_iam_group.tfer--s3-admin.id
}

output "aws_iam_instance_profile_tfer--airflow-ec2-profil_id" {
  value = aws_iam_instance_profile.tfer--airflow-ec2-profil.id
}

output "aws_iam_instance_profile_tfer--mlflow-ec2-profil2_id" {
  value = aws_iam_instance_profile.tfer--mlflow-ec2-profil2.id
}

output "aws_iam_instance_profile_tfer--mlflow-ec2-profil_id" {
  value = aws_iam_instance_profile.tfer--mlflow-ec2-profil.id
}

output "aws_iam_instance_profile_tfer--nappecast-ec2-profil_id" {
  value = aws_iam_instance_profile.tfer--nappecast-ec2-profil.id
}

output "aws_iam_role_policy_attachment_tfer--airflow-ec2-role_AmazonSSMManagedInstanceCore_id" {
  value = aws_iam_role_policy_attachment.tfer--airflow-ec2-role_AmazonSSMManagedInstanceCore.id
}

output "aws_iam_role_policy_attachment_tfer--airflow-ec2-role_CloudWatchAgentServerPolicy_id" {
  value = aws_iam_role_policy_attachment.tfer--airflow-ec2-role_CloudWatchAgentServerPolicy.id
}

output "aws_iam_role_policy_attachment_tfer--mlflow-ec2-role2_AmazonSSMManagedInstanceCore_id" {
  value = aws_iam_role_policy_attachment.tfer--mlflow-ec2-role2_AmazonSSMManagedInstanceCore.id
}

output "aws_iam_role_policy_attachment_tfer--nappecast-ec2-role_AmazonEC2ContainerRegistryReadOnly_id" {
  value = aws_iam_role_policy_attachment.tfer--nappecast-ec2-role_AmazonEC2ContainerRegistryReadOnly.id
}

output "aws_iam_role_policy_attachment_tfer--nappecast-ec2-role_AmazonS3FullAccess_id" {
  value = aws_iam_role_policy_attachment.tfer--nappecast-ec2-role_AmazonS3FullAccess.id
}

output "aws_iam_role_policy_attachment_tfer--nappecast-ec2-role_AmazonSSMManagedInstanceCore_id" {
  value = aws_iam_role_policy_attachment.tfer--nappecast-ec2-role_AmazonSSMManagedInstanceCore.id
}

output "aws_iam_role_policy_attachment_tfer--nappecast-trigger-lambda-role_AWSLambdaBasicExecutionRole_id" {
  value = aws_iam_role_policy_attachment.tfer--nappecast-trigger-lambda-role_AWSLambdaBasicExecutionRole.id
}

output "aws_iam_role_policy_attachment_tfer--nappecast-trigger-lambda-role_AWSLambdaVPCAccessExecutionRole_id" {
  value = aws_iam_role_policy_attachment.tfer--nappecast-trigger-lambda-role_AWSLambdaVPCAccessExecutionRole.id
}

output "aws_iam_role_policy_attachment_tfer--rds-monitoring-role_AmazonRDSEnhancedMonitoringRole_id" {
  value = aws_iam_role_policy_attachment.tfer--rds-monitoring-role_AmazonRDSEnhancedMonitoringRole.id
}

output "aws_iam_role_policy_tfer--airflow-ec2-role_GetSecretsManagerKey_id" {
  value = aws_iam_role_policy.tfer--airflow-ec2-role_GetSecretsManagerKey.id
}

output "aws_iam_role_policy_tfer--airflow-ec2-role_airflow-permissions_id" {
  value = aws_iam_role_policy.tfer--airflow-ec2-role_airflow-permissions.id
}

output "aws_iam_role_policy_tfer--github-actions-deploy_github-actions-ecr-airflow_id" {
  value = aws_iam_role_policy.tfer--github-actions-deploy_github-actions-ecr-airflow.id
}

output "aws_iam_role_policy_tfer--github-actions-deploy_github-actions-ecr-streamlit_id" {
  value = aws_iam_role_policy.tfer--github-actions-deploy_github-actions-ecr-streamlit.id
}

output "aws_iam_role_policy_tfer--github-actions-deploy_github-actions-ecr_id" {
  value = aws_iam_role_policy.tfer--github-actions-deploy_github-actions-ecr.id
}

output "aws_iam_role_policy_tfer--github-actions-deploy_sg-ssh_id" {
  value = aws_iam_role_policy.tfer--github-actions-deploy_sg-ssh.id
}

output "aws_iam_role_policy_tfer--mlflow-ec2-role2_GetSecretsManagerKey_id" {
  value = aws_iam_role_policy.tfer--mlflow-ec2-role2_GetSecretsManagerKey.id
}

output "aws_iam_role_policy_tfer--mlflow-ec2-role2_s3-mlflow-artifacts2_id" {
  value = aws_iam_role_policy.tfer--mlflow-ec2-role2_s3-mlflow-artifacts2.id
}

output "aws_iam_role_policy_tfer--nappecast-ec2-role_GetSecretsManagerKey_id" {
  value = aws_iam_role_policy.tfer--nappecast-ec2-role_GetSecretsManagerKey.id
}

output "aws_iam_role_policy_tfer--nappecast-scheduler-ec2-role_nappecast-start-stop-instances_id" {
  value = aws_iam_role_policy.tfer--nappecast-scheduler-ec2-role_nappecast-start-stop-instances.id
}

output "aws_iam_role_policy_tfer--nappecast-scheduler-invoke-trigger-role_nappecast-invoke-trigger-lambda_id" {
  value = aws_iam_role_policy.tfer--nappecast-scheduler-invoke-trigger-role_nappecast-invoke-trigger-lambda.id
}

output "aws_iam_role_policy_tfer--scheduler-stop-ec2-role_scheduler-stop-ec2-role_id" {
  value = aws_iam_role_policy.tfer--scheduler-stop-ec2-role_scheduler-stop-ec2-role.id
}

output "aws_iam_role_tfer--airflow-ec2-role_id" {
  value = aws_iam_role.tfer--airflow-ec2-role.id
}

output "aws_iam_role_tfer--github-actions-deploy_id" {
  value = aws_iam_role.tfer--github-actions-deploy.id
}

output "aws_iam_role_tfer--mlflow-ec2-role2_id" {
  value = aws_iam_role.tfer--mlflow-ec2-role2.id
}

output "aws_iam_role_tfer--mlflow-ec2-role_id" {
  value = aws_iam_role.tfer--mlflow-ec2-role.id
}

output "aws_iam_role_tfer--nappecast-ec2-role_id" {
  value = aws_iam_role.tfer--nappecast-ec2-role.id
}

output "aws_iam_role_tfer--nappecast-scheduler-ec2-role_id" {
  value = aws_iam_role.tfer--nappecast-scheduler-ec2-role.id
}

output "aws_iam_role_tfer--nappecast-scheduler-invoke-trigger-role_id" {
  value = aws_iam_role.tfer--nappecast-scheduler-invoke-trigger-role.id
}

output "aws_iam_role_tfer--nappecast-trigger-lambda-role_id" {
  value = aws_iam_role.tfer--nappecast-trigger-lambda-role.id
}

output "aws_iam_role_tfer--rds-monitoring-role_id" {
  value = aws_iam_role.tfer--rds-monitoring-role.id
}

output "aws_iam_role_tfer--scheduler-stop-ec2-role_id" {
  value = aws_iam_role.tfer--scheduler-stop-ec2-role.id
}

output "aws_iam_user_group_membership_tfer--nappecast-admin-002F-ec2-admin_id" {
  value = aws_iam_user_group_membership.tfer--nappecast-admin-002F-ec2-admin.id
}

output "aws_iam_user_group_membership_tfer--nappecast-admin-002F-s3-admin_id" {
  value = aws_iam_user_group_membership.tfer--nappecast-admin-002F-s3-admin.id
}

output "aws_iam_user_policy_attachment_tfer--readonly-002E-terraform_AmazonS3ReadOnlyAccess_id" {
  value = aws_iam_user_policy_attachment.tfer--readonly-002E-terraform_AmazonS3ReadOnlyAccess.id
}

output "aws_iam_user_policy_attachment_tfer--readonly-002E-terraform_ReadOnlyAccess_id" {
  value = aws_iam_user_policy_attachment.tfer--readonly-002E-terraform_ReadOnlyAccess.id
}

output "aws_iam_user_policy_tfer--nappecast-admin_nappecast-lambda-deploy_id" {
  value = aws_iam_user_policy.tfer--nappecast-admin_nappecast-lambda-deploy.id
}

output "aws_iam_user_tfer--AIDA4JCB4FK3DU562CFMH_id" {
  value = aws_iam_user.tfer--AIDA4JCB4FK3DU562CFMH.id
}

output "aws_iam_user_tfer--AIDA4JCB4FK3GW2SNP67A_id" {
  value = aws_iam_user.tfer--AIDA4JCB4FK3GW2SNP67A.id
}
