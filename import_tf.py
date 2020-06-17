
import json
import datetime
import argparse
from duplocli.terraform.aws.aws_tf_import import AwsTfImport

from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_create_tfstate_step1 import AwsCreateTfstateStep1
from duplocli.terraform.aws.step1.get_aws_object_list import GetAwsObjectList
from duplocli.terraform.aws.step2.aws_tf_import_step2 import AwsTfImportStep2
from duplocli.terraform.aws.aws_parse_params import AwsParseParams, ImportParameters
from duplocli.terraform.aws.backup_import_folders import BackupImportFolders

import psutil
import os

######## ####
def main(params):
    tenant = AwsTfImport(params)
    tenant.execute_step(steps="all")

if __name__ == '__main__':
    # set PYTHONPATH=c:\duplocli;
    # """
    #     [-t / --tenant_id TENANTID]           -- TenantId e.g. 97a833a4-2662-4e9c-9867-222565ec5cb6
    #     [-n / --tenant_name TENANTNAME]         -- TenantName e.g. webdev
    #     [-r / --aws_region AWSREGION]          -- AWSREGION  e.g. us-west2
    #     [-a / --api_token APITOKEN]           -- Duplo API Token
    #     [-u / --url URL]                -- Duplo URL  e.g. https://msp.duplocloud.net
    #     [-k / --download_aws_keys DOWNLOADKEYS]       -- Aws keypair=yes/no, private key used for ssh into EC2 servers
    #     [-z / --zip_folder ZIPFOLDER]          -- folder to save imported terrorform files in zip format
    #     [-j / --params_json_file_path PARAMSJSONFILE]     -- All params passed in single JSON file
    #     [-h / --help HELP]               -- help
    #
    # """
    # python tf_import.py --tenant_name "bigdata01" --aws_region "us-west-2"
    # python tf_import.py --params_json_file_path "import_tf_parameters_auth_sevice.json"
    params_resovler = AwsParseParams()
    parsed_args = params_resovler.get_parser().parse_args()
    final_params = params_resovler.resolve_parameters(parsed_args)
    main(final_params)
