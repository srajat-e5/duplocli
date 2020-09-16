#!/bin/sh

envPath=/shell/.duplo_env.sh
echo "export ARM_SUBSCRIPTION_ID='${AZURE_SUBSCRIPTION_ID}'"  > $envPath
echo "export ARM_CLIENT_ID='${AZURE_CLIENT_ID}'"  >> $envPath
echo "export ARM_CLIENT_SECRET='${AZURE_CLIENT_SECRET}'"  >> $envPath
echo "export ARM_TENANT_ID='${AZURE_TENANT_ID}'"  >> $envPath

#todo use these names in env
echo "export AZURE_SUBSCRIPTION_ID='${AZURE_SUBSCRIPTION_ID}'"  >> $envPath
echo "export AZURE_CLIENT_ID='${AZURE_CLIENT_ID}'"  >> $envPath
echo "export AZURE_CLIENT_SECRET='${AZURE_CLIENT_SECRET}'"  >> $envPath
echo "export AZURE_TENANT_ID='${AZURE_TENANT_ID}'"  >> $envPath

echo "***** AZURE_TENANT_ID $AZURE_TENANT_ID"


envPath=/shell/.duplo_env.json
echo "{"  > $envPath
echo "'AZURE_SUBSCRIPTION_ID':'${AZURE_SUBSCRIPTION_ID}'"  >> $envPath
echo "'AZURE_CLIENT_ID'='${AZURE_CLIENT_ID}'"  >> $envPath
echo "'AZURE_CLIENT_SECRET'='${AZURE_CLIENT_SECRET}'"  >> $envPath
echo "'AZURE_TENANT_ID'='${AZURE_TENANT_ID}'"  >> $envPath
echo "}"  >> $envPath