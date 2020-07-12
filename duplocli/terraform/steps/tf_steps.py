from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils

from duplocli.terraform.steps.tf_step1 import TfImportStep1
from duplocli.terraform.steps.tf_step2 import TfImportStep2

from duplocli.terraform.resources.aws_resources import AwsResources
from duplocli.terraform.resources.azure_resources import AzureResources
from duplocli.terraform.resources.google_resources import GoogleResources
from duplocli.terraform.resources.kubernetes_resources import  KubernetesResources
from duplocli.terraform.resources.helm_resources import HelmResources

from duplocli.terraform.tfbackup.backup_import_folders import BackupImportFolders

import os
class TfSteps:
    only_step2 = False
    only_step1 = False
    def __init__(self, params):
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params)
        self.params = params

    ######### modules == tenant, infra or all customer objects ######
    def execute(self):
        self.pre_execute()

        ##  debug time
        if self.only_step1 or self.only_step2 :
            for module in self.params.modules():  # infra and tenants in modules to export
                self.params.set_step_type(module)
                if self.only_step1:
                    self._step1_tf_state()
                else:
                    self._step2_tf_main()
            return [ self.params.temp_folder , self.params.import_name, self.params.zip_file_path+".zip"]

        ###
        # execute
        for module in self.params.modules(): # infra and tenants in modules to export
            self.module_execute(module)
        self.post_execute()
        return  [ self.params.temp_folder , self.params.import_name, self.params.zip_file_path+".zip"]


    def module_execute(self, module):
        self.params.set_step_type(module)
        self._step1_tf_state()
        self._step2_tf_main()

    ######### steps ######

    def _step1_tf_state(self):
        self.params.set_step("step1")
        print("\n")
        print(self.file_utils.stage_prefix(), "step1_tf_state")
        #step1
        api = self._api()
        if self.params.module == 'infra':
            cloud_resources = api.get_infra_resources()
        else:
            cloud_resources = api.get_tenant_resources()
        #step2
        print(cloud_resources)
        self.step1 = self._step1()
        self.step1.execute(cloud_resources)
        # download_aws_keys
        if self.params.module == 'infra':
            pass
        else:
            if self.params.download_aws_keys == 'yes':
                print(" ====== execute_infra_step1 download_key ====== \n")
                tenant_key_pairs = api.get_tenant_key_pair_list()
                self.step1.download_key(tenant_key_pairs)
        print(" ====== execute_infra_step1 ====== DONE\n")

    #
    # def _step1_tf_infra(self):
    #     print("\n====== execute_infra_step1 ====== START")
    #     self.params.set_step("step1")
    #     api = self._api()
    #     tenant_resources = api.get_infra_resources()
    #     print(tenant_resources)
    #     self.step1 = self._step1()
    #     self.step1.execute(tenant_resources)
    #     #download_aws_keys
    #     if self.params.download_aws_keys == 'yes':
    #         print(" ====== execute_infra_step1 download_key ====== \n")
    #         tenant_key_pairs = api.get_tenant_key_pair_list()
    #         self.step1.download_key(tenant_key_pairs)
    #     print(" ====== execute_infra_step1 ====== DONE\n")
    #
    # def _step1_tf_tenant(self):
    #     self.params.set_step("step1")
    #     print("\n====== execute_tenant_step1 ====== START")
    #     api = self._api()
    #     tenant_resources = api.get_tenant_resources()
    #     self.step1 = self._step1()
    #     self.step1.execute(tenant_resources)
    #     #download_aws_keys
    #     if self.params.download_aws_keys == 'yes':
    #         print(" ====== execute_tenant_step1 download_key ====== \n")
    #         tenant_key_pairs = api.get_tenant_key_pair_list()
    #         self.step1.download_key(tenant_key_pairs)
    #     print(" ====== execute_tenant_step1 ====== DONE\n")

    def _step2_tf_main(self):
        self.params.set_step("step2")
        print("\n====== execute_step2 ====== START")
        self.step2 = self._step2()
        self.step2.execute()
        print("temp_folder  ***** ", self.params.temp_folder)
        print("import_name  ***** ", self.params.import_name)
        print("zip_file_path  ***** ", os.path.abspath(self.params.zip_file_path+".zip"))
        print(" ====== execute_step2 ====== DONE\n")
    ############# ######


    ############# ######
    def pre_execute(self):
        self.file_utils.delete_folder(self.params.temp_folder)
        for module in self.params.modules():
            self.params.set_step_type(module)
            self.params.set_step("step1")
            self.file_utils._ensure_folders()

    def post_execute(self):
        self._zip()
        # backup and s3 sync
        terraform_folder = os.path.join("duplocli", "terraform")
        import_tf_backup_settings_auth_service = os.path.join(terraform_folder, "import_tf_backup_settings_auth_service.json")
        if os.path.exists(import_tf_backup_settings_auth_service):
            backup_settings_json = import_tf_backup_settings_auth_service
        else:
            backup_settings_json =  os.path.join(terraform_folder,"tfbackup","json_default_tf_backup_settings.json")
        eackupImportFolders = BackupImportFolders(self.params, backup_settings_json=backup_settings_json)
        eackupImportFolders.backup_folders()

    def _zip(self):
        copy_files = []
        for module in self.params.modules():
            self.params.set_step_type(module)
            self.params.set_step("step2")
            copy_files.append(self.file_utils.tf_state_file())
            copy_files.append(self.file_utils.tf_main_file())
        copy_files.append(self.file_utils.keys_folder())
        self.file_utils.zip_final_folder(self.params.tenant_name,
                                         self.file_utils.final_folder(),
                                         self.file_utils.zip_folder(),
                                         copy_files)
    ############

    ###############
    def _api(self):
        if self.params.provider == "azurerm":
            self.api = AzureResources(self.params)
        elif self.params.provider == "google":
            self.api = GoogleResources(self.params)
        elif self.params.provider == "kubernetes":
            self.api = KubernetesResources(self.params)
        elif self.params.provider == "aws":
            os.environ['AWS_DEFAULT_REGION'] = self.params.aws_region
            self.api = AwsResources(self.params)
        elif self.params.provider == "helm":
            self.api = HelmResources(self.params)
        else:  # ? todo: error
            os.environ['AWS_DEFAULT_REGION'] = self.params.aws_region
            self.api = AwsResources(self.params)
        return self.api

    def _step1(self):
        # if self.step1 is None:
        #     self.step1 = TfImportStep1(self.params)
        self.step1 = TfImportStep1(self.params)
        return self.step1

    def _step2(self):
        # if self.step2 is None:
        #     self.step2 = TfImportStep2(self.params)
        self.step2 = TfImportStep2(self.params)
        return self.step2
    ###############