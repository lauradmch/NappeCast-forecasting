resource "aws_db_snapshot" "tfer--brewly-db-snapshot" {
  db_instance_identifier = "brewly-db"
  db_snapshot_identifier = "brewly-db-snapshot"
}

resource "aws_db_snapshot" "tfer--brewly-snapshot" {
  db_instance_identifier = "brewly"
  db_snapshot_identifier = "brewly-snapshot"
}

resource "aws_db_snapshot" "tfer--coatching-aifs-mlflow-snapshot" {
  db_instance_identifier = "coatching-aifs-mlflow"
  db_snapshot_identifier = "coatching-aifs-mlflow-snapshot"
}

resource "aws_db_snapshot" "tfer--rds-003A-nappecast-2026-10-24-14-02" {
  db_instance_identifier = "nappecast"
  db_snapshot_identifier = "rds:nappecast-2026-10-24-14-02"
}

resource "aws_db_snapshot" "tfer--rds-003A-nappecast-2026-10-25-14-02" {
  db_instance_identifier = "nappecast"
  db_snapshot_identifier = "rds:nappecast-2026-10-25-14-02"
}

resource "aws_db_snapshot" "tfer--rds-003A-nappecast-2026-10-26-14-02" {
  db_instance_identifier = "nappecast"
  db_snapshot_identifier = "rds:nappecast-2026-10-26-14-02"
}

resource "aws_db_snapshot" "tfer--rgflow-snapshot" {
  db_instance_identifier = "rgflow"
  db_snapshot_identifier = "rgflow-snapshot"
}
