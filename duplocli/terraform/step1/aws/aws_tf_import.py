import argparse
from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.schema.aws_tf_schema import AwsTfSchema

from duplocli.terraform.step1.aws.aws_tf_step1 import AwsCreateTfstateStep1
from duplocli.terraform.step1.aws.aws_resources_step1 import AwsResourcesStep1
from duplocli.terraform.step1.aws.aws_tf_step2 import AwsTfImportStep2
from duplocli.terraform.tfbackup.backup_import_folders import BackupImportFolders

import psutil
import os
class AwsTfImport:
    
    def __init__(self, params):
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params)
        self.params = params
        os.environ['AWS_DEFAULT_REGION'] = self.params.aws_region

    def execute(self):
        self.pre_execute()
        for module in self.params.modules():
            self.module_execute(module)
        self.post_execute()
        return  [ self.params.temp_folder , self.params.import_name, self.params.zip_file_path+".zip"]

    def module_execute(self, module):
        self.params.set_step_type(module)
        if module == 'infra':
            self._infra()
        else:
            self._tenant()
        self._state_to_tf_main()

    def _infra(self):
        print("\n====== execute_infra_step1 ====== START")
        self.params.set_step("step1")
        api = AwsResourcesStep1(self.params)
        tenant_resources = api.get_infra_resources()
        print(tenant_resources)
        self.step1 = AwsCreateTfstateStep1(self.params)
        self.step1.execute_step(tenant_resources)
        #download_aws_keys
        if self.params.download_aws_keys == 'yes':
            print(" ====== execute_infra_step1 download_key ====== \n")
            tenant_key_pairs = api.get_tenant_key_pair_list()
            self.step1.download_key(tenant_key_pairs)
        print(" ====== execute_infra_step1 ====== DONE\n")

    def _tenant(self):
        self.params.set_step("step1")
        print("\n====== execute_tenant_step1 ====== START")
        api = AwsResourcesStep1(self.params)
        tenant_resources = api.get_tenant_resources()
        self.step1 = AwsCreateTfstateStep1(self.params)
        self.step1.execute_step(tenant_resources)
        #download_aws_keys
        if self.params.download_aws_keys == 'yes':
            print(" ====== execute_tenant_step1 download_key ====== \n")
            tenant_key_pairs = api.get_tenant_key_pair_list()
            self.step1.download_key(tenant_key_pairs)
        print(" ====== execute_tenant_step1 ====== DONE\n")

    def _state_to_tf_main(self):
        self.params.set_step("step2")
        print("\n====== execute_step2 ====== START")
        self.step2 = AwsTfImportStep2(self.params)
        self.step2.execute_step()
        print("temp_folder  ***** ", self.params.temp_folder)
        print("import_name  ***** ", self.params.import_name)
        print("zip_file_path  ***** ", os.path.abspath(self.params.zip_file_path+".zip"))
        print(" ====== execute_step2 ====== DONE\n")

        #self.step2 = AwsTfImportStep2(tenant_name=tenant_name, aws_az=aws_az)

    def pre_execute(self):
        self.file_utils.delete_folder(self.params.temp_folder)
        for module in self.params.modules():
            self.params.set_step_type(module)
            self.params.set_step("step1")
            self.file_utils._ensure_folders()

    def zip_import(self, module):
        pass

    def post_execute(self):
        self.zip_import()
        # backup and s3 sync
        if os.path.exists("import_tf_backup_settings_auth_service.json"):
            backup_settings_json="import_tf_backup_settings_auth_service.json"
        else:
            backup_settings_json="import_tf_backup_settings_default.json"
        eackupImportFolders = BackupImportFolders(backup_settings_json=backup_settings_json)
        eackupImportFolders.backup_folders()