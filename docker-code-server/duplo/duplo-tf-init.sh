#!/usr/bin/with-contenv bash

#GOPATH=/config/go
#GOVERSION=1.15.6
#TERRAFORM_VERSION=0.14.3
######
mkdir -p $GOPATH/src/github.com/hashicorp/terraform
cd $GOPATH/src/github.com/hashicorp/terraform
git clone https://github.com/hashicorp/terraform.git ./ && \
    git checkout v${TERRAFORM_VERSION}
/bin/bash scripts/build.sh

##
mkdir -p $GOPATH/src/github.com/duplocloud/terraform-provider-duplocloud
cd $GOPATH/src/github.com/duplocloud/terraform-provider-duplocloud
#  git clone https://pravin-duplocloud:XXXXXX@github.com/duplocloud/terraform-provider-duplocloud.git ./
#  git checkout CrudApi
#  go mod vendor ; make build; make install
#  cd examples; terraform init; terraform plan