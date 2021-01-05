FROM duplocloud/code-server:sso_v16


###############################
##
ENV GOVERSION=1.15.6
ENV TERRAFORM_VERSION=0.14.3
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
RUN apt-get update && apt-get -y install make wget unzip curl jq ca-certificates openssl
RUN cd /usr/local && wget https://storage.googleapis.com/golang/go${GOVERSION}.linux-amd64.tar.gz &&  tar zxf go${GOVERSION}.linux-amd64.tar.gz && rm go${GOVERSION}.linux-amd64.tar.gz
RUN cd /tmp && wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip  && unzip terraform_${TERRAFORM_VERSION}_linux_amd64.zip -d /usr/local/bin && rm terraform_${TERRAFORM_VERSION}_linux_amd64.zip
#
RUN mkdir -p $GOPATH/src/github.com/hashicorp/terraform
RUN mkdir -p $GOPATH/src/github.com/duplocloud/terraform-provider-duplocloud
#
RUN go version
RUN terraform version
###############################

######

COPY duplo/duplo/99-duplo-code-server-init /etc/cont-init.d/
COPY duplo/duplo-tf-init.sh /root/
RUN chmod 777 /root/*.sh
#######