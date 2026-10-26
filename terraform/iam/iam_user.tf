resource "aws_iam_user" "tfer--AIDA4JCB4FK3DU562CFMH" {
  force_destroy = "false"
  name          = "readonly.terraform"
  path          = "/"
}

resource "aws_iam_user" "tfer--AIDA4JCB4FK3GW2SNP67A" {
  force_destroy = "false"
  name          = "nappecast-admin"
  path          = "/"
}
