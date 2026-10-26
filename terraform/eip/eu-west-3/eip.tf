resource "aws_eip" "tfer--eipalloc-00009430ae95c65e5" {
  domain               = "vpc"
  instance             = "i-06b315e78fa277e77"
  network_border_group = "eu-west-3"
  network_interface    = "eni-03bba1ef9c047bb60"
  public_ipv4_pool     = "amazon"
}

resource "aws_eip" "tfer--eipalloc-06537520ff14343d3" {
  domain               = "vpc"
  network_border_group = "eu-west-3"
  public_ipv4_pool     = "amazon"
}

resource "aws_eip" "tfer--eipalloc-0a89fbe71082fee87" {
  domain               = "vpc"
  network_border_group = "eu-west-3"
  network_interface    = "eni-0961b7e2837d425a1"
  public_ipv4_pool     = "amazon"
}

resource "aws_eip" "tfer--eipalloc-0b632f3363c5e673c" {
  domain               = "vpc"
  instance             = "i-0c770608e3877ec43"
  network_border_group = "eu-west-3"
  network_interface    = "eni-0546ed01b7d962f90"
  public_ipv4_pool     = "amazon"
}

resource "aws_eip" "tfer--eipalloc-0d4f05dddbcc71a2a" {
  domain               = "vpc"
  instance             = "i-017d82908629e09cd"
  network_border_group = "eu-west-3"
  network_interface    = "eni-0778822f9760a86d5"
  public_ipv4_pool     = "amazon"
}
