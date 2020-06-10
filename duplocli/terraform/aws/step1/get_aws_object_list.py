import boto3
import json
# from bson importtf json_util
import datetime
from collections import defaultdict
# src/tenant_import/aws/aws_tf_import_step1.py
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_create_tfstate_step1 import AwsCreateTfstateStep1
from duplocli.terraform.aws.common.tf_file_utils import TfFileUtils

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
    debug_json = False
    create_key_pair = False
    #
    aws_obj_list = []
    aws_sg_list = []
    resources_unique_ids =[]
    mapping_aws_keys_to_tf_keys = []

    def __init__(self, tenant_name="k8-02", aws_az="us-west-2"):
        self.utils = TfUtils(step=self.step)
        self.file_utils = TfFileUtils(step=self.step)
        self.aws_az = aws_az
        #tenant
        self.tenant_name = tenant_name
        self.tenant_id = self.utils.get_tenant_id(tenant_name)
        self._load_mapping_aws_keys_to_tf_keys()

    #### public methods #######
    def get_tenant_resources(self):
        self.aws_obj_list = []
        self.aws_sg_list=[]
        self.resources_unique_ids = []
        self._aws_security_group()
        self._aws_iam_role()
        self._aws_iam_instance_profile()
        self._aws_instance()
        self._aws_db_instance()
        self._aws_s3_bucket()
        self._aws_elasticache_cluster()
        return  self.aws_obj_list

    def get_tenant_key_pair_list(self):
        awsclient = boto3.client('ec2')
        response = awsclient.describe_instances()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_instance._json", response)
        aws_objs=[]
        key_names=[]
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                tags = self.utils.getHashFromArray(instance["Tags"])
                tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
                #todo:this is for linux ... skip for windows
                if self.tenant_name == tenant_name_ec2 :
                    name = self.utils.getVal(tags, "Name")
                    instanceId = instance["InstanceId"]
                    key_name = instance["KeyName"]
                    if "Platform" in instance and instance["Platform"] == 'windows':
                        platform = instance["Platform"]
                        print("**** aws import step1 : get_key_pair_list platform is ", platform, name )
                        #skip?
                    if key_name not in key_names:
                        aws_obj = {"name":name, "key_name":key_name, "instanceId":instanceId}
                        aws_objs.append(aws_obj)
                        key_names.append(key_name)
                        # self.file_utils.print_json(aws_obj)
        if len(aws_objs) ==0 :
            print("**** aws import step1 : get_key_pair_list  :", "NOT_FOUND ANY")
        if self.debug_output:
            self.file_utils.print_json(aws_objs)
        return aws_objs

    ### private: methods to get individual resource for tenant ###
    def _aws_s3_bucket(self):
        awsclient = boto3.client('s3')
        response = awsclient.list_buckets()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_s3_bucket._json", response)
        aws_objs=[]
        for instance in response["Buckets"]:
            # pass
            aws_name=instance['Name']
            if aws_name.startswith(self.tenant_id+"-"):
                self.aws_resource("aws_s3_bucket", instance)
                aws_objs.append(instance)
                print("**** aws import step1 : aws_s3_bucket :", instance['Name'])
            #todo: resolve tenant specific
        if len(aws_objs) ==0 :
            print("**** aws import step1 : aws_s3_bucket :", "NOT_FOUND ANY")
        if self.debug_output:
            self.file_utils.print_json(aws_objs)
        return self

    def _aws_db_instance(self):
        awsclient = boto3.client('rds')
        response = awsclient.describe_db_instances()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_db_instance._json", response)
        aws_objs=[]
        for instance in response["DBInstances"]:
            arn = instance['DBInstanceArn']
            tags = awsclient.list_tags_for_resource(ResourceName=arn)
            tags_dict = self.utils.getHashFromArray(tags['TagList'])
            tannant_id_instance = self.utils.getVal(tags_dict, "Name")
            if tannant_id_instance == self.tenant_id:
                self.aws_resource("aws_db_instance", instance)
                aws_objs.append(instance)
                print("**** aws import step1 : aws_db_instance :", instance['DBInstanceIdentifier'], arn)
        if len(aws_objs) ==0 :
            print("**** aws import step1 : aws_db_instance :", "NOT_FOUND ANY")
        if self.debug_output:
            self.file_utils.print_json(aws_objs)
        return self

    def _aws_instance(self):
        awsclient = boto3.client('ec2')
        response = awsclient.describe_instances()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_instance._json", response)
        aws_objs=[]
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                tags = self.utils.getHashFromArray(instance["Tags"])
                tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
                if self.tenant_name == tenant_name_ec2 :
                    ######## aws_instance
                    name = self.utils.getVal(tags, "Name")
                    self.aws_resource("aws_instance", instance, tf_variable_id=name)
                    aws_objs.append(instance)
                    print("**** aws import step1 : aws_instance :", tenant_name_ec2, name)
                    ######## aws_key_pair
                    key_name = instance["KeyName"]
                    if self.create_key_pair:
                        self.aws_resource("aws_key_pair", instance, tf_variable_id=key_name, tf_import_id=key_name , skip_if_exists=True)
                    else:
                        print("**** aws import step1 :SKIP create aws_key_pair :", key_name, "as self.create_key_pair=", self.create_key_pair)
                    aws_objs.append(instance)
                    print("**** aws import step1 : aws_key_pair :" , key_name)
        if len(aws_objs) ==0 :
            print("**** aws import step1 : aws_instance :", "NOT_FOUND ANY")
        if self.debug_output:
            self.file_utils.print_json(aws_objs)
        return self

    def _aws_iam_role(self):
        awsclient = boto3.client('iam')
        iam = boto3.resource('iam')
        response = awsclient.list_roles()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_iam_role._json", response)
        aws_objs=[]
        for instance in response["Roles"]:
            name = self.utils.getVal(instance, "RoleName")
            if self.tenant_id == name :
                self.aws_resource("aws_iam_role", instance)
                arn = self.utils.getVal(instance, "Arn")
                print("**** aws import step1 : aws_iam_role :" ,name, arn)
                aws_objs.append(instance)
                role = iam.Role(name)
                attached_policies =  list(role.attached_policies.all())
                policies = list(role.policies.all())
                for inline_policy in policies:
                    ip_name = inline_policy.name
                    ip_role_name =  inline_policy.role_name
                    ip_sync_id = "{0}:{1}".format(ip_role_name, ip_name)
                    ip_data = {'name':ip_name, 'role_name':ip_role_name }
                    self.aws_resource("aws_iam_role_policy", ip_data, tf_variable_id = ip_name, tf_import_id=ip_sync_id)
                    aws_objs.append(ip_data)
                    print("**** aws import step1 : aws_iam_role_policy:", ip_role_name, ip_sync_id)
                for attached_policy in attached_policies:
                    arn = attached_policy.arn
                    policy_name = arn.split("/").pop()
                    sync_id="{0}/{1}".format(name, arn)
                    data = {'PolicyName': policy_name, 'RoleName': name, 'arn': arn}
                    self.aws_resource("aws_iam_role_policy_attachment", data, tf_variable_id=policy_name, tf_import_id=sync_id)
                    aws_objs.append(data)
                    print("**** aws import step1 : aws_iam_role_policy_attachment :", policy_name, sync_id)
        if len(aws_objs) ==0 :
            print("**** aws import step1 : aws_iam_role, aws_iam_role_policy, aws_iam_role_policy_attachment :", "NOT_FOUND ANY")
        if self.debug_output:
            self.file_utils.print_json(aws_objs)
        return self

    def _aws_security_group(self):
        awsclient = boto3.client('ec2')
        response = awsclient.describe_security_groups()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_security_group._json", response)
        aws_objs = []
        for instance in response["SecurityGroups"]:
            group_name = self.utils.getVal(instance, "GroupName")
            group_id = self.utils.getVal(instance, "GroupId")
            # print( "1", group_name, group_id)
            if  group_name == self.tenant_id or group_name.startswith(self.tenant_id+"-"):
                self.aws_resource("aws_security_group", instance)
                print("**** aws import step1 : aws_security_group :" ,group_name, group_id)
                aws_objs.append(instance)
        if len(aws_objs) ==0 :
            print("**** aws import step1 : aws_security_group :", "NOT_FOUND ANY")
        if self.debug_output:
            self.file_utils.print_json(aws_objs)
        return self

    def _aws_iam_instance_profile(self):
        awsclient = boto3.client('iam')
        response = awsclient.list_instance_profiles()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_iam_instance_profile._json", response)
        aws_objs = []
        for instance in response["InstanceProfiles"]:
            InstanceProfileName = self.utils.getVal(instance, "InstanceProfileName")
            InstanceProfileId = self.utils.getVal(instance, "InstanceProfileId")
            if  InstanceProfileName == self.tenant_id  :
                self.aws_resource("aws_iam_instance_profile", instance)
                print("**** aws import step1 : aws_iam_instance_profile :" , InstanceProfileName, InstanceProfileId)
                aws_objs.append(instance)
        if len(aws_objs) ==0 :
            print("**** aws import step1 : aws_iam_instance_profile :", "NOT_FOUND ANY")
        if self.debug_output:
            self.file_utils.print_json(aws_objs)
        return self

    def _aws_elasticache_cluster(self):
        awsclient = boto3.client('elasticache')
        response = awsclient.describe_cache_clusters()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_elasticache_cluster._json", response)
        aws_objs=[]
        for instance in response["CacheClusters"]:
            cacheClusterId = self.utils.getVal(instance, "CacheClusterId")
            securityGroups = instance['SecurityGroups']
            for securityGroup in securityGroups:
                securityGroupId = securityGroup['SecurityGroupId']
                if self._is_security_group_from_tenant(securityGroupId):
                    self.aws_resource("aws_elasticache_cluster", instance, tf_variable_id=cacheClusterId, tf_import_id=cacheClusterId,  skip_if_exists=True )
                    print("**** aws import step1 : aws_elasticache_cluster :", cacheClusterId)
        if len(aws_objs) ==0 :
            print("**** aws import step1 : aws_iam_instance_profile :", "NOT_FOUND ANY")
        if self.debug_output:
            self.file_utils.print_json(aws_objs)
        return self

    ########### helpers ###########
    def aws_resource(self, tf_resource_type, aws_obj, tf_variable_id=None, tf_import_id=None , skip_if_exists=False):
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
            if skip_if_exists:
                print("**** aws import step1 : SKIP: already exists - tf_resource_var_name should be unique **** aws import step1 : {0} {1} {2}".format(tf_resource_type,tf_resource_var_name, tf_id))
                return
            raise Exception("tf_resource_var_name should be unique {}".format(tf_id))
        # create array
        tf_resource = {"tf_resource_type": tf_resource_type, "tf_variable_id": tf_resource_var_name,
                       "tf_import_id": tf_resource_type_sync_id}
        self.aws_obj_list.append(tf_resource)
        self.resources_unique_ids.append(tf_id)
        return tf_resource

    ############ vdrify if object has securityGroup from tenant ##########
    def _get_aws_security_groups_for_tenant(self):
        if len(self.aws_sg_list) > 0:
            return self.aws_sg_list
        awsclient = boto3.client('ec2')
        response = awsclient.describe_security_groups()
        for instance in response["SecurityGroups"]:
            group_name = self.utils.getVal(instance, "GroupName")
            if group_name == self.tenant_id or group_name.startswith(self.tenant_id + "-"):
                self.aws_sg_list.append(instance)
        return self.aws_sg_list

    def _is_security_group_from_tenant(self, sg_group_id):
        self.aws_sg_objs = self._get_aws_security_groups_for_tenant()
        for instance in self.aws_sg_objs:
            group_id = self.utils.getVal(instance, "GroupId")
            if group_id == sg_group_id:
                return True
        return False

    ############ mapping_aws_keys_to_tf_keys = sync_ids and names ##########

    ############ mapping_aws_keys_to_tf_keys = sync_ids and names ##########
    def _load_mapping_aws_keys_to_tf_keys(self):
        self.mapping_aws_keys_to_tf_keys = self.file_utils.load_json_file(
                                                self.file_utils.mapping_aws_keys_to_tf_keys_file())
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
    file_utils = TfFileUtils(step="step1")
    api = GetAwsObjectList()
    json = api.get_tenant_resources()
    file_utils.print_json(json)
