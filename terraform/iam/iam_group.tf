resource "aws_iam_group" "tfer--ec2-admin" {
  name = "ec2-admin"
  path = "/"
}

resource "aws_iam_group" "tfer--eks-admin" {
  name = "eks-admin"
  path = "/"
}

resource "aws_iam_group" "tfer--s3-admin" {
  name = "s3-admin"
  path = "/"
}
