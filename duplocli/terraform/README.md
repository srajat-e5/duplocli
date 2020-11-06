#steps to run 

# setup python  
## install requirements: tested with python 3.6 and conda
pip install -r requirements.txt  

####duplocloud/shell:terraform_kubectl_v8
##setup terraform: https://learn.hashicorp.com/terraform/getting-started/install.html
### Terraform Install
    * mac
        brew install terraform
    * windows
        choco install terraform
    * Terraform Manual installation
       * Download appropriate files from 
        https://www.terraform.io/downloads.html
       * Extract and add terrform to PATH
       
 ## Configure aws access. (It will shared by terraform and boto3)
    * Please refer to aws documentation for configuration.
        https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html

 ## Steps to import duplo managed aws resources into terrform managed state 
      * cd  into  duplocli/terraform/aws folder 
      * Run 'aws_tf_import.py' script. 
      * This will create files terrform files : main.tf.json & terraform.tfstate
      *  'aws_tf_import.py'  arguments :
         
       '''  
       
        argument to python file

        [-t / --tenant_id TENANTID]           -- TenantId e.g. 97a833a4-2662-4e9c-9867-222565ec5cb6
        [-n / --tenant_name TENANTNAME]         -- TenantName e.g. webdev
        [-r / --aws_region AWSREGION]          -- AWSREGION  e.g. us-west2
        [-a / --api_token APITOKEN]           -- Duplo API Token
        [-u / --url URL]                -- Duplo URL  e.g. https://msp.duplocloud.net
        [-k / --download_aws_keys DOWNLOADKEYS]       -- Aws keypair=yes/no, private key used for ssh into EC2 servers
        [-z / --zip_folder ZIPFOLDER]          -- folder to save imported terrorform files in zip format
        [-j / --params_json_file_path PARAMSJSONFILE]     -- All params passed in single JSON file
        [-h / --help HELP]               -- help



        OR alternately 

        pass the above parameters in single json file

       [-j/--params_json_file_path PARAMSJSONFILE] = FOLDER/terraform_import_json.json
            terraform_import_json.json
            {
              "tenant_name": "xxxxxx",
              "aws_region": "xxxxxx",
              "zip_folder": "zip",
              "download_aws_keys": "yes",
              "url": "https://xxx.duplocloud.net",
              "tenant_id": "xxx-2662-4e9c-9867-9a4565ec5cb6",
              "api_token": "xxxxxx"
            }

        OR alternately 
        pass the above parameters in ENV variables
        export tenant_name="xxxxxx"
        export aws_region="xxxxxx"
        export zip_folder="zip",
        export download_aws_keys="yes",
        export url="https://xxx.duplocloud.net",
        export tenant_id="xxx-2662-4e9c-9867-9a4565ec5cb6",
        export api_token="xxxxxx"

        Sequence of parameters evaluation is: default -> ENV -> JSON_FILE -> arguments
        parameters in argument 
         ->  override  parameters in terraform_import_json
        AND parameters in terraform_import_json
         ->   override  parameters in ENV variables
        AND parameters in ENV variables
         ->   override default values (default_parameters.json)
       '''
       ''' 
         python aws_tf_import.py --tenant_name "bigdata01" --aws_region "us-west-2" 
          '''
  
  ## Output Files
      *  duplocli/terraform/aws/step2/main.tf.json
      *  duplocli/terraform/aws/step2/terraform.tfstate
      *  duplocli/terraform/aws/keys/PKEY_FILES

  ## Log files
      *  duplocli/terraform/aws/log/step1_log.log
      *  duplocli/terraform/aws/log/step2_log.log 

  # Modifing and re-running Terraform scripts 
      *  Make changes to terraform files 
      **  duplocli/terraform/aws/step2/main.tf.json
      **  duplocli/terraform/aws/step2/terraform.tfstate
      * Could run terraform commands like 
      ''' 
        terrform plan 
        terrform show 
      '''
       
       
 
