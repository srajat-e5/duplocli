

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