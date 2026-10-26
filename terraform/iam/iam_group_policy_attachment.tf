resource "aws_iam_group_policy_attachment" "tfer--ec2-admin_AmazonEC2ContainerRegistryFullAccess" {
  group      = "ec2-admin"
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
}

resource "aws_iam_group_policy_attachment" "tfer--ec2-admin_AmazonEC2FullAccess" {
  group      = "ec2-admin"
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_iam_group_policy_attachment" "tfer--ec2-admin_AmazonEventBridgeSchedulerFullAccess" {
  group      = "ec2-admin"
  policy_arn = "arn:aws:iam::aws:policy/AmazonEventBridgeSchedulerFullAccess"
}

resource "aws_iam_group_policy_attachment" "tfer--ec2-admin_AmazonSSMFullAccess" {
  group      = "ec2-admin"
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMFullAccess"
}

resource "aws_iam_group_policy_attachment" "tfer--ec2-admin_CloudWatchFullAccess" {
  group      = "ec2-admin"
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccess"
}

resource "aws_iam_group_policy_attachment" "tfer--ec2-admin_CloudWatchFullAccessV2" {
  group      = "ec2-admin"
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchFullAccessV2"
}

resource "aws_iam_group_policy_attachment" "tfer--ec2-admin_IAMFullAccess" {
  group      = "ec2-admin"
  policy_arn = "arn:aws:iam::aws:policy/IAMFullAccess"
}

resource "aws_iam_group_policy_attachment" "tfer--eks-admin_AdministratorAccess" {
  group      = "eks-admin"
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_group_policy_attachment" "tfer--eks-admin_AmazonEKSClusterPolicy" {
  group      = "eks-admin"
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_iam_group_policy_attachment" "tfer--eks-admin_AmazonEKSServicePolicy" {
  group      = "eks-admin"
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSServicePolicy"
}

resource "aws_iam_group_policy_attachment" "tfer--s3-admin_AmazonS3FullAccess" {
  group      = "s3-admin"
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}
