resource "aws_s3_bucket" "tfer--nappecast" {
  bucket        = "nappecast"
  force_destroy = "false"

  grant {
    id          = "0e7598aec0c8752eb83377fa90b43e632bc9b170240e7ddd4de889b4515d10a5"
    permissions = ["FULL_CONTROL"]
    type        = "CanonicalUser"
  }

  object_lock_enabled = "false"
  request_payer       = "BucketOwner"

  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }

      bucket_key_enabled = "true"
    }
  }

  versioning {
    enabled    = "false"
    mfa_delete = "false"
  }
}
