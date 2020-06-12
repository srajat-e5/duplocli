
import json
import datetime
import argparse
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_create_tfstate_step1 import AwsCreateTfstateStep1
from duplocli.terraform.aws.step1.get_aws_object_list import GetAwsObjectList
from duplocli.terraform.aws.step2.aws_tf_import_step2 import AwsTfImportStep2
from duplocli.terraform.aws.aws_parse_params import AwsParseParams, ImportParameters

import psutil

class AwsTfImport:

    def __init__(self, importParameters):
        self.utils = TfUtils()
        self.params = importParameters

    def execute_step(self, steps="all"):

        if steps == "step1":
            # self.execute_step1()
            self.execute_step1_with_api()
        elif steps == "step2":
            self.execute_step2()
        else:
            # self.execute_step1()
            self.execute_step1_with_api()
            self.execute_step2()

    def execute_step1_with_api(self):
        print("\n====== execute_step1 ====== START")
        api = GetAwsObjectList(tenant_name=self.tenant_name, aws_az=self.aws_az)
        tenant_resources = api.get_tenant_resources()
        self.step1 = AwsCreateTfstateStep1(self.aws_az)
        self.step1.execute_step(tenant_resources)
        #download_aws_keys
        if self.download_aws_keys:
            print(" ====== execute_step1 download_key ====== \n")
            tenant_key_pairs = api.get_tenant_key_pair_list()
            self.step1.download_key(tenant_key_pairs, duplo_api_json_file=self.duplo_api_json_file)
        print(" ====== execute_step1 ====== DONE\n")

    def execute_step1(self):
        print("\n====== execute_step1 ====== START")
        self.step1 = AwsCreateTfstateStep1(tenant_name=self.tenant_name, aws_az=self.aws_az)
        self.step1.execute_step()
        print(" ====== execute_step1 ====== DONE\n")

    def execute_step2(self):
        print("\n====== execute_step2 ====== START")
        self.step2 = AwsTfImportStep2(tenant_name=self.tenant_name, aws_az=self.aws_az)
        self.step2.execute_step()
        print(" ====== execute_step2 ====== DONE\n")

        #self.step2 = AwsTfImportStep2(tenant_name=tenant_name, aws_az=aws_az)


######## ####
def main(params):
    tenant = AwsTfImport(params)


if __name__ == '__main__':
    # set PYTHONPATH=c:\duplocli;
    # python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2"
    # python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2" --download_aws_keys True --duplo_api_json_file "duplo_api_json.json"
    params_resovler = AwsParseParams()
    parsed_args = params_resovler.get_parser().parse_args()
    final_params = params_resovler.resolve_parameters(parsed_args)
    main(final_params)
