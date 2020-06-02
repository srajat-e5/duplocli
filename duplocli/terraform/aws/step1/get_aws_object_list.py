import boto3
import json
# from bson importtf json_util
import datetime
from collections import defaultdict
# src/tenant_import/aws/aws_tf_import_step1.py
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_to_tf_util_step1 import AwsToTfUtilStep1


### json from duplo api ############
# [
#     {
#         "tf_import_id": "sg-05f79b15664ff729a",
#         "tf_resource_type": "aws_security_group",
#         "tf_variable_id": "duploservices-bigdata01-alb"
#     },
#     {
#         "tf_import_id": "sg-099cd5c1e20492476",
#         "tf_resource_type": "aws_security_group",
#         "tf_variable_id": "duploservices-bigdata01-lb"
#     },
#     ...
# ]

class GetAwsObjectList:
    step = "step1"
    debug_output = False
    debug_json = True
    aws_obj_list = []
    resources_unique_ids =[]
    # mapping_aws_to_tf_state
    mapping_aws_keys_to_tf_keys_file = "data/mapping_aws_keys_to_tf_keys.json"
    mapping_aws_keys_to_tf_keys = []

    def __init__(self, tenant_name="bigdata01", aws_az="us-west-2"):
        self.utils = TfUtils()
        self.aws_az = aws_az
        self.tenant_name = tenant_name
        self.tenant_id = self.utils.get_tenant_id(tenant_name)
        self._load_mapping_aws_keys_to_tf_keys()

    def get_tenant_resources(self):
        self.aws_obj_list = []
        self.resources_unique_ids = []
        self._aws_security_group()
        self._aws_iam_role()
        self._aws_iam_instance_profile()
        self._aws_instance()
        self._aws_db_instance()
        self._aws_s3_bucket()
        self._aws_elasticache_cluster()
        return  self.aws_obj_list

    ###
    def _aws_s3_bucket(self):
        awsclient = boto3.client('s3')
        response = awsclient.list_buckets()
        if self.debug_json:
            self.utils.save_json_to_log("aws_s3_bucket.json", response, self.step)
        aws_obj_list=[]
        for instance in response["Buckets"]:
            # pass
            aws_name=instance['Name']
            if aws_name.startswith(self.tenant_id+"-"):
                self.aws_resource("aws_s3_bucket", instance)
                aws_obj_list.append(instance)
                print("**** aws import : aws_s3_bucket ", instance['Name'])
            #todo: resolve tenant specific
        if len(aws_obj_list) ==0 :
            print("**** aws import : aws_s3_bucket ", "NOT_FOUND ANY")
        if self.debug_output:
            self.utils.print_json(aws_obj_list)
        return self

    def _aws_db_instance(self):
        awsclient = boto3.client('rds')
        response = awsclient.describe_db_instances()
        if self.debug_json:
            self.utils.save_json_to_log("aws_db_instance.json", response, self.step)
        aws_obj_list=[]
        for instance in response["DBInstances"]:
            arn = instance['DBInstanceArn']
            tags = awsclient.list_tags_for_resource(ResourceName=arn)
            tags_dict = self.utils.getHashFromArray(tags['TagList'])
            tannant_id_instance = self.utils.getVal(tags_dict, "Name")
            if tannant_id_instance == self.tenant_id:
                self.aws_resource("aws_db_instance", instance)
                aws_obj_list.append(instance)
                print("**** aws import : aws_db_instance", instance['DBInstanceIdentifier'], arn)
            #todo: resolve tenant specific
        if len(aws_obj_list) ==0 :
            print("**** aws import : aws_db_instance ", "NOT_FOUND ANY")
        if self.debug_output:
            self.utils.print_json(aws_obj_list)
        return self

    def _aws_instance(self):
        awsclient = boto3.client('ec2')
        response = awsclient.describe_instances()
        if self.debug_json:
            self.utils.save_json_to_log("aws_instance.json", response, self.step)
        aws_obj_list=[]
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                tags = self.utils.getHashFromArray(instance["Tags"])
                tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
                if self.tenant_name == tenant_name_ec2 :
                    name = self.utils.getVal(tags, "Name")
                    self.aws_resource("aws_instance", instance, tf_variable_id=name)
                    aws_obj_list.append(instance)
                    print("**** aws import : aws_instance " ,tenant_name_ec2, name)
        if len(aws_obj_list) ==0 :
            print("**** aws import : aws_instance ", "NOT_FOUND ANY")
        if self.debug_output:
            self.utils.print_json(aws_obj_list)
        return self

    def _aws_iam_role(self):
        awsclient = boto3.client('iam')
        response = awsclient.list_roles()
        if self.debug_json:
            self.utils.save_json_to_log("aws_iam_role.json", response, self.step)
        aws_obj_list=[]
        for instance in response["Roles"]:
            name = self.utils.getVal(instance, "RoleName")
            if self.tenant_id == name :
                self.aws_resource("aws_iam_role", instance)
                arn = self.utils.getVal(instance, "Arn")
                print("**** aws import : aws_iam_role " ,name, arn)
                aws_obj_list.append(instance)
        if len(aws_obj_list) ==0 :
            print("**** aws import : aws_iam_role ", "NOT_FOUND ANY")
        if self.debug_output:
            self.utils.print_json(aws_obj_list)
        return self

    def _aws_security_group(self):
        awsclient = boto3.client('ec2')
        response = awsclient.describe_security_groups()
        if self.debug_json:
            self.utils.save_json_to_log("aws_security_group.json", response, self.step)
        aws_obj_list = defaultdict(self.utils.def_value)
        for instance in response["SecurityGroups"]:
            group_name = self.utils.getVal(instance, "GroupName")
            group_id = self.utils.getVal(instance, "GroupId")
            # print( "1", group_name, group_id)
            if  group_name == self.tenant_id or group_name.startswith(self.tenant_id+"-"):
                self.aws_resource("aws_security_group", instance)
                print("**** aws import : aws_security_group " ,group_name, group_id)
                aws_obj_list[group_name] = instance
        if len(aws_obj_list) ==0 :
            print("**** aws import : aws_security_group ", "NOT_FOUND ANY")
        if self.debug_output:
            self.utils.print_json(aws_obj_list)
        return self

    def _aws_iam_instance_profile(self):
        awsclient = boto3.client('iam')
        response = awsclient.list_instance_profiles()
        if self.debug_json:
            self.utils.save_json_to_log("aws_iam_instance_profile.json", response, self.step)
        aws_obj_list = defaultdict(self.utils.def_value)
        for instance in response["InstanceProfiles"]:
            # print(instance)
            InstanceProfileName = self.utils.getVal(instance, "InstanceProfileName")
            InstanceProfileId = self.utils.getVal(instance, "InstanceProfileId")
            if  InstanceProfileName == self.tenant_id  :
                self.aws_resource("aws_iam_instance_profile", instance)
                print("**** aws import : aws_iam_instance_profile " , InstanceProfileName, InstanceProfileId)
                aws_obj_list[InstanceProfileName] = instance
        if len(aws_obj_list) ==0 :
            print("**** aws import : aws_iam_instance_profile ", "NOT_FOUND ANY")
        if self.debug_output:
            self.utils.print_json(aws_obj_list)
        return self

    ###### new
    def _aws_elasticache_cluster(self):
        awsclient = boto3.client('elasticache')
        response = awsclient.describe_cache_clusters()
        if self.debug_json:
            self.utils.save_json_to_log("aws_elasticache_cluster.json", response, self.step)
        aws_obj_list=[]
        for instance in response["CacheClusters"]:
            self.aws_resource("aws_elasticache_cluster", instance)
            #todo: resolve tenant specific

        if self.debug_output:
            self.utils.print_json(aws_obj_list)
        return self

    ########### helpers ###########
    def aws_resource(self, tf_resource_type, aws_obj, tf_variable_id=None, tf_import_id=None):
        # unique tf variable name
        if tf_variable_id is None:
            tf_resource_var_name = self._get_aws_to_tf_state_sync_name(tf_resource_type, aws_obj)
        else:
            tf_resource_var_name = tf_variable_id
        # tf_import_id  for import from aws
        if tf_import_id is None:
            tf_resource_type_sync_id = self._get_aws_to_tf_state_sync_id(tf_resource_type, aws_obj)
        else:
            tf_resource_type_sync_id = tf_import_id
        # validate name and syncid
        if tf_resource_var_name is None or tf_resource_type_sync_id is None:
            raise Exception("aws_resource 'tf_variable_id' 'tf_import_id' must be provided")
        # make sure you have unique tf_id .... since we are using array in place of hashtable
        tf_resource_type = tf_resource_type.strip()
        tf_resource_type_sync_id = tf_resource_type_sync_id.strip()
        tf_id = "{}.{}".format(tf_resource_type, tf_resource_var_name)
        if tf_id in self.resources_unique_ids:
            raise Exception("tf_resource_var_name should be unique {}".format(tf_id))
        # create array
        tf_resource = {"tf_resource_type": tf_resource_type, "tf_variable_id": tf_resource_var_name,
                       "tf_import_id": tf_resource_type_sync_id}
        self.aws_obj_list.append(tf_resource)
        self.resources_unique_ids.append(tf_id)
        return tf_resource

    ############ mapping_aws_keys_to_tf_keys = sync_ids and names ##########
    def _load_mapping_aws_keys_to_tf_keys(self):
        self.mapping_aws_keys_to_tf_keys = self.utils.load_json_file(self.mapping_aws_keys_to_tf_keys_file)
        self.mapping_aws_to_tf_state_sync_ids = self.mapping_aws_keys_to_tf_keys['syncids']
        self.mapping_aws_to_tf_state_sync_names = self.mapping_aws_keys_to_tf_keys['names']

    def _get_aws_to_tf_state_sync_id(self, tf_resource_type, aws_obj):
        if tf_resource_type not in self.mapping_aws_to_tf_state_sync_ids:
            raise Exception("please define sync_id for '{0}' mapping_aws_keys_to_tf_keys.json."
                            + " Used to aws id during terraform import.".format(tf_resource_type))

        ### get aws sync_id: used to update tf state
        aws_key = self.mapping_aws_to_tf_state_sync_ids[tf_resource_type]
        aws_key_val = aws_obj[aws_key]
        return aws_key_val

    def _get_aws_to_tf_state_sync_name(self, tf_resource_type, aws_obj):
        if tf_resource_type not in self.mapping_aws_to_tf_state_sync_names:
            raise Exception("please define sync name for '{0}' mapping_aws_keys_to_tf_keys.json. "
                            + " Used to create a name for terraform resource in main.tf.json".format(
                tf_resource_type))

        ### get aws sync_name: used to create a name for terraform object in main.tf
        aws_key = self.mapping_aws_to_tf_state_sync_names[tf_resource_type]
        aws_key_val = aws_obj[aws_key]
        return aws_key_val

        ############ aws_to_tf_state_sync_id ##########

######### main #######
if __name__ == '__main__':
    utils = TfUtils()
    api = GetAwsObjectList()
    json =api.get_tenant_resources()
    utils.print_json(json)


