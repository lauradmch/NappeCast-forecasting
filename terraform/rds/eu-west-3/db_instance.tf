# Base PostgreSQL NappeCast (entrepôt de données : prédictions et logs).
data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  kms_key_arn         = "arn:aws:kms:${var.aws_region}:${local.account_id}:key/${var.rds_kms_key_id}"
  monitoring_role_arn = "arn:aws:iam::${local.account_id}:role/${var.rds_monitoring_role_name}"
}

resource "aws_db_instance" "tfer--nappecast" {
  allocated_storage                     = "20"
  auto_minor_version_upgrade            = "true"
  availability_zone                     = "eu-west-3c"
  backup_retention_period               = "1"
  backup_target                         = "region"
  backup_window                         = "13:58-14:28"
  ca_cert_identifier                    = "rds-ca-rsa2048-g1"
  copy_tags_to_snapshot                 = "true"
  customer_owned_ip_enabled             = "false"
  database_insights_mode                = "standard"
  db_subnet_group_name                  = aws_db_subnet_group.tfer--default-vpc-0400adbbc2bdd55be.name
  dedicated_log_volume                  = "false"
  deletion_protection                   = "false"
  engine                                = "postgres"
  engine_lifecycle_support              = "open-source-rds-extended-support-disabled"
  engine_version                        = "18.3"
  iam_database_authentication_enabled   = "false"
  identifier                            = "nappecast"
  instance_class                        = "db.t4g.micro"
  iops                                  = "0"
  kms_key_id                            = local.kms_key_arn
  license_model                         = "postgresql-license"
  maintenance_window                    = "sun:04:51-sun:05:21"
  max_allocated_storage                 = "1000"
  monitoring_interval                   = "60"
  monitoring_role_arn                   = local.monitoring_role_arn
  multi_az                              = "false"
  network_type                          = "IPV4"
  option_group_name                     = "default:postgres-18"
  parameter_group_name                  = "default.postgres18"
  performance_insights_enabled          = "true"
  performance_insights_kms_key_id       = local.kms_key_arn
  performance_insights_retention_period = "7"
  port                                  = "5432"
  publicly_accessible                   = "true"
  storage_encrypted                     = "true"
  storage_throughput                    = "0"
  storage_type                          = "gp2"
  username                              = var.rds_username
  vpc_security_group_ids                = var.rds_security_group_ids
}
