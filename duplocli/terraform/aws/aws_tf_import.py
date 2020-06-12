
import json
import datetime
import argparse
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_create_tfstate_step1 import AwsCreateTfstateStep1
from duplocli.terraform.aws.step1.get_aws_object_list import GetAwsObjectList
from duplocli.terraform.aws.step2.aws_tf_import_step2 import AwsTfImportStep2
from duplocli.terraform.aws.aws_parse_params import AwsParseParams, ImportParameters

import psutil
import os
class AwsTfImport:

    def __init__(self, params):
        self.utils = TfUtils(params)
        self.params = params
        os.environ['AWS_DEFAULT_REGION'] = self.params.aws_region

    def execute_step(self, steps="all"):
        if steps == "step1":
            self.execute_step1_with_api()
        elif steps == "step2":
            self.execute_step2()
        else:
            self.execute_step1_with_api()
            self.execute_step2()

    def execute_step1_with_api(self):
        print("\n====== execute_step1 ====== START")
        api = GetAwsObjectList(self.params)
        tenant_resources = api.get_tenant_resources()
        self.step1 = AwsCreateTfstateStep1(self.params)
        self.step1.execute_step(tenant_resources)
        #download_aws_keys
        if self.params.download_aws_keys == 'yes':
            print(" ====== execute_step1 download_key ====== \n")
            tenant_key_pairs = api.get_tenant_key_pair_list()
            self.step1.download_key(tenant_key_pairs)
        print(" ====== execute_step1 ====== DONE\n")

    def execute_step2(self):
        print("\n====== execute_step2 ====== START")
        self.step2 = AwsTfImportStep2(self.params)
        self.step2.execute_step()
        print(" ====== execute_step2 ====== DONE\n")

        #self.step2 = AwsTfImportStep2(tenant_name=tenant_name, aws_az=aws_az)


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
    # python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2"
    # python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2" --download_aws_keys True --duplo_api_json_file "duplo_api_json.json"
    #python aws_tf_import.py --params_json_file_path "/Users/brighu/_duplo_code/duplocli/duplocli/terraform/aws/duplo_api_json_test.json"
    params_resovler = AwsParseParams()
    parsed_args = params_resovler.get_parser().parse_args()
    final_params = params_resovler.resolve_parameters(parsed_args)
    main(final_params)
