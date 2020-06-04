import boto3
import os
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.schema.aws_tf_schema import AwsTfSchema


class AwsTfImportStep2():

    step = "step2"

    # aws_tf_schema
    aws_tf_schema_file = "data/aws_tf_schema.json"
    aws_tf_schema = {}
    is_allow_none = True


    # terraform.tfstate from step1
    state_read_from_file = "output/step1/terraform.tfstate"
    state_save_to_file = "output/step2/terraform.tfstate"
    state_dict = {}

    # main.tf.json
    main_tf_json_file_name = "main.tf.json"
    main_tf_json_dict = {"resource": {}}
    resources_dict = main_tf_json_dict["resource"]

    #tf_import_script.sh
    tf_import_script_file_name = "tf_import_script.sh"
    tf_import_sh_list = []

    # tf_import_script.sh
    tf_run_script_file_name = "run.sh"
    aws_az="us-west-2"

    def __init__(self, state_file="output/step1/terraform.tfstate", tenant_name="bigdata01", aws_az="us-west-2"):
        self.utils = TfUtils()
        self.aws_az = aws_az
        self.tenant_name = tenant_name
        self.tenant_id = self.utils.get_tenant_id(tenant_name)

        self.state_read_from_file=state_file
        self.load_schema()
        self.load_state_file()

        ## script files
        self.tf_output_path = self.utils.get_tf_output_path(self.step)
        self.tf_json_file = self.utils.get_save_to_output_path(self.step, self.main_tf_json_file_name)
        self.tf_import_script_file = self.utils.get_save_to_output_path(self.step, self.tf_import_script_file_name)
        self.tf_run_script_file = self.utils.get_save_to_output_path(self.step, self.tf_run_script_file_name)
        #
        self.empty_output()
        self.aws_provider()

    def execute_step(self):
        self.process()
        self._save_tf_files()
        self.create_state()

    def load_schema(self):
        self.aws_tf_schema = AwsTfSchema (self.aws_tf_schema_file)
        #self.utils.load_json_file(self.aws_tf_schema_file)

    def load_state_file(self):
        self.state_dict = self.utils.load_json_file(self.state_read_from_file)

    def process(self):
        self.state_dict = self.utils.load_json_file(self.state_read_from_file)
        # self.utils.print_json(self.state_dict, sort_keys=False)
        resources = self.state_dict['resources']
        for resource in resources:
            self._process_resource(resource)

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
                elif tf_resource_type == "aws_s3_bucket" and attribute_name in ["acl", "force_destroy"]:
                    resource_obj["lifecycle"] = {"ignore_changes": ["acl", "force_destroy"]}
                elif tf_resource_type == "aws_iam_instance_profile" and attribute_name in ["roles"]:
                        resource_obj["lifecycle"] = {"ignore_changes": ["roles"]}
                elif tf_resource_type == "aws_instance" and attribute_name in ["cpu_core_count", "cpu_threads_per_core"]:
                    resource_obj["lifecycle"] = {"cpu_core_count": "cpu_threads_per_core"}
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

    def _save_tf_files(self):

        ## needed : terraform init and terraform plan
        self.tf_import_sh_list.append('terraform plan ')

        ## save: tf_json_file , tf_import_script_file , terraform.tfstate
        self.utils.save_to_json(self.tf_json_file, self.main_tf_json_dict)
        self.utils.save_run_script(self.tf_import_script_file, self.tf_import_sh_list)
        self.utils.save_to_json(self.state_save_to_file, self.state_dict)

        #wrapper script  ? : cd into "../output/step2" and terraform init and terraform plan
        #an extra script in case of --- error check inside bash?
        run_sh_list = []
        run_sh_list.append("cd {0}".format(self.tf_output_path))
        run_sh_list.append("chmod 777 *.sh")
        run_sh_list.append("./{0}  ".format(self.tf_import_script_file_name))
        self.utils.save_run_script(self.tf_run_script_file, run_sh_list)


    def empty_output(self):
        self.utils.empty_output_folder(self.step)


    def create_state(self):
        self._save_tf_files()
        self.utils.create_state(self.tf_run_script_file, self.step)


