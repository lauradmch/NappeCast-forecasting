data "terraform_remote_state" "sg" {
  backend = "local"

  config = {
    path = "../../../../generated/aws/sg/eu-west-3/terraform.tfstate"
  }
}
