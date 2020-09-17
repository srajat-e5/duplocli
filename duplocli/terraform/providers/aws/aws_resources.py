import boto3
import json
import datetime
from collections import defaultdict
from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils


### json from duplo resources  ############
# [
#     {
#         "tf_import_id": "sg-05f79b15664ff729a",
#         "tf_resource_type": "azurerm_virtual_machine",
#         "tf_variable_id": "duploservices-bigdata01-alb"
#     },
#     {
#         "tf_import_id": "sg-099cd5c1e20492476",
#         "tf_resource_type": "aws_subnet",
#         "tf_variable_id": "duploservices-bigdata01-lb"
#     },
#     ...
# ]

class AwsResources :
    debug_print_out = False
    debug_json = True
    create_key_pair = False
    #
    aws_vpc_list = {}
    #
    tf_cloud_obj_list = []
    tf_cloud_sg_list = []
    resources_unique_ids =[]

    def __init__(self, params):
        self.params = params
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params, step=params.step, step_type=params.step_type)
        self.tenant_prefix = self.utils.get_tenant_id(params.tenant_name)

    ########### helpers ###########
    def tf_cloud_resource(self, tf_resource_type, tf_cloud_obj, tf_variable_id=None, tf_import_id=None , skip_if_exists=False):
        if tf_import_id in ["eni-0b69e66c897740b0f","eni-0bce26ce0e55b9648"]:
            print("tf_import_id", tf_import_id)
        tf_resource_var_name = tf_variable_id
        tf_resource_type_sync_id = tf_import_id
        if tf_resource_var_name is None or tf_resource_type_sync_id is None:
            raise Exception("tf_cloud_resource 'tf_variable_id' 'tf_import_id' must be provided")
        # self.file_utils.print_json(tf_cloud_obj)
        tf_resource_type = tf_resource_type.strip()
        tf_resource_type_sync_id = tf_resource_type_sync_id.strip()
        tf_resource_var_name =  tf_resource_var_name.strip()
        tf_resource_var_name=  tf_resource_var_name.replace(".","-").replace("/","-")
        tf_id = "{}.{}".format(tf_resource_type, tf_resource_var_name)
        if tf_id in self.resources_unique_ids:
            if skip_if_exists:
                print(self.file_utils.stage_prefix(), "SKIP: already exists - tf_resource_var_name should be unique : {0} {1} {2}".format(tf_resource_type,tf_resource_var_name, tf_id))
                return
            raise Exception("tf_resource_var_name should be unique {}".format(tf_id))
        # create array
        tf_resource = {"tf_resource_type": tf_resource_type, "tf_variable_id": tf_resource_var_name,
                       "tf_import_id": tf_resource_type_sync_id,
                       "module": self.file_utils.params.module}
        self.tf_cloud_obj_list.append(tf_resource)
        self.resources_unique_ids.append(tf_id)
        return tf_resource


    #### public methods #######
    def get_tenant_resources(self):
        self.tf_cloud_obj_list = []
        self.tf_cloud_sg_list=[]
        self.resources_unique_ids = []
        self._aws_security_group()
        self._aws_iam_role()
        self._aws_iam_instance_profile()
        self._aws_instance()
        self._aws_db_instance()
        self._aws_s3_bucket()
        self._aws_elasticache_cluster()
        return  self.tf_cloud_obj_list

    def get_infra_resources(self):
        self.tf_cloud_obj_list = []
        self.tf_cloud_sg_list = []
        self.resources_unique_ids = []
        self._get_vpc_list()
        self._aws_vpc()
        # self._aws_subnet()
        # self._aws_route_table()
        self.file_utils.print_json( self.tf_cloud_obj_list)
        return self.tf_cloud_obj_list

    def get_infra_resources2(self):
        self.tf_cloud_obj_list = []
        self.tf_cloud_sg_list = []
        self.resources_unique_ids = []
        self._get_vpc_list()
        self._aws_vpc()
        # self._aws_subnet()
        # self._aws_route_table()
        self.file_utils.print_json( self.tf_cloud_obj_list)
        return self.tf_cloud_obj_list

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
                if self.params.tenant_name == tenant_name_ec2 :
                    name = self.utils.getVal(tags, "Name")
                    instanceId = instance["InstanceId"]
                    key_name = instance["KeyName"]
                    if "Platform" in instance and instance["Platform"] == 'windows':
                        platform = instance["Platform"]
                        print(self.file_utils.stage_prefix(), "get_key_pair_list platform is ", platform, name )
                        #skip?
                    if key_name not in key_names:
                        aws_obj = {"name":name, "key_name":key_name, "instanceId":instanceId}
                        aws_objs.append(aws_obj)
                        key_names.append(key_name)
                        # self.file_utils.print_json(aws_obj)
        if len(aws_objs) ==0 :
            print(self.file_utils.stage_prefix(), "get_key_pair_list  :", "NOT_FOUND ANY")
        if self.debug_print_out:
            self.file_utils.print_json(aws_objs)
        return aws_objs


    ########## get_infra_resources START ##############################
    ########## get_infra_resources START ##############################
    ########## get_infra_resources START ##############################

    def _aws_vpc(self):
        awsclient = boto3.client('ec2')
        response = awsclient.describe_vpcs()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_vpc.json", response)
        aws_objs = []
        for instance in response["Vpcs"]:
            _id = instance['VpcId']
            is_default = instance['IsDefault']
            if is_default or self._is_default_vpc(_id) :
                self.tf_cloud_resource("aws_default_vpc", instance, tf_variable_id="aws-default-" + _id, tf_import_id= _id)
                print(self.file_utils.stage_prefix(), "aws_default_vpc :", _id)
            elif 'Tags' not in instance:
                self.tf_cloud_resource("aws_vpc", instance, tf_variable_id="aws-" + _id, tf_import_id= _id)
                print(self.file_utils.stage_prefix(), "aws_vpc :", _id)
            else:
                self.tf_cloud_resource("aws_vpc", instance, tf_variable_id="duplo-" + _id, tf_import_id= _id)
                print(self.file_utils.stage_prefix(), "aws_vpc :", _id)
            aws_objs.append(instance)
            awsobject = boto3.resource('ec2').Vpc(_id)

            # aws_default_network_acl
            # aws_default_route_table
            # aws_default_security_group
            # aws_default_subnet
            # aws_default_vpc
            # aws_default_vpc_dhcp_options

            ########  temp comment   ########
            internet_gateways = list(awsobject.internet_gateways.all())
            self._aws_internet_gateways(internet_gateways, is_default, instance)

            network_acls = list(awsobject.network_acls.all())
            self._aws_network_acls(network_acls, is_default, instance)

            network_interfaces = list(awsobject.network_interfaces.all())
            self._aws_network_interfaces(network_interfaces, is_default, instance)

            route_tables = list(awsobject.route_tables.all())
            self._aws_route_tables(route_tables, is_default, instance)

            security_groups = list(awsobject.security_groups.all())
            self._aws_security_groups(security_groups, is_default, instance)

            subnets = list(awsobject.subnets.all())
            self._aws_subnets(subnets, is_default, instance)
            ########  temp comment   ########

            # accepted_vpc_peering_connections = list(awsobject.accepted_vpc_peering_connections.all())
            # requested_vpc_peering_connections = list(awsobject.requested_vpc_peering_connections.all())

            # print("internet_gateways", internet_gateways)
            # accepted_vpc_peering_connections
            # instances
            # internet_gateways
            # network_acls
            # network_interfaces
            # requested_vpc_peering_connections
            # route_tables
            # security_groups
            # subnets

        if len(aws_objs) == 0:
            print(self.file_utils.stage_prefix(), "aws_vpc / aws_default_vpc :", "NOT_FOUND ANY")
        if self.debug_print_out:
            self.file_utils.print_json(aws_objs)
        return self

    def _aws_internet_gateways(self, objects, is_default, vpc):
        # terraform import aws_internet_gateway.gw igw-c0a643a9  === id
        for object in objects:
            _id = object.internet_gateway_id
            self.tf_cloud_resource("aws_internet_gateway", vpc, tf_variable_id=_id, tf_import_id=_id)
            print(self.file_utils.stage_prefix(), "aws_internet_gateway :", _id)


    def _aws_network_acls(self, objects, is_default, vpc):
        # terraform import aws_internet_gateway.gw igw-c0a643a9  === id
        for object in objects:
            _id = object.network_acl_id
            if is_default:
                self.tf_cloud_resource("aws_default_network_acl", vpc, tf_variable_id=_id, tf_import_id=_id)
                print(self.file_utils.stage_prefix(), "aws_default_network_acl :", _id)
            else:
                self.tf_cloud_resource("aws_network_acl", vpc, tf_variable_id=_id, tf_import_id=_id)
                print(self.file_utils.stage_prefix(), "aws_network_acl :", _id)

    def _aws_network_interfaces(self, objects, is_default, vpc):
        # terraform import aws_network_interface.gw igw-c0a643a9  === id
        for object in objects:
            _id = object.network_interface_id
            if _id == "eni-0b69e66c897740b0f":
                print("tf_import_id", _id)
            self.tf_cloud_resource("aws_network_interface", vpc, tf_variable_id=_id, tf_import_id=_id)
            print(self.file_utils.stage_prefix(), "aws_network_interface :", _id)

    def _aws_route_tables(self, objects, is_default, vpc):
        # terraform import aws_internet_gateway.gw igw-c0a643a9  === id
        for object in objects:
            _id = object.route_table_id
            if is_default:
                self.tf_cloud_resource("aws_default_route_table", vpc, tf_variable_id=_id, tf_import_id=_id)
                print(self.file_utils.stage_prefix(), "aws_default_route_table :", _id)
            else:
                self.tf_cloud_resource("aws_route_table", vpc, tf_variable_id=_id, tf_import_id=_id)
                print(self.file_utils.stage_prefix(), "aws_route_table :", _id)
            for route in object.routes:
                _cidr_block  = route.destination_cidr_block
                if _cidr_block is None:
                    _cidr_block = route.destination_ipv6_cidr_block
                _route_id="{}_{}".format(_id, _cidr_block)
                self.tf_cloud_resource("aws_route", vpc, tf_variable_id=_route_id, tf_import_id= _route_id)
                print(self.file_utils.stage_prefix(), "aws_route :", _route_id)
            # aws_objs.append(instance)

    def _aws_security_groups(self, objects, is_default, vpc):
        for object in objects:
            _id = object.group_id
            _name = object.group_name
            if not 'duplo' in _name : # skip will be handled by tenant
                if is_default:
                    self.tf_cloud_resource("aws_default_security_group", vpc, tf_variable_id=_name, tf_import_id=_id, skip_if_exists=True)
                    print(self.file_utils.stage_prefix(), "aws_security_group :", _id)
                else:
                    self.tf_cloud_resource("aws_security_group", vpc, tf_variable_id=_name, tf_import_id=_id, skip_if_exists=True)
                    print(self.file_utils.stage_prefix(), "aws_security_group :", _id)

    def _aws_subnets(self, objects, is_default, vpc):
        for object in objects:
            _id = object.subnet_id
            if is_default:
                self.tf_cloud_resource("aws_default_subnet", vpc, tf_variable_id=_id, tf_import_id=_id,
                                  skip_if_exists=True)
                print(self.file_utils.stage_prefix(), "aws_security_group :", _id)
            else:
                self.tf_cloud_resource("aws_subnet", vpc, tf_variable_id=_id, tf_import_id=_id,
                                  skip_if_exists=True)
                print(self.file_utils.stage_prefix(), "aws_security_group :", _id)

    ########## _aws_instances START ##############################
    ########## _aws_instances START ##############################
    ########## _aws_instances START ##############################

    def _aws_instances(self):
        awsclient = boto3.client('ec2')
        response = awsclient.describe_instances()
        if self.debug_json:
            self.file_utils.save_json_to_log("aws_instance._json", response)
        aws_objs=[]
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                if "Tags" not in instance:
                    continue
                tags = self.utils.getHashFromArray(instance["Tags"])
                tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
                if self.params.tenant_name == tenant_name_ec2 :
                    ######## aws_instance
                    name = self.utils.getVal(tags, "Name")
                    aws_name = instance['InstanceId']
                    self.tf_cloud_resource("aws_instance", instance, tf_variable_id=aws_name, tf_import_id=aws_name,
                                      skip_if_exists=True)
                    aws_objs.append(instance)
                    print(self.file_utils.stage_prefix(), "aws_instance :", tenant_name_ec2, name, aws_name)
                    ######## aws_key_pair
                    key_name = instance["KeyName"]
                    if self.create_key_pair:
                        self.tf_cloud_resource("aws_key_pair", instance, tf_variable_id=key_name, tf_import_id=key_name , skip_if_exists=True)
                    else:
                        print(self.file_utils.stage_prefix(), " : SKIP create aws_key_pair :", key_name, "as self.create_key_pair=", self.create_key_pair)
                    aws_objs.append(instance)
                    print(self.file_utils.stage_prefix(), "aws_key_pair :" , key_name)
        if len(aws_objs) ==0 :
            print(self.file_utils.stage_prefix(), "aws_instance :", "NOT_FOUND ANY")
        if self.debug_print_out:
            self.file_utils.print_json(aws_objs)
        return self
    ########## get_tenant_resources START ##############################
    ########## get_tenant_resources START ##############################
    ########## get_tenant_resources START ##############################
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
            if aws_name.startswith(self.tenant_prefix+"-"):
                self.tf_cloud_resource("aws_s3_bucket", instance, tf_variable_id=aws_name, tf_import_id=aws_name, skip_if_exists=True)
                aws_objs.append(instance)
                print(self.file_utils.stage_prefix(), "aws_s3_bucket :", instance['Name'])
            #todo: resolve tenant specific
        if len(aws_objs) ==0 :
            print(self.file_utils.stage_prefix(), "aws_s3_bucket :", "NOT_FOUND ANY")
        if self.debug_print_out:
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
            if tannant_id_instance == self.tenant_prefix:
                aws_name = instance['DBInstanceIdentifier']
                self.tf_cloud_resource("aws_db_instance", instance, tf_variable_id=aws_name, tf_import_id=aws_name,
                                  skip_if_exists=True)
                aws_objs.append(instance)
                print(self.file_utils.stage_prefix(), "aws_db_instance :", instance['DBInstanceIdentifier'], aws_name,  arn)
        if len(aws_objs) ==0 :
            print(self.file_utils.stage_prefix(), "aws_db_instance :", "NOT_FOUND ANY")
        if self.debug_print_out:
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
                if "Tags" not in instance:
                    continue
                tags = self.utils.getHashFromArray(instance["Tags"])
                tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
                if self.params.tenant_name == tenant_name_ec2 :
                    ######## aws_instance
                    name = self.utils.getVal(tags, "Name")
                    aws_name = instance['InstanceId']
                    self.tf_cloud_resource("aws_instance", instance, tf_variable_id=aws_name, tf_import_id=aws_name,
                                      skip_if_exists=True)
                    aws_objs.append(instance)
                    print(self.file_utils.stage_prefix(), "aws_instance :", tenant_name_ec2, name, aws_name)
                    ######## aws_key_pair
                    key_name = instance["KeyName"]
                    if self.create_key_pair:
                        self.tf_cloud_resource("aws_key_pair", instance, tf_variable_id=key_name, tf_import_id=key_name , skip_if_exists=True)
                    else:
                        print(self.file_utils.stage_prefix(), " : SKIP create aws_key_pair :", key_name, "as self.create_key_pair=", self.create_key_pair)
                    aws_objs.append(instance)
                    print(self.file_utils.stage_prefix(), "aws_key_pair :" , key_name)
        if len(aws_objs) ==0 :
            print(self.file_utils.stage_prefix(), "aws_instance :", "NOT_FOUND ANY")
        if self.debug_print_out:
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
            if self.tenant_prefix == name :
                self.tf_cloud_resource("aws_iam_role", instance, tf_variable_id=name, tf_import_id=name, skip_if_exists=True)
                arn = self.utils.getVal(instance, "Arn")
                print(self.file_utils.stage_prefix(), "aws_iam_role :" ,name, arn)
                aws_objs.append(instance)
                role = iam.Role(name)
                attached_policies =  list(role.attached_policies.all())
                policies = list(role.policies.all())
                for inline_policy in policies:
                    ip_name = inline_policy.name
                    ip_role_name =  inline_policy.role_name
                    ip_sync_id = "{0}:{1}".format(ip_role_name, ip_name)
                    ip_data = {'name':ip_name, 'role_name':ip_role_name }
                    self.tf_cloud_resource("aws_iam_role_policy", ip_data, tf_variable_id = ip_name, tf_import_id=ip_sync_id)
                    aws_objs.append(ip_data)
                    print(self.file_utils.stage_prefix(), "aws_iam_role_policy:", ip_role_name, ip_sync_id)
                for attached_policy in attached_policies:
                    arn = attached_policy.arn
                    policy_name = arn.split("/").pop()
                    sync_id="{0}/{1}".format(name, arn)
                    data = {'PolicyName': policy_name, 'RoleName': name, 'arn': arn}
                    self.tf_cloud_resource("aws_iam_role_policy_attachment", data, tf_variable_id=policy_name, tf_import_id=sync_id)
                    aws_objs.append(data)
                    print(self.file_utils.stage_prefix(), "aws_iam_role_policy_attachment :", policy_name, sync_id)
        if len(aws_objs) ==0 :
            print(self.self.file_utils.stage_prefix(), "aws_iam_role, aws_iam_role_policy, aws_iam_role_policy_attachment :", "NOT_FOUND ANY")
        if self.debug_print_out:
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
            if  group_name == self.tenant_prefix or group_name.startswith(self.tenant_prefix+"-"):
                self.tf_cloud_resource("aws_security_group", instance, tf_variable_id=group_name, tf_import_id=group_id,  skip_if_exists=True)
                print(self.file_utils.stage_prefix(), "aws_security_group :" ,group_name, group_id)
                aws_objs.append(instance)
        if len(aws_objs) ==0 :
            print(self.file_utils.stage_prefix(), "aws_security_group :", "NOT_FOUND ANY")
        if self.debug_print_out:
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
            if  InstanceProfileName == self.tenant_prefix  :
                aws_name = instance['InstanceProfileName']
                self.tf_cloud_resource("aws_iam_instance_profile", instance, tf_variable_id=aws_name, tf_import_id=aws_name,
                                  skip_if_exists=True)
                print(self.file_utils.stage_prefix(), "aws_iam_instance_profile :" , InstanceProfileName, InstanceProfileId)
                aws_objs.append(instance)
        if len(aws_objs) ==0 :
            print(self.file_utils.stage_prefix(), "aws_iam_instance_profile :", "NOT_FOUND ANY")
        if self.debug_print_out:
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
                    self.tf_cloud_resource("aws_elasticache_cluster", instance, tf_variable_id=cacheClusterId, tf_import_id=cacheClusterId,  skip_if_exists=True )
                    print(self.file_utils.stage_prefix(), "aws_elasticache_cluster :", cacheClusterId)
        if len(aws_objs) ==0 :
            print(self.file_utils.stage_prefix(), "aws_iam_instance_profile :", "NOT_FOUND ANY")
        if self.debug_print_out:
            self.file_utils.print_json(aws_objs)
        return self


    ########## get_tenant_resources  END ##############################
    ########## get_tenant_resources  END ##############################
    ########## get_tenant_resources  END ##############################


    ############ get default vpc ##########

    def _get_vpc_list(self):
        if len(self.aws_vpc_list) > 0:
            return self.aws_vpc_list
        awsclient = boto3.client('ec2')
        response = awsclient.describe_vpcs()
        for instance in response["Vpcs"]:
            _id = instance['VpcId']
            is_default = instance['IsDefault']
            if is_default:
                self.aws_vpc_list["default"] = _id
                self.aws_vpc_list[_id] = "default"
            else:
                self.aws_vpc_list[_id] = "duplo"
        return self.aws_vpc_list

    def _is_default_vpc(self, vpcId):
        return self.aws_vpc_list["default"] == vpcId

    def _get_vpc(self, vpcId):
        return self.aws_vpc_list[vpcId]


    ############ verify if object has securityGroup from tenant ##########

    def _get_aws_security_groups_for_tenant(self):
        if len(self.tf_cloud_sg_list) > 0:
            return self.tf_cloud_sg_list
        awsclient = boto3.client('ec2')
        response = awsclient.describe_security_groups()
        for instance in response["SecurityGroups"]:
            group_name = self.utils.getVal(instance, "GroupName")
            if group_name == self.tenant_prefix or group_name.startswith(self.tenant_prefix + "-"):
                self.tf_cloud_sg_list.append(instance)
        return self.tf_cloud_sg_list

    def _is_security_group_from_tenant(self, sg_group_id):
        self.aws_sg_objs = self._get_aws_security_groups_for_tenant()
        for instance in self.aws_sg_objs:
            group_id = self.utils.getVal(instance, "GroupId")
            if group_id == sg_group_id:
                return True
        return False

    ############ mapping_cloud_keys_to_tf_keys = sync_ids and names ##########


