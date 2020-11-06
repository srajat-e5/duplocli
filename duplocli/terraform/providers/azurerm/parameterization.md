

## parameterization
### usage : export terraform from azure
``` 
# myoutputfoldername = tenant1
duplocli/duplocli/terraform/tf_import_azure.py  --import_name tenant1  --import_module tenant --tenant_name azdemo1

```

### files in final output folder 
    * variables.tf.json = variable defination
    * terraform.tfvars.json = default values for variables
    * main.tf.json = tf main file     
    * replace.py   = utility to rename parameter names. Only used in new stack.        
    * terraform.tfstate = tf state. only used for existing stack
    
### existing stack 
``` 
# source "/shell/.duplo_env.sh" ##for docker
# source ~/.duplo_env.sh # mac linux
# .duplo_env.sh  =
##### source PATH_TO_DUPLO_ENV/.duplo_env.sh  
##
#export AZURE_SUBSCRIPTION_ID="x"
#export AZURE_CLIENT_ID="xx"
#export AZURE_CLIENT_SECRET="xx"
#export AZURE_TENANT_ID="xx"
##
#export ARM_SUBSCRIPTION_ID="x"
#export ARM_CLIENT_ID="xx"
#export ARM_CLIENT_SECRET="xx"
#export ARM_TENANT_ID="xx"
 
terrform init
terrform plan -var-file=terraform.tfvars.json

```

### new stack 
``` 
source ~/.duplo_env.sh
terrform init

# must rename tenant name/prefix. all globaly unique azure object names e.g. storage
python replace.py --src duploservices --dest tfsvs
python replace.py --src azdemo1 --dest tftenant20

#plan
terrform plan -var-file=terraform.tfvars.json

#create new stack
terrform apply -var-file=terraform.tfvars.json

```

 