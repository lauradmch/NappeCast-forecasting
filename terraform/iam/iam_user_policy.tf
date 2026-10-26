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
      "Resource": "arn:aws:lambda:eu-west-3:${data.aws_caller_identity.current.account_id}:function:nappecast-*"
    },
    {
      "Action": "iam:PassRole",
      "Effect": "Allow",
      "Resource": [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/nappecast-trigger-lambda-role",
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/nappecast-scheduler-invoke-trigger-role"
      ]
    }
  ],
  "Version": "2012-10-17"
}
POLICY

  user = "nappecast-admin"
}
