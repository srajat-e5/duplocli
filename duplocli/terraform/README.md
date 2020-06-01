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
 
 
