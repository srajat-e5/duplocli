#steps to run 

# setup python  
# install requirements: tested with python 3.6 and conda
pip install -r requirements.txt  

#setup terraform: https://learn.hashicorp.com/terraform/getting-started/install.html
## install using installer
    * mac
    brew install terraform
    * windows
    choco install terraform
##Manual installation
   * download appropriate files from 
    https://www.terraform.io/downloads.html
   * Extract and add terrform to PATH
   
   
 # run terrform import
  cd duplocli/terraform
  cd aws
  python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2"
  
 # check logs
  *  cd to duplocli/terraform/aws 
  *  cat log/step1_log
  *  cat log/step2_log
 
  # run terrform plan 
  * cd to duplocli/terraform/aws/output/step2
  * RUN
  ** terrform plan 
 
 
