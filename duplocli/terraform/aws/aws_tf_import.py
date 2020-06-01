
import json
import datetime
import argparse
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_tf_import_step1 import AwsTfImportStep1
from duplocli.terraform.aws.step2.aws_tf_import_step2 import AwsTfImportStep2


class AwsTfImport:

    def __init__(self, tenant_name=None, aws_az=None):

        if tenant_name is None:
            raise Exception("tenant is required")
        if aws_az is None:
            raise Exception("aws_az is required")

        self.utils = TfUtils()
        self.aws_az = aws_az
        self.tenant_name = tenant_name
        self.tenant_id = self.utils.get_tenant_id(tenant_name)

    def execute_step(self, steps="all"):

        if steps == "step1":
            self.execute_step1()
        elif steps == "step2":
            self.execute_step2()
        else:
            self.execute_step1()
            self.execute_step2()


    def execute_step1(self):
        print("\n====== execute_step1 ====== START")
        self.step1 = AwsTfImportStep1(tenant_name=self.tenant_name, aws_az=self.aws_az)
        self.step1.execute_step()
        print(" ====== execute_step1 ====== DONE\n")

    def execute_step2(self):
        print("\n====== execute_step2 ====== START")
        self.step2 = AwsTfImportStep2(tenant_name=self.tenant_name, aws_az=self.aws_az)
        self.step2.execute_step()
        print(" ====== execute_step2 ====== DONE\n")

        #self.step2 = AwsTfImportStep2(tenant_name=tenant_name, aws_az=aws_az)


######## ####
def main(steps="all", tenant_name="bigdata01", aws_az="us-west-2"):
    tenant = AwsTfImport(tenant_name=tenant_name, aws_az=aws_az)
    tenant.execute_step(steps=steps)
    # tenant.execute_step(steps="step1")
    #tenant.execute_step(steps="step2")

if __name__ == '__main__':
    # python aws_tf_import.py --tenant_name "bigdata01" --aws_az "us-west-2"
    parser = argparse.ArgumentParser(prog='AwsTfImport')
    parser.add_argument('--tenant_name', action='store', dest='tenant_name',
                        help='tenant name to import terraform start')
    parser.add_argument('--aws_az', action='store', dest='aws_az',
                        help='aws az to import terraform start')
    results = parser.parse_args()
    main(tenant_name = results.tenant_name, aws_az = results.aws_az)