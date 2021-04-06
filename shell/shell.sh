#!/bin/sh
URL=$1
# ID=$(python /shell/parseurl.py $URL 'container')
# SSH=$(python /shell/parseurl.py $URL 'ssh')

TF=$(python /shell/parseurl.py $URL 'terraform')
KUBECTL=$(python /shell/parseurl.py $URL 'kubectl')

IP=$(python /shell/parseurl.py $URL 'ip')
aws_region=$(python /shell/parseurl.py $URL 'aws_region')
tenant_name=$(python /shell/parseurl.py $URL 'tenant_name')
duplo_endpoint=$(python /shell/parseurl.py $URL 'duplo_endpoint')
tenant_id=$(python /shell/parseurl.py $URL 'tenant_id')
api_token=$(python /shell/parseurl.py $URL 'api_token')


pod=$(python /shell/parseurl.py $URL 'pod')
k8_api_url=$(python /shell/parseurl.py $URL 'k8_api_url')
k8_token=$(python /shell/parseurl.py $URL 'k8_token')

export PATH=/shell/bin:${PATH}
if [ -n "$KUBECTL" ]; then
    /bin/bash /shell/docker_init.sh $k8_api_url $k8_token duploservices-$tenant_name $pod 
elif [ -n "$TF" ]; then
    cd /duplocli
    import_name="$tenant_name-`date +"%m_%d_%y__%H_%M_%S"`"
    zip_file_path="/zip/$import_name"
    mkdir -p /zip
    python import_tf.py --tenant_name $tenant_name --aws_region $aws_region --download_aws_keys "yes" \
     --url $duplo_endpoint --tenant_id $tenant_id --api_token "$api_token" --zip_file_path=$zip_file_path
    aws s3 cp $zip_file_path.zip s3://$EXPORT_BUCKET/


    s3_signed_url="`aws s3 presign s3://$EXPORT_BUCKET/$import_name.zip`"

    echo ""
    echo ""
    echo ""
    echo ""
    echo ""
    echo "******************************************************************************************************************"
    echo "*******************PLEASE COPY s3 url to download the terraform file from s3 *******************"
    echo "s3 url = "
    echo "$s3_signed_url"
    echo "**************************************"
    echo "after download. Extract the zip file and cd into extracted folder"
    echo "run "
    echo "terraform init"
    echo "Now you should be able to use terraform commands like terraform plan or show"
    echo "**************************************"
    echo ""
    echo ""
    echo ""
    /bin/bash
fi
