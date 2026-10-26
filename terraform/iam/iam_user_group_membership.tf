resource "aws_iam_user_group_membership" "tfer--nappecast-admin-002F-ec2-admin" {
  groups = ["ec2-admin"]
  user   = "nappecast-admin"
}

resource "aws_iam_user_group_membership" "tfer--nappecast-admin-002F-s3-admin" {
  groups = ["s3-admin"]
  user   = "nappecast-admin"
}
