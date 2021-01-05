### build terraform ###

```shell script
docker build -f Dockerfile.tf  -t  duplocloud/code-server:sso_tf_v3 . ; docker push  duplocloud/code-server:sso_tf_v3
```


```shell script
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


#  git clone https://xxx-duplocloud:XXXXXX@github.com/duplocloud/terraform-provider-duplocloud.git ./
#  git checkout CrudApi
#  go mod vendor
#  make build
#  make install
#  go mod vendor ; make build; make install
```