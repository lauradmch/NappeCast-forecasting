variable "aws_region" {
  description = "Région AWS de la base de données"
  type        = string
  default     = "eu-west-3"
}

variable "rds_kms_key_id" {
  description = "Identifiant (UUID) de la clé KMS qui chiffre la base et Performance Insights"
  type        = string
}

variable "rds_monitoring_role_name" {
  description = "Nom du rôle IAM utilisé pour la supervision améliorée de RDS"
  type        = string
  default     = "rds-monitoring-role"
}

variable "rds_security_group_ids" {
  description = "Identifiants des groupes de sécurité associés à la base"
  type        = list(string)
}

variable "rds_username" {
  description = "Nom de l'administrateur de la base (le mot de passe n'est jamais stocké dans le code)"
  type        = string
}
