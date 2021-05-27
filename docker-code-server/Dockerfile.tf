FROM duplocloud/code-server:sso_tf_v5
###############################
##
ENV DEBIAN_FRONTEND=noninteractive
ENV GOVERSION=1.15.6
ENV TERRAFORM_VERSION=0.14.11
##
ENV TF_DEV=true
ENV TF_RELEASE=true
#
ENV GOROOT=/usr/local/go
ENV GOPATH=/config/go
ENV GOBIN="$HOME/go/bin"
#
RUN mkdir -p $GOBIN
RUN mkdir -p $GOPATH
RUN mkdir -p $GOPATH/bin
RUN mkdir -p $GOPATH/src
ENV PATH=$PATH:$GOROOT/bin:$GOBIN:$GOPATH:$GOPATH/bin:$GOPATH/src
#
RUN apt-get update && apt-get -y install make wget unzip curl jq ca-certificates openssl  vim bash git


#RUN apt-get update && apt-get upgrade -y && apt-get clean
#RUN apt-get install -y python-pip
RUN rm /usr/local/bin/terraform
RUN apt-get update \
  && cd /tmp \
  && wget "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip" \
  && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/local/bin


RUN cd /usr/local && wget https://storage.googleapis.com/golang/go${GOVERSION}.linux-amd64.tar.gz &&  tar zxf go${GOVERSION}.linux-amd64.tar.gz && rm go${GOVERSION}.linux-amd64.tar.gz

RUN mkdir -p $GOPATH/src/github.com/hashicorp/terraform
RUN mkdir -p $GOPATH/src/github.com/duplocloud/terraform-provider-duplocloud
#
RUN go version
RUN terraform version
###############################

######

COPY duplo/99-duplo-code-server-init /etc/cont-init.d/
COPY duplo/duplo-tf-init.sh /root/
RUN chmod 777 /root/*.sh
#######

##
RUN cd /tmp && wget https://storage.googleapis.com/kubernetes-release/release/v1.20.0/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl
##
