
import json
import datetime
import argparse
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_create_tfstate_step1 import AwsCreateTfstateStep1
from duplocli.terraform.aws.step1.get_aws_object_list import GetAwsObjectList
from duplocli.terraform.aws.step2.aws_tf_import_step2 import AwsTfImportStep2
from duplocli.terraform.aws.aws_parse_params import AwsParseParams, ImportParameters
from duplocli.terraform.aws.backup_import_folders import BackupImportFolders

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

        # backup and s3 sync
        if os.path.exists("import_tf_backup_settings_auth_service.json"):
            backup_settings_json="import_tf_backup_settings_auth_service.json"
        else:
            backup_settings_json="import_tf_backup_settings_default.json"
        eackupImportFolders = BackupImportFolders(backup_settings_json=backup_settings_json)
        eackupImportFolders.backup_folders()

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
