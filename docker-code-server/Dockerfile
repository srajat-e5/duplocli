FROM lsiobase/ubuntu:bionic

#### build terrafrom ###
## docker build -f Dockerfile.tf  -t  duplocloud/code-server:sso_tf_v4 . ; docker push  duplocloud/code-server:sso_tf_v4

# set version label
ARG BUILD_DATE
ARG VERSION
ARG CODE_RELEASE=3.4.1
LABEL build_version="Linuxserver.io version:- ${VERSION} Build-date:- ${BUILD_DATE}"
LABEL maintainer="aptalca"
#DUPLO_CHANGE: changed to fix error at  CODE_VERSION=$(echo "$CODE_RELEASE" | awk '{print substr($1,3); }') && \
ENV CODE_VERSION=$CODE_RELEASE
# environment settings
ENV HOME="/config"

RUN \
 echo "**** install node repo ****" && \
 apt-get update && \
 apt-get install -y \
	gnupg && \
 curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add - && \
 echo 'deb https://deb.nodesource.com/node_12.x bionic main' \
	> /etc/apt/sources.list.d/nodesource.list && \
 curl -s https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
 echo 'deb https://dl.yarnpkg.com/debian/ stable main' \
	> /etc/apt/sources.list.d/yarn.list && \
 echo "**** install build dependencies ****" && \
 apt-get update && \
 apt-get install -y \
	build-essential \
	libx11-dev \
	libxkbfile-dev \
	libsecret-1-dev \
	pkg-config && \
 echo "**** install runtime dependencies ****" && \
 apt-get install -y \
	git \
	jq \
	nano \
	net-tools \
	nodejs \
	sudo \
	yarn && \
 echo "**** install code-server ****" && \
 if [ -z ${CODE_RELEASE+x} ]; then \
	CODE_RELEASE=$(curl -sX GET "https://api.github.com/repos/cdr/code-server/releases/latest" \
	| awk '/tag_name/{print $4;exit}' FS='[""]'); \
 fi && \
 #DUPLO_CHANGE:  CODE_VERSION=$(echo "$CODE_RELEASE" | awk '{print substr($1,3); }') && \
 yarn --production global add code-server@"$CODE_VERSION" && \
 yarn cache clean && \
 ln -s /node_modules/.bin/code-server /usr/bin/code-server && \
 echo "**** clean up ****" && \
 apt-get purge --auto-remove -y \
	build-essential \
	libx11-dev \
	libxkbfile-dev \
	libsecret-1-dev \
	pkg-config && \
 apt-get clean

#DUPLO_CHANGE: jeeva
RUN apt-get update
RUN apt-get install --yes --no-install-recommends software-properties-common
RUN apt-get install --yes --no-install-recommends curl awscli iputils-ping
RUN apt-get install --yes --no-install-recommends wget
RUN apt-get install --yes --no-install-recommends build-essential python2.7 python2.7-dev python-pip python-setuptools
RUN apt-get install --yes --no-install-recommends libmysqlclient-dev
RUN apt-get install --yes --no-install-recommends --fix-missing libffi-dev
RUN apt-get install --yes --no-install-recommends libssl-dev
RUN apt-get install --yes --no-install-recommends libxml2-dev libxslt1-dev
RUN apt-get install --yes --no-install-recommends --fix-missing mysql-client
RUN apt-get install --yes libmysqlclient-dev
RUN apt-get install -y apt-transport-https  ca-certificates curl gnupg-agent software-properties-common
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
RUN add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu  $(lsb_release -cs) \ stable"
RUN apt-get update
RUN apt-get install -y docker-ce docker-ce-cli containerd.io
RUN pip install setuptools awscli

#### zappa ####
ENV LOCAL_PATH=/config/.local/bin
ENV PATH=$LOCAL_PATH:$PATH
# RUN usermod -s /bin/bash abc
RUN apt-get update
RUN apt-get install -y curl vim python3.7 python3.7-dev python3.7-distutils python3-venv  python3-pip
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.7 1
RUN update-alternatives --set python /usr/bin/python3.7
RUN curl -s https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py --force-reinstall && \
    rm get-pip.py
RUN apt install -y virtualenv
RUN pip install virtualenv #?
RUN pip3 install virtualenv #?
RUN python3 -V
RUN python -V
RUN echo $PATH
#### firefox ######
#### firefox ######

# add local files
COPY /root /
COPY bashrc  /config/.bashrc
RUN chmod 755 /config/.bashrc
RUN usermod -s /bin/bash abc

##
RUN apt-get clean && \
rm -rf \
 /tmp/* \
 /var/lib/apt/lists/* \
 /var/tmp/*

#DUPLO_CHANGE:
USER root
RUN echo "abc  ALL=NOPASSWD: ALL" >> /etc/sudoers

# ports and volumes
EXPOSE 8443


#SSO nginx reverse proxy changes
# RUN apt-get update
# RUN apt-get install -y --no-install-recommends libatlas-base-dev gfortran nginx supervisor

# COPY flaskapp/supervisor.conf /etc/supervisor/conf.d/
# COPY flaskapp/nginx.conf /etc/nginx/nginx.conf
# COPY flaskapp/app /flaskapp/app
# COPY flaskapp/uwsgi.ini /etc/uwsgi/uwsgi.ini
# COPY flaskapp/requirements.txt /flaskapp/requirements.txt
# RUN pip install uwsgi

# RUN pip install -r /flaskapp/requirements.txt
# RUN pip install supervisor

# RUN useradd --no-create-home nginx
# RUN rm /etc/nginx/sites-enabled/default
# RUN mkdir -m 777 -p /flaskapp/flask_cookie

# CMD supervisord -n
