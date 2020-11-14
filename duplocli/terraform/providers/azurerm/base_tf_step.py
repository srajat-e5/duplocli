from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.schema.tf_schema import TfSchema
import requests
import os
import psutil


class AzureBaseTfImportStep:
    aws_tf_schema = {}
    main_tf_json_dict = {"resource": {}}
    resources_dict = main_tf_json_dict["resource"]
    tf_import_sh_list = []
    password_const = "Y8y2Nyu=WRcuQ?uw"
    def __init__(self, params):
        self.params = params
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params, step=self.params.step, step_type=self.params.step_type)
        self.aws_tf_schema = {}
        self.main_tf_json_dict = {"resource": {}}
        self.resources_dict = self.main_tf_json_dict["resource"]
        self.tf_import_sh_list = []
        self.tf_import_sh_list.append("")
        self._load_schema()
        self.provider()

    #####################################################
    def add_env_azurerm(self):
        pass

    #####################################################

    def _load_schema(self):
        self.aws_tf_schema = TfSchema(self.params)

    def _get_or_create_tf_resource_type_root(self, tf_resource_type):
        if tf_resource_type not in self.resources_dict:
            self.resources_dict[tf_resource_type] = {}
        return self.resources_dict[tf_resource_type]

    #####################################################
    def _create_tf_state(self):
        self._plan()
        self.file_utils.save_main_file(self.main_tf_json_dict)
        self.file_utils.save_tf_import_script(self.tf_import_sh_list)
        self.file_utils.save_tf_run_script()
        self.file_utils.create_state(self.file_utils.tf_run_script())

    def _plan(self):
        self.tf_import_sh_list.append('terraform init ')
        self.tf_import_sh_list.append('terraform refresh ')
        self.tf_import_sh_list.append('terraform plan ')

    ############ provider ##########
    def provider(self):
        self.azurerm_provider()

    def azurerm_provider(self):
        tf_resource_type = "provider"
        tf_resource_var_name = "azurerm"
        resource_obj = self._base_provider(tf_resource_type, tf_resource_var_name)
        resource_obj["version"] = ">= 2.15.0"
        resource_obj["features"] = {}
        self.tf_import_sh_list.append('terraform init ')
        self.tf_import_sh_list.append("source {0}".format(self.file_utils.get_azure_env_sh()))

        return resource_obj

    def _base_provider(self, tf_resource_type, tf_resource_var_name):
        resource_obj = {}
        resource_obj[tf_resource_var_name] = {}
        self.main_tf_json_dict[tf_resource_type] = resource_obj
        return resource_obj[tf_resource_var_name]

    ############ helper  ##########

    ############ download_key public resources ##########
    def download_key(self, aws_obj_list=[]):
        pass
