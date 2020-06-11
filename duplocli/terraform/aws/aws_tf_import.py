
import json
import datetime
import argparse
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_create_tfstate_step1 import AwsCreateTfstateStep1
from duplocli.terraform.aws.step1.get_aws_object_list import GetAwsObjectList
from duplocli.terraform.aws.step2.aws_tf_import_step2 import AwsTfImportStep2
import psutil

class AwsTfImport:

    def __init__(self, tenant_name=None, aws_az=None, duplo_api_json_file=None, download_aws_keys=None):
        print("WINDOWS ", psutil.WINDOWS )
        if tenant_name is None:
            raise Exception("tenant is required")
        if aws_az is None:
            raise Exception("aws_az is required")
        if str(download_aws_keys) == "True":
            if duplo_api_json_file is None:
                raise Exception("duplo_api_auth_key is required for download_aws_keys")

        self.utils = TfUtils()
        self.aws_az = aws_az
        self.tenant_name = tenant_name
        self.tenant_id = self.utils.get_tenant_id(tenant_name)
        self.duplo_api_json_file = duplo_api_json_file
        self.download_aws_keys = download_aws_keys

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
def main(steps="all", tenant_name="bigdata01", aws_az="us-west-2"
         , duplo_api_json_file=None  , download_aws_keys=None
         ):
    tenant = AwsTfImport(tenant_name=tenant_name, aws_az=aws_az , duplo_api_json_file=duplo_api_json_file , download_aws_keys=download_aws_keys)
    tenant.execute_step(steps=steps)
    # tenant.execute_step(steps="step1")
    #tenant.execute_step(steps="step2")

if __name__ == '__main__':
    # set PYTHONPATH=c:\duplocli;
    # python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2"
    # python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2" --download_aws_keys True --duplo_api_json_file "duplo_api_json.json"

    parser = argparse.ArgumentParser(prog='AwsTfImport')
    parser.add_argument('--tenant_name', action='store', dest='tenant_name',
                        help='tenant name to import terraform start')
    parser.add_argument('--aws_az', action='store', dest='aws_az',
                        help='aws az to import terraform start')
    parser.add_argument('--duplo_api_json_file', action='store', dest='duplo_api_json_file',
                        help='duplo_api_json_file to access duplo details. required if download_aws_keys=True ')
    parser.add_argument('--download_aws_keys', action='store', dest='download_aws_keys',
                        help='if download_aws_keys=True , downloads keys for ec2 ssh login')

    results = parser.parse_args()
    # if results.download_aws_keys is not None:
    main(tenant_name = results.tenant_name
            , aws_az = results.aws_az
            , duplo_api_json_file = results.duplo_api_json_file
            , download_aws_keys = results.download_aws_keys)