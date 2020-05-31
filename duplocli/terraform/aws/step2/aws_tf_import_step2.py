import boto3
import json
import os
# from bson importtf json_util
import datetime
from collections import defaultdict
# src/tenant_import/aws/aws_tf_import_step1.py
# from tenant_import_to_tf.aws.step2.aws_to_tf_util_step2 import AwsToTfUtilStep2
from tenant_import_to_tf.aws.common.tf_utils import TfUtils
from tenant_import_to_tf.aws.schema.aws_tf_schema import AwsTfSchema


class AwsTfImportStep2():


    # # duplo_aws_tf_schema
    # duplo_aws_tf_schema_file = "../data/duplo_aws_tf_schema.json"
    # duplo_aws_tf_schema = {}

    # aws_tf_schema
    aws_tf_schema_file = "../data/aws_tf_schema.json"
    aws_tf_schema = {}
    is_allow_none = True

    # terraform.tfstate from step1
    state_file = "../output/step1/terraform.tfstate"
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


    def __init__(self, state_file="../output/step1/terraform.tfstate", step="step2"):
        self.utils = TfUtils()
        self.state_file=state_file
        self.step=step
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

    def load_schema(self):
        self.aws_tf_schema = AwsTfSchema (self.aws_tf_schema_file)
        #self.utils.load_json_file(self.aws_tf_schema_file)

    def load_state_file(self):
        self.state_dict = self.utils.load_json_file(self.state_file)

    def process(self):
        self.state_dict = self.utils.load_json_file(self.state_file)
        # self.utils.print_json(self.state_dict, sort_keys=False)
        resources = self.state_dict['resources']
        for resource in resources:
            self._process_resource(resource)

    def _process_resource(self, resource):
        print("=========================\n\n\n")
        tf_resource_type = resource["type"]
        tf_resource_var_name = resource["name"]
        print(tf_resource_type, "=", tf_resource_var_name)
        attributes = resource['instances'][0]['attributes'] # ??? WHY this is array?
        # self.utils.print_json(attributes, sort_keys=False)

        ### create: resource "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        tf_resource_type_root[tf_resource_var_name] = resource_obj

        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
        self.utils.print_json(schema.data_dict(), sort_keys=False)
        for attribute_name, attribute  in attributes.items():
            # print(attribute_name)
            is_nested = attribute_name  in schema.nested
            is_computed = attribute_name  in schema.computed
            if  is_nested:
                self._process_nested(attribute_name, attribute, resource_obj, schema)
            elif not is_computed:
                #https://github.com/hashicorp/terraform/issues/18321
                #https://github.com/terraform-providers/terraform-provider-aws/issues/4954
                #todo: forcing aws_instance recreation?
                if attribute_name in ["user_data", "replicas" ]:
                    # pass; #resource_obj[attribute_name] = attribute
                    resource_obj["lifecycle"]={"ignore_changes": [attribute_name] }
                elif tf_resource_type == "aws_s3_bucket" and attribute_name in ["acl", "force_destroy" ]:
                    resource_obj["lifecycle"] = {"ignore_changes": ["acl", "force_destroy" ]}
                elif attribute is not None  or self.is_allow_none : #or  (isinstance(object, list) and len(list) > 0)
                    resource_obj[attribute_name]=attribute
            else:
                pass

    def _process_nested(self, nested_atr_name, nested_atr, resource_obj_parent, schema_nested):
        schema = schema_nested.nested_block[nested_atr_name]
        # print("_process_nested", schema.data_dict())
        if isinstance(nested_atr, dict):
            resource_obj = {}
            resource_obj_parent[nested_atr_name] = resource_obj
            #
            for attribute_name, attribute in nested_atr.items():
                # print(attribute_name)
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




    ##### copied from aws_to_tf_util_step1.py: todo: consolidate with changes ##############
    def empty_output(self):
        cmd_mod = "rm -rf  {0}/*".format(self.tf_output_path)
        os.system(cmd_mod)

    def save_tf_files(self):
        ##only terraform plan
        self.tf_import_sh_list.append('terraform plan ')
        ## save
        self.utils.save_to_json(self.tf_json_file, self.main_tf_json_dict)
        self.utils.save_run_script(self.tf_import_script_file, self.tf_import_sh_list)
        self.utils.save_to_json("../output/step2/terraform.tfstate", self.state_dict)

        #wrapper script to cd into "../output/step2"
        run_sh_list = []
        run_sh_list.append("cd {0}".format(self.tf_output_path))
        run_sh_list.append("chmod 777 *.sh")
        # run_sh_list.append("cp -f {0} {1}".format(self.state_file, self.tf_output_path))
        # run_sh_list.append('terraform init ')
        # run_sh_list.append("cp -f {0} {1}".format(self.state_file, "."))
        # run_sh_list.append("./{0} > output.log 2>&1 ".format(self.tf_import_script_file_name))
        run_sh_list.append("./{0}  ".format(self.tf_import_script_file_name))
        # run_sh_list.append('terraform plan ')
        self.utils.save_run_script(self.tf_run_script_file, run_sh_list)

    def create_state(self):
        self.save_tf_files()
        cmd_mod = "chmod +x {0}; ./{0}".format(self.tf_run_script_file)
        print("create_state ", cmd_mod)
        os.system(cmd_mod)

    ######
    def aws_provider(self):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "provider"
        tf_resource_var_name = "aws"
        ### create: resource "provider" "aws"
        resource_obj = self._base_provider(tf_resource_type, tf_resource_var_name)
        resource_obj["version"] = "~> 2.0"
        resource_obj["region"] = "us-west-2" # should be variable
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




######## ####
def main():
    tenant = AwsTfImportStep2()
    tenant.process()
    tenant.save_tf_files()
    tenant.create_state()


if __name__ == '__main__':
    main()
    ######## ####