# use cases: TODO
## new tenant creation
### create new key_pair. (by adding following entry into main.ts)
  * new key pair 
  ```
    resource "tls_private_key" "this" {
       algorithm = "RSA"
    }
    
    module "key_pair" {
      source = "terraform-aws-modules/key-pair/aws"
    
      key_name   = "deployer-one"
      public_key = tls_private_key.this.public_key_openssh
    }
     
 
  # Or upload existing public key 
 
     resource "aws_key_pair" "deployer" {
         key_name   = "deployer-key"
         public_key = "ssh-rsa+EPuxIA4cDM4vzOqOkiMPhz5XK0whEjkVzTo4+S0puvDZuwIsdiW9mxhJc7tgBNL0cYlWSYVkz4G/fslNfRPW5mYAM49f4fhtxPb5ok4Q2Lg9dPKVHO/Bgeu5woMc7RY0p1ej6D4CKFE6lymSDJpW0YHX/wqE9+cfEauh7xZcG0q9t2ta6F6fmX0agvpFyZo8aFbXeUBr7osSCJNgvavWbM/06niWrOvYX2xwWdhXmXSrbX8ZbabVohBK41 email@example.com"
       }
  ```
 
    
###  Creating new tenant ?
    * please add manually the key_pair for new tenant. (as shown above )
    * remove ipaddresses from 'main.tf.json'
    * may be you need to look at conflicting additional optional attributes. by. running "terraform plan".
    
 
 ### param sample ?
 
  --import_name "my_test" 
  --import_module "infra" 
  --tenant_name "compliance" 
  --aws_region "us-west-2" 
  --download_aws_keys "yes" 
  --url "https://incloud.duplocloud.net" 
  --tenant_id "3c763ce2-2033-4c52-80a6-b21d94129e5a" 
  --api_token "AQAAANCMnd8BFdERjHoAwE_Cl-sBAAAAlNxds4SOrESIPwxm3nDxZAAAAAACAAAAAAAQZgAAAAEAACAAAACxV8cLYNUDxoXVeQ_jzLLQGvQkZTTHKAyBL_wCK688ywAAAAAOgAAAAAIAACAAAAADHLDHeIQ07ZMbvPdaeWFhjQM8mfuf3CtrmuXMstoSQJAAAADtAEvDRmIsu752o5P_jZdTUtAuhI88sIq4eJ7UOFxbOrK7Ap9m-V1Q8K6UfvE4c6UoDfPL-8aA8-azKr0ifEbe4Cr8-x141eNORaXE9DBfPDAJt7UF9fmrUz9Y43SZmLaKTs1ShpKsybTjs4b48D01HCLkPKYBZIcHae_-fLwr51o9iJBn3hVW4VFHnx633MhAAAAARzhH8-YcHfyHZR5HdfgE4bZXfi2jLyEidXUlJEr5SIy0v_Mld0eEQxLnDRvhhsf8anmQan5-FZu4HhcOKJtHhw"
 
 
 
 --import_name "my_test" 
 --infra  "yes"
 --tenant_name "compliance" 
 --aws_region "us-west-2" 
 --download_aws_keys "yes" 
 --url "https://incloud.duplocloud.net" 
 --tenant_id "xxxx-2033-4c52-80a6-b21d94129e5a" 
 --api_token "xxxxx"
{
  "tenant_name": "compliance",
  "aws_region":"us-west-2",
  "download_aws_keys": "yes",
  "url": "https://incloud.duplocloud.net",
  "tenant_id": "xxxxxxx-2033-4c52-80a6-b21d94129e5a",
   "api_token": "xxxxx"
 }
python python tf_import.py \
--tenant_name "compliance" --aws_region "us-west-2" --download_aws_keys "yes" \
--url "https://incloud.duplocloud.net" --tenant_id "xxx-2033-4c52-80a6-b21d94129e5a" --api_token "xxxxx"



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

 