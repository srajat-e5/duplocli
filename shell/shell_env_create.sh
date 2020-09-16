#!/bin/sh

envPath=/shell/.duplo_env.sh
echo "export ARM_SUBSCRIPTION_ID='${ARM_SUBSCRIPTION_ID}'"  > $envPath
echo "export ARM_CLIENT_ID='${ARM_CLIENT_ID}'"  >> $envPath
echo "export ARM_CLIENT_SECRET='${ARM_CLIENT_SECRET}'"  >> $envPath
echo "export ARM_TENANT_ID='${ARM_TENANT_ID}'"  >> $envPath

#todo use these names in env
echo "export AZURE_SUBSCRIPTION_ID='${ARM_SUBSCRIPTION_ID}'"  > $envPath
echo "export AZURE_CLIENT_ID='${ARM_CLIENT_ID}'"  >> $envPath
echo "export AZURE_CLIENT_SECRET='${ARM_CLIENT_SECRET}'"  >> $envPath
echo "export AZURE_TENANT_ID='${ARM_TENANT_ID}'"  >> $envPath





