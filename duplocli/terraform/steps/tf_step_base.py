
from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.schema.tf_schema import TfSchema
import requests
import os
import psutil


class TfImportStepBase :

    aws_tf_schema = {}
    main_tf_json_dict = {"resource": {}}
    resources_dict = main_tf_json_dict["resource"]
    tf_import_sh_list = []

    def __init__(self, params):
        self.params = params
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params, step=self.params.step, step_type=self.params.step_type)

        self.aws_tf_schema = {}
        self.main_tf_json_dict = {"resource": {}}
        self.resources_dict = self.main_tf_json_dict["resource"]
        self.tf_import_sh_list = []

        self._load_schema()
        self.provider()

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
        self.tf_import_sh_list.append('terraform plan ')

    ############ provider ##########
    def provider(self):
        if self.params.provider == "aws":
            self.aws_provider()
        elif self.params.provider == "azurerm":
            self.azurerm_provider()
        elif self.params.provider == "google":
            pass
        elif self.params.provider == "kubernetes":
            pass
        else:
            self.aws_provider()

    def azurerm_provider(self):
        tf_resource_type = "provider"
        tf_resource_var_name = "azurerm"
        resource_obj = self._base_provider(tf_resource_type, tf_resource_var_name)
        resource_obj["version"] = "=2.0.0"
        self.tf_import_sh_list.append('terraform init ')
        return resource_obj

    def aws_provider(self):
        tf_resource_type = "provider"
        tf_resource_var_name = "aws"
        resource_obj = self._base_provider(tf_resource_type, tf_resource_var_name)
        resource_obj["version"] = "~> 2.0"
        resource_obj["region"] = self.params.aws_region  # should be variable
        self.tf_import_sh_list.append('terraform init ')
        return resource_obj

    def _base_provider(self, tf_resource_type, tf_resource_var_name):
        resource_obj = {}
        resource_obj[tf_resource_var_name] = {}
        self.main_tf_json_dict[tf_resource_type] = resource_obj
        return resource_obj[tf_resource_var_name]


    ############ helper  ##########

    def rm_aws_security_group_rule_tf_bug(self):

        if self.params.provider != 'aws':
            print(" SKIP ", self.params.provider, " rm_aws_security_group_rule_tf_bug ")
            return

        main_resources = self.main_tf_json_dict['resource']
        aws_security_group_rules = []
        object_type_bug = "aws_security_group_rule"  # #aws_security_group
        if object_type_bug in main_resources:
            aws_security_group_rules = list(main_resources[object_type_bug].keys())

        state_dict = self.file_utils.load_json_file(self.file_utils.tf_state_file())
        if "resources" in state_dict:
            resources = state_dict['resources']
        else:
            resources = state_dict['resource']

        resources_to_del = []
        for resource in resources:  # list
            # print(resource)
            if object_type_bug == resource["type"]:
                name = resource["name"]
                if name not in aws_security_group_rules:
                    # resources.remove(resource)
                    resources_to_del.append(resource)
                else:
                    print("name skip ", name)
        for resource in resources_to_del:  # list
            resources.remove(resource)
        # save
        self.file_utils.save_state_file(state_dict)
        # print(state_dict)

    ############ download_key public resources ##########
    def download_key(self,  aws_obj_list=[] ):
        if self.params.provider != 'aws':
            print(" SKIP ", self.params.provider, " key download_keys ")
            return (self.file_utils.tf_main_file(), self.file_utils.tf_state_file(), "")

        # download_aws_keys = self.params.download_aws_keys
        url = self.params.url
        tenant_id = self.params.tenant_id
        api_token = self.params.api_token
        if  url is None or tenant_id is None  or api_token is None :
            raise  Exception("to download_keys  - url, tenant_id, api_token are required.")

        for aws_key_pair_instance in  aws_obj_list:
            #aws_obj = {"name":name, "key_name":key_name, "instanceId":instanceId}
            key_name = aws_key_pair_instance['key_name']
            instanceId = aws_key_pair_instance['instanceId']
            endpoint = "{0}/subscriptions/{1}/getKeyPair/{2}".format(url   , tenant_id  , instanceId)
            headers = {"Authorization": "Bearer {0}".format( api_token )}
            response = requests.get(endpoint,   headers=headers)
            self.file_utils.save_key_file(key_name, response.content )
            print("**** aws import step1 : save_key_file ", key_name, instanceId)
        return (self.file_utils.tf_main_file(), self.file_utils.tf_state_file(), self.file_utils.keys_folder())


