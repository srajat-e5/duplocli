FROM duplocloud/shell:2.15

ENV DEBIAN_FRONTEND=noninteractive
#Terraform v0.12.24
ENV TERRAFORM_VERSION=0.12.24

RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get upgrade -y && apt-get clean

RUN apt-get install -y python-pip
RUN pip install awscli

RUN apt-get update \
  && apt-get install -y wget vim unzip curl jq bash ca-certificates git openssl unzip wget \
  && cd /tmp \
  && wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
  && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/bin

RUN mkdir -p /duplocli
COPY . /duplocli/

WORKDIR /duplocli
RUN ls -altR .
RUN python3 -V
RUN python -V

# RUN pip3 install -r /duplocli/duplocli/terraform/requirements.txt
RUN pip install boto3
RUN pip install requests
RUN pip install psutil

RUN rm -rf /tmp/* \
  && rm -rf /var/lib/apt/lists/* \
  rm -rf /var/tmp/*

ADD startup.sh /
RUN chmod 777 /duplocli/*.sh

ENV PYTHONPATH=/duplocli

ENTRYPOINT [ "supervisord", "-n" ]
