#!/bin/bash -e
/shell/shellinabox/shellinaboxd -t -d --port=9000 --disable-ssl --disable-peer-check --css /shell/custom.css --service "/:root:root:/home:AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION EXPORT_BUCKET=$EXPORT_BUCKET duplo_host=$duplo_host   duplo_token=$duplo_token JEEVA=KUMAR /shell/shell.sh \${url}"
