

## azure
### every infrastructure == resource group
* 1 -  duploinfra-INFRA_NAME ( VNET, VNET-SUBNETs, StorasgeAccount, key-vault, for everysubnet - NSG (security groups), NSG rules ) AxzureNfrastucureManager
* 2 -  duplobackup-INFRA_NAME ( backup/images/snapshots) - its empty ( its grows as we go)

### every tenant == resource group
* 1- duploservices-TENANT_NAME -( ManagedIdentity, App Sec Grp, List of VM , Each VM = 1 VM + nic + OS disk, n data disk, optional Public IP)

```
terraform providers schema -json
```
 
 
 ```hcl

resource "local_file" "duplotf" {
  content  = "${data.template_file.duplotf.rendered}"
  filename = "tmp/duplotf"
}

data "template_file" "duplotf" {
  template = "${file("template/duplotf.tpl")}"
  ...
}

resource "null_resource" "update_config_map_aws_auth" {
  provisioner "local-exec" {
    command = "kubectl apply -f tmp/config-map-aws-auth_${var.cluster-name}.yaml --kubeconfig ${local_file.duplotf.filename}"
  }
}



```

```hcl
  
data "local_file" "example" {

filename = "${path.module}/file.json"

}

locals {

example_var = "${data.local_file.example.content["dictionary_name"]}"

}


data "external" "example" {

program = ["cat", "${path.module}/file.json"]

query = { }

}

Then you can reference the map in terraform like this:

locals {

example_var = "${data.example.result["dictionary_name"]}"

}



resource "template_dir" "config" {
    source_dir      = "./unrendered"
    destination_dir = "./rendered"

    vars = {
        message = "world"
    }
}
```

```hcl

  bucket = sha1(format("my_super_secret_key:%s", var.client.name))


user-data.sh.tpl
#!/bin/bash
DOMAIN = "${domain}"
PORT = "8080"
instance.tf
variable "environment" {}

variable "environment_domains" {
  default = {
    "dev"  = "testing.dev.xxxx.com"
    "qa"   = "testing.prod.xxxx.com"
    "prod" = "testing.qa.xxxx.com"
  }
}

data "template_file" "user_data" {
  template = "${file("${path.module}/user-data.sh.tpl")}"

  vars {
    domain = "${lookup(var.environment_domains, var.environment)}"
  }
}


resource "aws_instance" "server" {
  ...
  user_data = "${template_file.user_data.rendered}"
  ...
}
```


```hcl
data "template_file" "user_data" {
  template = "${file("${path.module}/user-data-${var.env}.sh")}"
  ...
}

resource "aws_instance" "server" {
  user_data = "${template_file.user_data.rendered}"
  ...
}

```

```hcl
data "template_file" "user_data" {
  template = "${file("${path.module}/user-data-${var.env}.sh")}"
  ...
}

resource "aws_instance" "server" {
  user_data = "${template_file.user_data.rendered}"
  ...
}

```

```hcl
json_variables.tfvars.json
 {
	"KEY_A": "VALUE_A",
	"KEY_B": "VALUE_B",
	...
	"KEY_C": [{
		"KEY_D": "VALUE_D",
		...
		"KEY_E": [{
			"KEY_F": "VALUE_F",
			...
		}]
		...
	}]
}
 
terraform apply -var-file="json_variables.tfvars.json"
in    main.tf 
VALUE_F ==>
${var.KEY_C[0].KEY_E[0].KEY_F}
```


```hcl

data "template_file" "prometheus2_role_default_attributes" {
  template = file(format("attributes/prometheus.tpl")

  vars = {
    prometheus_url    = var.prometheus_url
    postgres_exporter = "${lower(var.env_type)}-hostname.com"
    pe_kube_exporter  = "${lower(var.env_type)}-hostname.com"
    environment       = lower(var.env_type)
    region            = lower(var.region)
    service_provider  = lower(var.service_provider)
  }
}
 
# prometheus.tpl  reference vars={}   
{
    {
      "replacement": "${service_provider}",
      "target_label": "provider"
    },
    {
      "replacement": "${region}",
      "target_label": "region"
    }
}
resource "chef_role" "prometheus2_server" {
  name = "${lower(var.env_type)}-${lower(var.application)}-${var.component}"

  run_list = [
      ...
  ]

  override_attributes_json = data.template_file.prometheus2_role_default_attributes.rendered
}
```

```hcl

resource "aws_instance" "server" {
  count = 4 # create four similar EC2 instances

  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"

  tags = {
    Name = "Server ${count.index}"
  }
}

variable "subnet_ids" {
  type = list(string)
}

resource "aws_instance" "server" {
  # Create one instance for each subnet
  count = length(var.subnet_ids)

  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"
  subnet_id     = var.subnet_ids[count.index]

  tags = {
    Name = "Server ${count.index}"
  }
}

```


```hcl

## resource block cannot use both count and for_eachTerraform 0.12.6. 
#Map: 
resource "azurerm_resource_group" "rg" {
  for_each = {
    a_group = "eastus"
    another_group = "westus2"
  }
  name     = each.key
  location = each.value
}
#Set: 
resource "aws_iam_user" "the-accounts" {
  for_each = toset( ["Todd", "James", "Alice", "Dottie"] )
  name     = each.key
}

#toset
locals {
  subnet_ids = toset([
    "subnet-abcdef",
    "subnet-012345",
  ])
}

resource "aws_instance" "server" {
  for_each = local.subnet_ids

  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"
  subnet_id     = each.key # note: each.key and each.value are the same for a set

  tags = {
    Name = "Server ${each.key}"
  }
}


###
variable "subnet_ids" {
  type = set(string)
}

resource "aws_instance" "server" {
  for_each = var.subnet_ids

  # (and the other arguments as above)
}
 
```


```hcl


resource "azurerm_resource_group" "example" {
  # ...

  lifecycle {
    create_before_destroy = true #ignore_changes
  }
}

resource "aws_instance" "example" {
  # ...

  lifecycle {
    ignore_changes = [
      # Ignore changes to tags, e.g. because a management agent
      # updates these based on some ruleset managed elsewhere.
      tags,
    ]
  }
}

```