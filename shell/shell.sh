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


#************************************** aws_import_tf **************************************
aws_import_tf() {

    if [ -z "$AWS_ACCESS_KEY_ID" ]; then
        echo "aws_import_tf SKIP:"
        return 0
    fi

    cd /duplocli/duplocli/terraform/
    import_name="aws-$tenant_name-`date +"%m_%d_%y__%H_%M_%S"`"
    zip_file_path="/zip/$import_name"
    mkdir -p /zip
    python3 tf_import_aws.py --tenant_name $tenant_name --aws_region $aws_region --download_aws_keys "yes" \
     --url $duplo_endpoint --tenant_id $tenant_id --api_token $api_token --zip_file_path=$zip_file_path
    aws s3 cp $zip_file_path.zip s3://$EXPORT_BUCKET/


    s3_signed_url="`aws s3 presign s3://$EXPORT_BUCKET/$import_name.zip`"

    echo ""
    echo ""
    echo ""
    echo ""
    echo ""
    echo "******************************************************************************************************************"
    echo "*******************PLEASE COPY s3 url to download the terrfrom file from s3 *******************"
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

}

#************************************** azure_import_tf **************************************
azure_import_tf() {


    if [ -z "$ARM_SUBSCRIPTION_ID" ]; then
        echo "azure_import_tf SKIP:"
        return 0
    fi

    sh /shell/shell_env_create.sh
    source /shell/.duplo_env.sh

    cd /duplocli/duplocli/terraform/
    import_name="azure-$tenant_name-`date +"%m_%d_%y__%H_%M_%S"`"
    zip_file_path="/zip/$import_name"
    mkdir -p /zip
    python3 tf_import_azure.py --tenant_name $tenant_name --aws_region $aws_region --download_aws_keys "yes" \
     --url $duplo_endpoint --tenant_id $tenant_id --api_token $api_token --zip_file_path=$zip_file_path
    aws s3 cp $zip_file_path.zip s3://$EXPORT_BUCKET/


    s3_signed_url="`aws s3 presign s3://$EXPORT_BUCKET/$import_name.zip`"

    echo ""
    echo ""
    echo ""
    echo ""
    echo ""
    echo "******************************************************************************************************************"
    echo "*******************PLEASE COPY s3 url to download the terrfrom file from s3 *******************"
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

}


#************************************** KUBECTL **************************************
if [ -n "$KUBECTL" ]; then
    /bin/bash /shell/docker_init.sh $k8_api_url $k8_token duploservices-$tenant_name $pod

#************************************** $TF **************************************
elif [ -n "$TF" ]; then
    export PYTHONPATH=$PYTHONPATH:/duplocli
    echo "************************************** calling aws_import_tf *********************c "
    aws_import_tf
    echo "************************************** calling azure_import_tf *********************c "
    azure_import_tf
    echo "************************************** import_tf Dome *********************c "

    cd /duplocli
    /bin/bash
fi

