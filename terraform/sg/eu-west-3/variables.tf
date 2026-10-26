variable "admin_cidr" {
  description = "Adresse IP de l'administrateur autorisée en SSH, base de données, MLflow et Airflow, au format CIDR (ex. 203.0.113.10/32)"
  type        = string

  validation {
    condition     = can(cidrhost(var.admin_cidr, 0))
    error_message = "admin_cidr doit être un CIDR valide, par exemple 203.0.113.10/32."
  }
}

variable "team_cidr_blocks" {
  description = "Adresses IP de l'équipe autorisées à accéder au serveur MLflow (port 5000), au format CIDR"
  type        = list(string)

  validation {
    condition     = alltrue([for c in var.team_cidr_blocks : can(cidrhost(c, 0))])
    error_message = "Chaque élément de team_cidr_blocks doit être un CIDR valide."
  }
}
