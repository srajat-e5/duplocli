import boto3
import os
from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.schema.aws_tf_schema import AwsTfSchema
from duplocli.terraform.common.tf_file_utils import TfFileUtils
import shutil
import psutil

class AwsTfImportStep2():

    is_allow_none = True
    # aws_tf_schema
    aws_tf_schema = {}
    state_dict = {}

    # main.tf.json
    main_tf_json_dict = {"resource": {}}
    resources_dict = main_tf_json_dict["resource"]

    #tf_import_script.sh
    tf_import_sh_list = []

    def __init__(self, params):
        self.params = params
        aws_az = params.aws_region
        tenant_name = params.tenant_name

        self.utils = TfUtils(params)
        self.aws_az = aws_az
        self.tenant_name = params.tenant_name
        self.tenant_id = self.utils.get_tenant_id(tenant_name)
        ####
        # file_utils for steps
        self.file_utils = TfFileUtils(self.params, step=self.step)
        self.file_utils_step1 = TfFileUtils(self.params, step="step1")
        self.file_utils_final = TfFileUtils(self.params, step="final")
        self._load_schema() 
        self.aws_provider()

    #######
    def execute_step(self):
        self._empty_output()
        self.process()
        self._create_tf_state()

    def process(self):
        self._state_file_or_default()
        self._zip_folder_or_default()
        # self.utils.print_json(self.state_dict, sort_keys=False)
        if "resources" in  self.state_dict:
            resources = self.state_dict['resources']
        else:
            resources = self.state_dict['resource']
        for resource in resources:
            self._process_resource(resource)
        return self.main_tf_json_dict

    ####### load json files
    def _load_schema(self):
        self.aws_tf_schema = AwsTfSchema(self.params, self.file_utils.aws_tf_schema_file())

    def _load_tf_state_file(self):
        self.state_dict = self.file_utils.load_json_file(self.state_read_from_file)

    def _zip_folder_or_default(self):
        self.zip_folder = self.file_utils.zip_folder()
        return self.zip_folder

    def _state_file_or_default(self):
        if self.params.state_file is not None:
            if psutil.WINDOWS:
                self.state_read_from_file = self.params.state_file.replace("/", "\\")
            else:
                self.state_read_from_file = self.params.state_file
        else:
            self.state_read_from_file = self.file_utils_step1.tf_state_file()
        self._load_tf_state_file()


    #############
    def _process_resource(self, resource):
        # print("**** aws import step2 : ", "=========================\n\n\n")
        tf_resource_type = resource["type"]
        tf_resource_var_name = resource["name"]
        print("**** aws import step2 : ", tf_resource_type, "=", tf_resource_var_name)
        attributes = resource['instances'][0]['attributes'] # ??? WHY this is array?
        # self.utils.print_json(attributes, sort_keys=False)

        ### create: resource "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        tf_resource_type_root[tf_resource_var_name] = resource_obj

        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
        # self.utils.print_json(schema.data_dict(), sort_keys=False)
        for attribute_name, attribute  in attributes.items():
            # print("**** aws import step2 : ", attribute_name)
            is_nested = attribute_name  in schema.nested
            is_computed = attribute_name  in schema.computed
            is_optional = attribute_name  in schema.optional
            if  is_nested:
                self._process_nested(attribute_name, attribute, resource_obj, schema)
            elif is_optional or not is_computed :
                #https://github.com/hashicorp/terraform/issues/18321
                #https://github.com/terraform-providers/terraform-provider-aws/issues/4954
                #todo: forcing aws_instance recreation?: should we move to configuration data/mapping_aws_keys_to_tf_keys.json
                if attribute_name in ["user_data", "replicas" ]:
                    # pass; #resource_obj[attribute_name] = attribute
                    resource_obj["lifecycle"]={"ignore_changes": [attribute_name] }
                elif tf_resource_type == "aws_elasticache_cluster" and attribute_name in ["replication_group_id", "cache_nodes"]:
                    resource_obj["lifecycle"] = {"ignore_changes": ["replication_group_id", "cache_nodes"]}
                elif tf_resource_type == "aws_s3_bucket" and attribute_name in ["acl", "force_destroy","acceleration_status"]:
                    resource_obj["lifecycle"] = {"ignore_changes": ["acl", "force_destroy", "acceleration_status"]}
                elif tf_resource_type == "aws_iam_instance_profile" and attribute_name in ["roles"]:
                    resource_obj["lifecycle"] = {"ignore_changes": ["roles"]}
                elif tf_resource_type == "aws_instance" and attribute_name in ["cpu_core_count", "cpu_threads_per_core"]:
                    pass #resource_obj["lifecycle"] = {"cpu_core_count": "cpu_threads_per_core"}
                elif attribute_name == "id":
                    pass
                elif attribute is not None  or self.is_allow_none : #or  (isinstance(object, list) and len(list) > 0)
                    resource_obj[attribute_name]=attribute
            else:
                pass

    def _process_nested(self, nested_atr_name, nested_atr, resource_obj_parent, schema_nested):
        schema = schema_nested.nested_block[nested_atr_name]
        # print("**** aws import step2 : ", "_process_nested", schema.data_dict())
        if isinstance(nested_atr, dict):
            resource_obj = {}
            resource_obj_parent[nested_atr_name] = resource_obj
            #
            for attribute_name, attribute in nested_atr.items():
                # print("**** aws import step2 : ", attribute_name)
                is_nested = attribute_name in schema.nested
                is_computed = attribute_name in schema.computed
                if is_nested:
                    self._process_nested(attribute_name, attribute, resource_obj, schema)
                elif not is_computed:
                    if attribute_name == "user_data":
                        resource_obj[attribute_name] = attribute
                    elif attribute is not None or self.is_allow_none:
                        resource_obj[attribute_name] = attribute
                else:
                    pass
        elif isinstance(nested_atr, list):
            resource_obj = []
            resource_obj_parent[nested_atr_name] = resource_obj

    ######
    def aws_provider(self):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "provider"
        tf_resource_var_name = "aws"
        ### create: resource "provider" "aws"
        resource_obj = self._base_provider(tf_resource_type, tf_resource_var_name)
        resource_obj["version"] = "~> 2.0"
        resource_obj["region"] = self.aws_az # should be variable
        self.tf_import_sh_list.append('terraform init ')
        return resource_obj

        # automate sync

    def _base_provider(self, tf_resource_type, tf_resource_var_name):
        ### create: resource "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        resource_obj = {}
        resource_obj[tf_resource_var_name] = {}
        self.main_tf_json_dict[tf_resource_type] = resource_obj
        # self.utils.print_json( self.main_tf_json_dict)
        return resource_obj[tf_resource_var_name]

    def _get_or_create_tf_resource_type_root(self, tf_resource_type):
        ### create: resource "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        if tf_resource_type in self.resources_dict:
            return self.resources_dict[tf_resource_type]
        else:
            self.resources_dict[tf_resource_type] = {}
            return self.resources_dict[tf_resource_type]


    ##### manage files and state ##############
    def _empty_output(self):
        self.file_utils.empty_temp_folder()
        self.file_utils_final.ensure_empty_temp_folder(self.file_utils.zip_folder())

    def _copy_final(self):
        self._zip_folder_or_default()
        self.file_utils.ensure_empty_temp_folder(self.file_utils._temp_final_folder())
        # self.file_utils.ensure_empty_temp_folder(self.zip_folder)
        copy_files=[]
        copy_files.append(self.file_utils.tf_state_file())
        copy_files.append(self.file_utils.tf_main_file())
        copy_files.append(self.file_utils.keys_folder())
        self.file_utils.zip_final_folder(self.tenant_name,
                                             self.file_utils._temp_final_folder(),
                                             self.zip_folder,
                                             copy_files )
    def _create_tf_state(self):
        # self._empty_output()
        ## save files
        self._plan()
        self.file_utils.save_state_file(self.state_dict)
        self.file_utils.save_main_file(self.main_tf_json_dict)
        self.file_utils.save_tf_import_script(self.tf_import_sh_list)
        self.file_utils.save_tf_run_script()
        ## execute script
        self.file_utils.create_state(self.file_utils.tf_run_script())
        self._copy_final()



    def _plan(self):
        ## needed : terraform init and terraform plan
        self.tf_import_sh_list.append('terraform init ')
        self.tf_import_sh_list.append('terraform plan ')
