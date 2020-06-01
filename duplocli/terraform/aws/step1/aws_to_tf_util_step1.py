import json
import datetime
from collections import defaultdict

import os

from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.schema.aws_tf_schema import AwsTfSchema


class AwsToTfUtilStep1 :
    step = "step1"

    # aws_tf_schema
    aws_tf_schema_file = "data/aws_tf_schema.json"
    aws_tf_schema = {}
    is_allow_none = True


    # mapping_aws_to_tf_state
    aws_to_tf_state_sync_ids_file = "data/aws_to_tf_sync_id_mapping.json"
    mapping_aws_to_tf_state_sync_ids = []

    # mapping_aws_to_tf_state
    mapping_aws_keys_to_tf_keys_file = "data/mapping_aws_keys_to_tf_keys.json"
    mapping_aws_keys_to_tf_keys = []

    # main.tf.json
    main_tf_json_file_name = "main.tf.json"
    main_tf_json_dict = {"resource":{}}
    resources_dict = main_tf_json_dict["resource"]

    #tf_import_script.sh
    tf_import_script_file_name = "tf_import_script.sh"
    tf_import_sh_list = []

    # tf_import_script.sh
    tf_run_script_file_name = "run.sh"


    def __init__(self, tenant_name="bigdata01", aws_az="us-west-2"):
        self.utils = TfUtils()
        self.aws_az = aws_az
        self.tenant_name = tenant_name
        self.tenant_id = self.utils.get_tenant_id(tenant_name)

        ## script files
        self.tf_output_path = self.utils.get_tf_output_path(self.step)
        self.tf_json_file = self.utils.get_save_to_output_path(self.step, self.main_tf_json_file_name)
        self.tf_import_script_file = self.utils.get_save_to_output_path(self.step, self.tf_import_script_file_name)
        self.tf_run_script_file = self.utils.get_save_to_output_path(self.step, self.tf_run_script_file_name)
        # mapping_aws_keys_to_tf_keys_file
        self._load_mapping_aws_keys_to_tf_keys()
        #
        self.load_schema()
        self.empty_output()
        self.aws_provider()

    def load_schema(self):
        self.aws_tf_schema = AwsTfSchema (self.aws_tf_schema_file)

        #self.utils.load_json_file(self.aws_tf_schema_file)
    ############ aws tf resources ##########
    #todo: could be automated using schema -- using required fields + data/duplo_aws_tf_schema.json
    def aws_resource(self, tf_resource_type, aws_obj, tf_name=None):

        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME" e.g. "aws_elasticache_cluster" "cluster1"
        if tf_name is None:
            tf_resource_var_name = self._get_aws_to_tf_state_sync_name(tf_resource_type,  aws_obj)
        else:
            tf_resource_var_name = tf_name

        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)

        #keep an eye ---we are neglecting datas type !
        #required fields: can not use current value from aws_obj. we do not know aws field name to tf field name mapping.
        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
        for required_name in schema.required:
            resource_obj[required_name] = "aa"
        return resource_obj

    ############ aws tf resources ##########
    def aws_elasticache_cluster(self, aws_obj):
        return self.aws_resource("aws_elasticache_cluster", aws_obj)
        # ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        # tf_resource_type = "aws_elasticache_cluster"
        # tf_resource_var_name = aws_obj['ClusterId']
        # ### create: resource tf_resource_type  tf_resource_var_name
        # resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # # resource_obj['ami'] = "aaa"

    def aws_s3_bucket(self, aws_obj):
        return self.aws_resource("aws_s3_bucket", aws_obj)
        # ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        # tf_resource_type = "aws_s3_bucket"
        # tf_resource_var_name = aws_obj['Name']
        # ### create: resource tf_resource_type  tf_resource_var_name
        # resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # # resource_obj['ami'] = "aaa"
        # return resource_obj

    def aws_db_instance(self, aws_obj):
        return self.aws_resource("aws_db_instance", aws_obj)
        # ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        # tf_resource_type = "aws_db_instance"
        # tf_resource_var_name = aws_obj['DBInstanceIdentifier']
        # ### create: resource tf_resource_type  tf_resource_var_name
        # resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # resource_obj['instance_class'] = "aa"
        # # resource_obj['ami'] = "aaa"
        # return resource_obj

    def aws_instance(self, aws_obj, name):
        return self.aws_resource("aws_instance", aws_obj, tf_name=name)
        # ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        # tf_resource_type = "aws_instance"
        # tf_resource_var_name = name
        # ### create: resource tf_resource_type  tf_resource_var_name
        # resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # resource_obj['instance_type'] = "aa"
        # resource_obj['ami'] = "aaa"
        # return resource_obj

    def aws_iam_instance_profile(self, aws_obj):
        return self.aws_resource("aws_iam_instance_profile", aws_obj)
        # ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        # tf_resource_type = "aws_iam_instance_profile"
        # tf_resource_var_name = aws_obj['InstanceProfileName']
        # ### create: resource tf_resource_type  tf_resource_var_name
        # resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # return resource_obj

    def aws_iam_role(self, aws_obj):
        return self.aws_resource("aws_iam_role", aws_obj)
        # ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        # tf_resource_type = "aws_iam_role"
        # tf_resource_var_name = aws_obj['RoleId']
        # ### create: resource tf_resource_type  tf_resource_var_name
        # resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # #required ?
        # assume_role_policy = self.utils.getVal(aws_obj, "AssumeRolePolicyDocument")
        # resource_obj['assume_role_policy'] = "{}" #self.utils.to_json_str(assume_role_policy)
        # return resource_obj

    def aws_security_group(self, aws_obj):
        return self.aws_resource("aws_security_group", aws_obj)
        # ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        # tf_resource_type = "aws_security_group"
        # tf_resource_var_name = aws_obj['GroupName']
        # ### create: resource tf_resource_type  tf_resource_var_name
        # resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # return resource_obj

    def aws_vpc(self, aws_obj):
        return self.aws_resource("aws_vpc", aws_obj)
        # ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        # tf_resource_type = "aws_vpc"
        # tf_resource_var_name = "duplo-vpc"
        # ### create: resource tf_resource_type  tf_resource_var_name
        # resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # return resource_obj

    def aws_provider(self):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "provider"
        tf_resource_var_name = "aws"
        ### create: resource "provider" "aws"
        resource_obj = self._base_provider(tf_resource_type, tf_resource_var_name)
        resource_obj["version"] = "~> 2.0"
        resource_obj["region"] = self.aws_az
        self.tf_import_sh_list.append('terraform init ')
        return resource_obj
    ############ aws tf resources ##########



    ############ utility methods ##########
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

    def _init_tf_resource(self, tf_resource_type, tf_resource_var_name, aws_obj):
        ### get aws sync_id: used to update tf state
        tf_resource_type_sync_id = self._get_aws_to_tf_state_sync_id(tf_resource_type,  aws_obj)

        ### create: resource "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        tf_resource_type_root[tf_resource_var_name] = resource_obj

        ### create: terraform import "TF_RESOURCE_TYPE.TF_RESOURCE_VAR_NAME" "tf_resource_type_sync_id"
        self.tf_import_sh_list.append(
            'terraform import "' + tf_resource_type + '.' + tf_resource_var_name + '"  "' + tf_resource_type_sync_id + '"')
        ### return:  resource_obj
        return resource_obj



    ############ mapping_aws_keys_to_tf_keys = sync_ids and names ##########
    def _load_mapping_aws_keys_to_tf_keys(self):
        self.mapping_aws_keys_to_tf_keys = self.utils.load_json_file(self.mapping_aws_keys_to_tf_keys_file)
        self.mapping_aws_to_tf_state_sync_ids = self.mapping_aws_keys_to_tf_keys['syncids']
        self.mapping_aws_to_tf_state_sync_names = self.mapping_aws_keys_to_tf_keys['names']

    def _get_aws_to_tf_state_sync_id(self, tf_resource_type,  aws_obj):
        if tf_resource_type not in self.mapping_aws_to_tf_state_sync_ids:
            raise Exception("please define sync_id for '{0}' mapping_aws_keys_to_tf_keys.json."
                            + " Used to aws id during terraform import.".format(tf_resource_type))

        ### get aws sync_id: used to update tf state
        aws_key = self.mapping_aws_to_tf_state_sync_ids[tf_resource_type]
        aws_key_val = aws_obj[aws_key]
        return aws_key_val

    def _get_aws_to_tf_state_sync_name(self, tf_resource_type,  aws_obj):
        if tf_resource_type not in self.mapping_aws_to_tf_state_sync_names:
            raise Exception("please define sync name for '{0}' mapping_aws_keys_to_tf_keys.json. "
                            + " Used to create a name for terraform resource in main.tf.json".format(tf_resource_type))

        ### get aws sync_name: used to create a name for terraform object in main.tf
        aws_key = self.mapping_aws_to_tf_state_sync_names[tf_resource_type]
        aws_key_val = aws_obj[aws_key]
        return aws_key_val

    ############ aws_to_tf_state_sync_id ##########

    ############ main.tf.json + script + generate state ##########

    def empty_output(self):
        self.utils.empty_output_folder(self.step)

    def create_state(self):
        self._plan()
        self._save_tf_files()
        self.utils.create_state(self.tf_run_script_file, self.step)

    def _save_tf_files(self):
        self.utils.save_to_json(self.tf_json_file, self.main_tf_json_dict)
        self.utils.save_run_script(self.tf_import_script_file, self.tf_import_sh_list)
        run_sh_list=[]
        run_sh_list.append("cd {0}".format(self.tf_output_path))
        run_sh_list.append("chmod 777 *.sh")
        run_sh_list.append("./{0}  ".format(self.tf_import_script_file_name))
        self.utils.save_run_script(self.tf_run_script_file, run_sh_list)
        # add plan to script

    def _plan(self):
        ### create: terraform plan ...
        # bug in tf -> creates extra aws_security_group_rule... remove aws_security_group_rule first.
        self.tf_import_sh_list.append(
            'terraform state list | grep aws_security_group_rule | xargs terraform state rm; terraform plan')

    ############ main.tf.json + script + generate state ##########
