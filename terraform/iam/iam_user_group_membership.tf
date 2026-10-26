resource "aws_iam_user_group_membership" "tfer--admin-002E-eks-002F-ec2-admin" {
  groups = ["ec2-admin"]
  user   = "admin.eks"
}

resource "aws_iam_user_group_membership" "tfer--admin-002E-eks-002F-eks-admin" {
  groups = ["eks-admin"]
  user   = "admin.eks"
}

resource "aws_iam_user_group_membership" "tfer--nappecast-admin-002F-ec2-admin" {
  groups = ["ec2-admin"]
  user   = "nappecast-admin"
}

resource "aws_iam_user_group_membership" "tfer--nappecast-admin-002F-s3-admin" {
  groups = ["s3-admin"]
  user   = "nappecast-admin"
}
