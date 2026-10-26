# Infrastructure NappeCast (Terraform)

Description en code de l'infrastructure AWS de **NappeCast** (prévision du niveau des nappes phréatiques), région `eu-west-3` (Paris).

> **Nature de ce code.** Il a été produit par export de l'infrastructure **déjà en production** (Terraformer), puis nettoyé : il sert de **documentation exécutable et de plan d'infrastructure**, pas d'outil de déploiement.
> **Ne lancez jamais `terraform apply` sur ce code sans avoir relu le `plan`** : une différence avec l'existant pourrait modifier ou recréer des ressources (base de données comprise).

**Périmètre : Bloc 3 (pipelines de données).** Ce dépôt décrit l'infrastructure qui porte les flux de données. L'entraînement des modèles, le déploiement continu (GitHub Actions, ECR) et le monitoring des modèles relèvent du **Bloc 4**.

## Ce que décrit chaque dossier

| Dossier | Service AWS | Rôle dans NappeCast |
|---|---|---|
| `ec2_instance/` | EC2 (3 instances) | `app-server` (API FastAPI + Streamlit), `mlflow-server` (suivi des expériences), `airflow-orchestrator` (collecte et prédiction quotidienne) |
| `rds/` | RDS PostgreSQL | Entrepôt de données : prédictions et journaux |
| `s3/` | S3 | Lac de données (`raw` / `interim` / `processed`) et artefacts MLflow, bucket `nappecast` |
| `sg/` | Groupes de sécurité | Règles réseau entre les composants et accès d'administration |
| `iam/` | IAM | Rôles, politiques et profils d'instance (accès aux secrets, à S3, au démarrage et à l'arrêt planifiés) |
| `eip/` | Adresses IP élastiques | IP fixes des instances |

Chaque dossier est un **module Terraform indépendant** : les commandes se lancent dans le dossier concerné (`terraform/<service>/eu-west-3/`, ou `terraform/iam/`).

```
terraform/
├── ec2_instance/eu-west-3/   instance.tf, scripts/ (démarrage des instances)
├── eip/eu-west-3/
├── iam/
├── rds/eu-west-3/            terraform.tfvars.example
├── s3/eu-west-3/
└── sg/eu-west-3/             terraform.tfvars.example
```

## Prérequis

- Terraform, et le fournisseur AWS en version `~> 5.100.0` (installé par `terraform init`)
- AWS CLI avec un profil **en lecture seule** (ex. `readonly-terraform`) pour `plan`

## Variables et secrets

- Les valeurs propres à un compte (clé de chiffrement KMS, groupes de sécurité, adresses IP autorisées, nom d'administrateur de la base) sont des **variables**.
- Copier `terraform.tfvars.example` en `terraform.tfvars` et renseigner les vraies valeurs. Le fichier `terraform.tfvars` est **ignoré par Git**.
- Le numéro de compte AWS est lu automatiquement (`aws_caller_identity`) et n'est écrit nulle part.
- Le **mot de passe de la base n'est pas dans le code**.

## Vérifier le code (sans rien modifier sur AWS)

```bash
cd terraform/rds/eu-west-3        # ou un autre dossier
terraform init
terraform fmt -check
terraform validate
AWS_PROFILE=readonly-terraform terraform plan
```

Le `plan` d'une infrastructure déjà existante doit afficher « No changes » une fois l'état importé. En cas de modification ou de suppression proposée, ne pas appliquer.

L'état Terraform (`*.tfstate`) n'est **jamais versionné** : il peut contenir des valeurs sensibles.

## Sécurité et conformité

- Aucun secret, clé d'accès ni fichier d'état dans le dépôt (`.gitignore` : `*.tfstate`, `*.tfvars`, `.terraform/`, `*.pem`).
- Chiffrement : stockage RDS chiffré par une clé KMS.
- Les adresses IP d'administration sont des variables, jamais écrites dans le code.
- **Conformité RGPD** : les données traitées (niveaux de nappes Hub'eau, météo Open-Meteo) sont **publiques et libres** ; elles ne contiennent aucune donnée personnelle.

## Limites connues

- **Export de l'existant** : les noms de ressources gardent le préfixe `tfer--` hérité de l'outil d'export.
- **Ressources d'autres projets du même compte AWS** encore présentes dans certains fichiers (ex. buckets S3 et rôles IAM non liés à NappeCast) ; seules celles de NappeCast sont décrites dans le tableau ci-dessus.
- **Dossier `lambda/`** : ne contient que la configuration du fournisseur (déclencheur de l'ancienne architecture).
- **Non décrits ici** : le VPC par défaut, Secrets Manager, EventBridge et CloudWatch.
- **État local uniquement** : une évolution naturelle serait un état distant (S3 chiffré avec verrouillage).