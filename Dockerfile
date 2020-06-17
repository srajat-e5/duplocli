FROM ubuntu:18.04


ENV DEBIAN_FRONTEND=noninteractive
#Terraform v0.12.24
ENV TERRAFORM_VERSION=0.12.24

RUN apt-get update
RUN apt-get install -y awscli

RUN apt-get update \
  && apt-get install -y wget unzip curl jq bash ca-certificates git openssl unzip wget \
  && cd /tmp \
  && wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
  && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/bin \
  && rm -rf /tmp/* \
  && rm -rf /var/lib/apt/lists/* \
  rm -rf /var/tmp/*
RUN set -xe \
    && apt-get update \
    && apt-get install -y python-pip
RUN pip install --upgrade pip
#

mkdir -p /duplocli
copy . /duplocli/

WORKDIR /duplocli
RUN pip install -r ./duplocli/terrform/requirements.txt


#
ADD startup.sh /
RUN chmod 777 /*.sh

CMD ["/duplocli/startup.sh"]
