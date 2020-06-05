#steps to run 

# setup python  
## install requirements: tested with python 3.6 and conda
pip install -r requirements.txt  

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
        --tenant_name "YOUR_TENANT_NAME" : duplo tenant to be imported into Terraform state
        --aws_az "us-west-2"  : aws availability zone
        --download_aws_keys "True" : to export aws EC2 public ssh keys into keys folder
        --duplo_api_json_file "path_to_json_file": duplo api configuration e.g. --duplo_api_json=duplo_api_json.json
       ''' # duplo_api_json.json to downlopad keys fomr duplocloud.
            {
              "url": "https://XXX.duplocloud.net",
              "tenant_id": "XXXXXX",
              "api_token": "XXX"
            }
       '''
       ''' 
         python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2" --download_aws_keys True --duplo_api_json_file "duplo_api_json.json"
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
### create new key_pair  
  
  ```
    resource "tls_private_key" "this" {
       algorithm = "RSA"
    }
    
    module "key_pair" {
      source = "terraform-aws-modules/key-pair/aws"
    
      key_name   = "deployer-one"
      public_key = tls_private_key.this.public_key_openssh
    }
     
    ```
    
    
### importing into new tenant ins aws?
    * please add manually the key_pair for new tenant
    * e.g.
    ''' 
    resource "aws_key_pair" "deployer" {
      key_name   = "deployer-key"
      public_key = "ssh-rsa +EPuxIA4cDM4vzOqOkiMPhz5XK0whEjkVzTo4+S0puvDZuwIsdiW9mxhJc7tgBNL0cYlWSYVkz4G/fslNfRPW5mYAM49f4fhtxPb5ok4Q2Lg9dPKVHO/Bgeu5woMc7RY0p1ej6D4CKFE6lymSDJpW0YHX/wqE9+cfEauh7xZcG0q9t2ta6F6fmX0agvpFyZo8aFbXeUBr7osSCJNgvavWbM/06niWrOvYX2xwWdhXmXSrbX8ZbabVohBK41 email@example.com"
    }
    '''
    * remove ipaddresses from 'main.tf.json'
    * may be you need to look at conflicting optional attributes.
    
 
