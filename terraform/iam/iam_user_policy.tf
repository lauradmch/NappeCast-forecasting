resource "aws_iam_user_policy" "tfer--nappecast-admin_nappecast-lambda-deploy" {
  name = "nappecast-lambda-deploy"

  policy = <<POLICY
{
  "Statement": [
    {
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration",
        "lambda:GetFunction",
        "lambda:InvokeFunction",
        "lambda:DeleteFunction",
        "lambda:TagResource"
      ],
      "Effect": "Allow",
      "Resource": "arn:aws:lambda:eu-west-3:844099234486:function:nappecast-*"
    },
    {
      "Action": "iam:PassRole",
      "Effect": "Allow",
      "Resource": [
        "arn:aws:iam::844099234486:role/nappecast-trigger-lambda-role",
        "arn:aws:iam::844099234486:role/nappecast-scheduler-invoke-trigger-role"
      ]
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  user = "nappecast-admin"
}
