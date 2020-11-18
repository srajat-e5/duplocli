from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils

from duplocli.terraform.providers.azurerm.tf_step_resources import AzurermResources
from duplocli.terraform.providers.azurerm.tf_step1 import AzurermTfImportStep1
from duplocli.terraform.providers.azurerm.tf_step2 import AzurermTfImportStep2
from duplocli.terraform.providers.azurerm.tf_step3_param_stack_tf import AzurermTfStep3ParamStack
from duplocli.terraform.providers.azurerm.tf_step4_new_stack_tf import AzurermTfStep4NewStack

from duplocli.terraform.tfbackup.backup_import_folders import BackupImportFolders

import os


class AzurermTfSteps:
    disable_step1 = False
    disable_step2 = False  # True False
    disable_step3 = False
    disable_step4 = False

    def __init__(self, params):
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params)
        self.params = params

    ######## modules == tenant, infra or all customer objects ######

    def execute(self):
        ### pre execute
        self.pre_execute()
        ### execute modules -- infra_list, tenant_list, infra, tenant, all
        for module in self.params.modules():
            self._module_execute(module)
        ### post execute
        self.post_execute()
        return [self.params.temp_folder, self.params.import_name, self.params.zip_file_path + ".zip"]

    ######### _module_execute ######

    def _module_execute(self, module):
        self.params.set_step_type(module)
        self._step1_tf_state()
        self._step2_tf_main()
        self._step3_tf_vars_extract()
        self._step4_tf_vars_new_stack()

    ######### steps ######

    def _step1_tf_state(self):
        if self.disable_step1:
            return
        self.params.set_step("step1")
        print("\n")
        print(self.file_utils.stage_prefix(), "step1_tf_state")
        # step1
        api = self._api()
        if self.params.module == 'infra':
            cloud_resources = api.get_infra_resources()
        else:
            cloud_resources = api.get_tenant_resources()
        # step2
        self.step1 = self._init_step1()
        self.step1.execute(cloud_resources)

        # validate import succeeded
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()
        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception("Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")

        print(" ====== execute_infra_step1 ====== DONE\n")

    def _step2_tf_main(self):
        if self.disable_step2:
            return
        self.params.set_step("step2")
        print("\n====== execute_step2 ====== START")
        self.step2 = self._init_step2()
        self.step2.execute()
        print(" ====== execute_step2 ====== DONE\n")

    def _step3_tf_vars_extract(self):
        if self.disable_step3:
            return
        self.params.set_step("step3")
        print("\n====== execute_step3 ====== START")
        self.step3 = self._init_step3()
        self.step3.execute()
        print(" ====== execute_step3 ====== DONE\n")

    def _step4_tf_vars_new_stack(self):
        if self.disable_step4:
            return
        self.params.set_step("step4")
        print("\n====== execute_step4 new_stack ====== START")
        self.step4 = self._init_step4()
        self.step4.execute()
        print("temp_folder  ***** ", self.params.temp_folder)
        print("import_name  ***** ", self.params.import_name)
        print("zip_file_path  ***** ", os.path.abspath(self.params.zip_file_path + ".zip"))
        print(" ====== execute_step4 new_stack====== DONE\n")
        # AzurermTfVarsExtract

    ############# ######

    ############# ######
    def pre_execute(self):
        if self.disable_step1:
            return
        self.file_utils.delete_folder(self.params.temp_folder)
        for module in self.params.modules():
            self.params.set_step_type(module)
            self.params.set_step("step1")
            self.file_utils._ensure_folders()

    def post_execute(self):
        if self.disable_step1 or self.disable_step2 or self.disable_step3 or self.disable_step4:
            return
        self._zip()
        self._backup()
        print("================================================================================== ")
        print("temp_folder  ***** ", self.params.temp_folder)
        print("import_name  ***** ", self.params.import_name)
        print("log_folder  ***** ", self.file_utils.log_folder())
        print("fial_folder  ***** ", self.file_utils.final_folder())
        print("files  ***** ", self.file_utils.ls_folder(self.file_utils.final_folder()))
        print("zip_file_path  ***** ", os.path.abspath(self.params.zip_file_path + ".zip"))
        print("log_folder  ***** ", os.path.abspath(self.file_utils.log_folder()))
        print("final_folder  ***** ", os.path.abspath(self.file_utils.final_folder()))
        print("================================================================================== ")

    #####################

    def _init_step1(self):
        self.step1 = AzurermTfImportStep1(self.params)
        return self.step1

    def _init_step2(self):
        self.step2 = AzurermTfImportStep2(self.params)
        return self.step2

    def _init_step3(self):
        self.step3 = AzurermTfStep3ParamStack(self.params)
        return self.step3

    def _init_step4(self):
        self.step3 = AzurermTfStep4NewStack(self.params)
        return self.step3

    ######################

    def _backup(self):
        try:
            # backup and s3 sync
            terraform_folder = os.path.join("duplocli", "terraform")
            import_tf_backup_settings_auth_service = os.path.join(terraform_folder,
                                                                  "import_tf_backup_settings_auth_service.json")
            if os.path.exists(import_tf_backup_settings_auth_service):
                backup_settings_json = import_tf_backup_settings_auth_service
            else:
                backup_settings_json = self._get_backup_settings_json()  # os.path.join(terraform_folder,"tfbackup","json_default_tf_backup_settings.json")
            eackupImportFolders = BackupImportFolders(self.params, backup_settings_json=backup_settings_json)
            eackupImportFolders.backup_folders()
        except Exception as e:
            print("ERROR:Steps:", "backup", e)

    def _get_backup_settings_json(self):
        json_file = "backup_settings.json"
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), json_file)
        return json_path

    def _zip(self):
        copy_to_final_files = []
        copy_to_new_stack_files = []
        step_name = "step3"
        if self.disable_step3:
            step_name = "step2"
        for module in self.params.modules():
            self.params.set_step_type(module)
            self.params.set_step(step_name)
            copy_to_final_files.append(self.file_utils.tf_resources_file())
            copy_to_final_files.append(self.file_utils.tf_state_file())
            copy_to_final_files.append(self.file_utils.tf_main_file())
            if not self.disable_step3:
                copy_to_final_files.append(self.file_utils.file_in_work_folder_for_step("step3", "variables.tf.json"))
                copy_to_final_files.append(self.file_utils.file_in_work_folder_for_step("step3", "terraform.tfvars.json"))
               # copy_files.append(self.file_utils.file_in_work_folder_for_step("step3", "replace.py"))
                copy_to_final_files.append(self.file_utils.file_in_work_folder_for_step("step3", "parameterization.md"))
            if not self.disable_step4:
                copy_to_new_stack_files.append(self.file_utils.file_in_work_folder_for_step("step4", "replace_azdemo1.sh"))
                copy_to_new_stack_files.append(self.file_utils.file_in_work_folder_for_step("step4", "main.tf.json"))
                copy_to_new_stack_files.append(self.file_utils.file_in_work_folder_for_step("step4", "variables.tf.json"))
                copy_to_new_stack_files.append(self.file_utils.file_in_work_folder_for_step("step4", "terraform.tfvars.json"))
                copy_to_new_stack_files.append(self.file_utils.file_in_work_folder_for_step("step4", "replace.py"))
                copy_to_new_stack_files.append(self.file_utils.file_in_work_folder_for_step("step4", "parameterization.md"))

        copy_to_final_files.append(self.file_utils.keys_folder())

        self.file_utils.zip_final_folder(self.params.tenant_name,
                                         self.file_utils.final_folder(),
                                         self.file_utils.zip_folder(),
                                         copy_to_final_files, copy_to_new_stack_files)

    ############

    ###############
    def _api(self):
        self.api = AzurermResources(self.params)
        return self.api

    ###############
