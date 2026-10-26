resource "aws_instance" "tfer--i-017d82908629e09cd_app-server" {
  ami                         = "ami-0856571822cc2a7d9"
  associate_public_ip_address = "true"
  availability_zone           = "eu-west-3c"

  capacity_reservation_specification {
    capacity_reservation_preference = "open"
  }

  cpu_core_count = "2"

  cpu_options {
    core_count       = "2"
    threads_per_core = "2"
  }

  cpu_threads_per_core    = "2"
  disable_api_stop        = "false"
  disable_api_termination = "false"
  ebs_optimized           = "true"

  enclave_options {
    enabled = "false"
  }

  get_password_data                    = "false"
  hibernation                          = "false"
  iam_instance_profile                 = "nappecast-ec2-profil"
  instance_initiated_shutdown_behavior = "stop"
  instance_type                        = "c5.xlarge"
  ipv6_address_count                   = "0"
  key_name                             = "nappecast-ec2-key"

  maintenance_options {
    auto_recovery = "default"
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_protocol_ipv6          = "disabled"
    http_put_response_hop_limit = "2"
    http_tokens                 = "required"
    instance_metadata_tags      = "disabled"
  }

  monitoring                 = "true"
  placement_partition_number = "0"

  private_dns_name_options {
    enable_resource_name_dns_a_record    = "false"
    enable_resource_name_dns_aaaa_record = "false"
    hostname_type                        = "ip-name"
  }

  private_ip = "172.31.41.22"

  root_block_device {
    delete_on_termination = "true"
    encrypted             = "false"
    iops                  = "3000"
    throughput            = "125"
    volume_size           = "25"
    volume_type           = "gp3"
  }

  security_groups   = ["nappecast-ec2-group"]
  source_dest_check = "true"
  subnet_id         = "subnet-0fe2ca3e8e7ea7656"

  tags = {
    Name = "app-server"
  }

  tags_all = {
    Name = "app-server"
  }

  tenancy                = "default"
  user_data_base64       = filebase64("${path.module}/scripts/app_server_user_data.sh")
  vpc_security_group_ids = ["sg-068b0a101c18effad"]
}

resource "aws_instance" "tfer--i-06b315e78fa277e77_mlflow-server-sqlite" {
  ami                         = "ami-0b9edcf0ef9b29fdd"
  associate_public_ip_address = "true"
  availability_zone           = "eu-west-3c"

  capacity_reservation_specification {
    capacity_reservation_preference = "open"
  }

  cpu_core_count = "1"

  cpu_options {
    core_count       = "1"
    threads_per_core = "2"
  }

  cpu_threads_per_core = "2"

  credit_specification {
    cpu_credits = "unlimited"
  }

  disable_api_stop        = "false"
  disable_api_termination = "false"
  ebs_optimized           = "false"

  enclave_options {
    enabled = "false"
  }

  get_password_data                    = "false"
  hibernation                          = "false"
  iam_instance_profile                 = "mlflow-ec2-profil2"
  instance_initiated_shutdown_behavior = "stop"
  instance_type                        = "t3.small"
  ipv6_address_count                   = "0"
  key_name                             = "nappecast-ec2-key"

  maintenance_options {
    auto_recovery = "default"
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_protocol_ipv6          = "disabled"
    http_put_response_hop_limit = "2"
    http_tokens                 = "required"
    instance_metadata_tags      = "disabled"
  }

  monitoring                 = "false"
  placement_partition_number = "0"

  private_dns_name_options {
    enable_resource_name_dns_a_record    = "false"
    enable_resource_name_dns_aaaa_record = "false"
    hostname_type                        = "ip-name"
  }

  private_ip = "172.31.32.79"

  root_block_device {
    delete_on_termination = "true"
    encrypted             = "false"
    iops                  = "3000"
    throughput            = "125"
    volume_size           = "8"
    volume_type           = "gp3"
  }

  security_groups   = ["mlflow-ec2-sg-v2"]
  source_dest_check = "true"
  subnet_id         = "subnet-0fe2ca3e8e7ea7656"

  tags = {
    Name = "mlflow-server-sqlite"
  }

  tags_all = {
    Name = "mlflow-server-sqlite"
  }

  tenancy                = "default"
  user_data_base64       = filebase64("${path.module}/scripts/mlflow_server_user_data.sh")
  vpc_security_group_ids = ["sg-06cdd4979e8928cf2"]
}

resource "aws_instance" "tfer--i-0c770608e3877ec43_airflow-orchestrator" {
  ami                         = "ami-083b1d187054aff9b"
  associate_public_ip_address = "true"
  availability_zone           = "eu-west-3a"

  capacity_reservation_specification {
    capacity_reservation_preference = "open"
  }

  cpu_core_count = "2"

  cpu_options {
    core_count       = "2"
    threads_per_core = "2"
  }

  cpu_threads_per_core    = "2"
  disable_api_stop        = "false"
  disable_api_termination = "false"
  ebs_optimized           = "true"

  enclave_options {
    enabled = "false"
  }

  get_password_data                    = "false"
  hibernation                          = "false"
  iam_instance_profile                 = "airflow-ec2-profil"
  instance_initiated_shutdown_behavior = "stop"
  instance_type                        = "c5.xlarge"
  ipv6_address_count                   = "0"
  key_name                             = "nappecast-ec2-key"

  maintenance_options {
    auto_recovery = "default"
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_protocol_ipv6          = "disabled"
    http_put_response_hop_limit = "2"
    http_tokens                 = "required"
    instance_metadata_tags      = "disabled"
  }

  monitoring                 = "false"
  placement_partition_number = "0"

  private_dns_name_options {
    enable_resource_name_dns_a_record    = "false"
    enable_resource_name_dns_aaaa_record = "false"
    hostname_type                        = "ip-name"
  }

  private_ip = "172.31.8.14"

  root_block_device {
    delete_on_termination = "true"
    encrypted             = "false"
    iops                  = "3000"
    throughput            = "125"
    volume_size           = "25"
    volume_type           = "gp3"
  }

  security_groups   = ["airflow-ec2-sg"]
  source_dest_check = "true"
  subnet_id         = "subnet-05768b262e9a18cf4"

  tags = {
    Name = "airflow-orchestrator"
  }

  tags_all = {
    Name = "airflow-orchestrator"
  }

  tenancy                = "default"
  user_data_base64       = filebase64("${path.module}/scripts/airflow_orchestrator_user_data.sh")
  vpc_security_group_ids = ["sg-0d34dad32a2811316"]
}
