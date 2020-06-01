import json
import datetime
from collections import defaultdict

import os

from duplocli.terraform.aws.common.tf_utils import TfUtils


class AwsToTfUtilStep1 :
    step = "step1"

    # mapping_aws_to_tf_state
    aws_to_tf_state_sync_ids_file = "data/aws_to_tf_sync_id_mapping.json"
    mapping_aws_to_tf_state_sync_ids = []

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

        # mapping_aws_to_tf_state
        self.mapping_aws_to_tf_state_sync_ids = self._load_aws_to_tf_state_sync_ids(self.aws_to_tf_state_sync_ids_file)
        ## script files
        self.tf_output_path = self.utils.get_tf_output_path(self.step)
        self.tf_json_file = self.utils.get_save_to_output_path(self.step, self.main_tf_json_file_name)
        self.tf_import_script_file = self.utils.get_save_to_output_path(self.step, self.tf_import_script_file_name)
        self.tf_run_script_file = self.utils.get_save_to_output_path(self.step, self.tf_run_script_file_name)
        #
        self.empty_output()
        self.aws_provider()

    ############ aws tf resources ##########
    #todo: could be automated using schema -- using required fields + data/duplo_aws_tf_schema.json
    ############ aws tf resources ##########
    def aws_elasticache_cluster(self, aws_obj):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "aws_elasticache_cluster"
        tf_resource_var_name = aws_obj['ClusterId']
        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # resource_obj['ami'] = "aaa"

    def aws_s3_bucket(self, aws_obj):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "aws_s3_bucket"
        tf_resource_var_name = aws_obj['Name']
        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        # resource_obj['ami'] = "aaa"
        return resource_obj

    def aws_db_instance(self, aws_obj):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "aws_db_instance"
        tf_resource_var_name = aws_obj['DBInstanceIdentifier']
        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        resource_obj['instance_class'] = "aa"
        # resource_obj['ami'] = "aaa"
        return resource_obj

    def aws_instance(self, aws_obj, name):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "aws_instance"
        tf_resource_var_name = name
        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        resource_obj['instance_type'] = "aa"
        resource_obj['ami'] = "aaa"
        return resource_obj

    def aws_iam_instance_profile(self, aws_obj):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "aws_iam_instance_profile"
        tf_resource_var_name = aws_obj['InstanceProfileName']
        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        return resource_obj

    def aws_iam_role(self, aws_obj):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "aws_iam_role"
        tf_resource_var_name = aws_obj['RoleId']
        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        #required ?
        assume_role_policy = self.utils.getVal(aws_obj, "AssumeRolePolicyDocument")
        resource_obj['assume_role_policy'] = "{}" #self.utils.to_json_str(assume_role_policy)
        return resource_obj

    def aws_security_group(self, aws_obj):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "aws_security_group"
        tf_resource_var_name = aws_obj['GroupName']
        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        return resource_obj

    def aws_vpc(self, aws_obj):
        ### "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type = "aws_vpc"
        tf_resource_var_name = "duplo-vpc"
        ### create: resource tf_resource_type  tf_resource_var_name
        resource_obj = self._init_tf_resource(tf_resource_type, tf_resource_var_name, aws_obj)
        return resource_obj

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
    #todo: could be automated using schema -- using required fields + data/duplo_aws_tf_schema.json
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

    ############ aws_to_tf_state_sync_id ##########
    def _get_aws_to_tf_state_sync_id(self, tf_resource_type,  aws_obj):
        ### get aws sync_id: used to update tf state
        tf_resource_type_sync_id_key = self.mapping_aws_to_tf_state_sync_ids[tf_resource_type]
        ### get aws sync_id value: from aws_obj
        tf_resource_type_sync_id = aws_obj[tf_resource_type_sync_id_key]
        return tf_resource_type_sync_id

    def _load_aws_to_tf_state_sync_ids(self, aws_to_tf_state_sync_ids_file):
        ### load mapping: aws sync_ids and tf resources
        aws_to_tf_state_sync_ids_json = self.utils.load_json_file(aws_to_tf_state_sync_ids_file)
        aws_to_tf_state_sync_ids = aws_to_tf_state_sync_ids_json['aws']
        return aws_to_tf_state_sync_ids
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
