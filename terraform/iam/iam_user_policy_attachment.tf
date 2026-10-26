resource "aws_iam_user_policy_attachment" "tfer--readonly-002E-terraform_AmazonS3ReadOnlyAccess" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  user       = "readonly.terraform"
}

resource "aws_iam_user_policy_attachment" "tfer--readonly-002E-terraform_ReadOnlyAccess" {
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
  user       = "readonly.terraform"
}
