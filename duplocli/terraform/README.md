#steps to run 

# setup python  
## install requirements: tested with python 3.6 and conda
pip install -r requirements.txt  

##setup terraform: https://learn.hashicorp.com/terraform/getting-started/install.html
### install using installer
    * mac
    brew install terraform
    * windows
    choco install terraform
### Manual installation
   * Download appropriate files from 
    https://www.terraform.io/downloads.html
   * Extract and add terrform to PATH
   
 ## steps to import duplo managed aws resources into terrform managed state 
  * Go to  duplocli/terraform/aws folder 
  * Run 'aws_tf_import.py' script to import files = main.tf.json & terraform.tfstate
  * python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2"
  
  ## check output main.tf.json and tfstate files. 
  *  Go to duplocli/terraform/aws/output folder
  *  terraform files:  step1/main.tf.json , step1/terraform.tfstate
  *  final state in duplocli/terraform/aws/output/step2
  *  terraform files : step2/main.tf.json or  step2/terraform.tfstate 
 
  ## debug log location
  # check logs
  *  Go to  duplocli/terraform/aws folder
  *  step1 log file = cat log/step1_log.log
  *  step2 log file = cat log/step2_log.log 

  # running - terrform plan with imported main.tf.json and tfstate files. 
  * Go to duplocli/terraform/aws/output/step1 folder
  * Or Go to duplocli/terraform/aws/output/step2 folder
  * RUN terraform commands 
  * e.g. 
  * terrform plan 
  * terrform show 
 
 

## importing into new tenant ins aws?
    * please add manually the key_pair for new tenant
    * e.g.
    ''' 
    resource "aws_key_pair" "deployer" {
      key_name   = "deployer-key"
      public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQD3F6tyPEFEzV0LX3X8BsXdMsQz1x2cEikKDEY0aIj41qgxMCP/iteneqXSIFZBp5vizPvaoIR3Um9xK7PGoW8giupGn+EPuxIA4cDM4vzOqOkiMPhz5XK0whEjkVzTo4+S0puvDZuwIsdiW9mxhJc7tgBNL0cYlWSYVkz4G/fslNfRPW5mYAM49f4fhtxPb5ok4Q2Lg9dPKVHO/Bgeu5woMc7RY0p1ej6D4CKFE6lymSDJpW0YHX/wqE9+cfEauh7xZcG0q9t2ta6F6fmX0agvpFyZo8aFbXeUBr7osSCJNgvavWbM/06niWrOvYX2xwWdhXmXSrbX8ZbabVohBK41 email@example.com"
    }
    '''
    * remove ipaddresses from 'main.tf.json'
    * may be you need to look at conflicting optional attributes.
    
    