import boto3
import json
# from bson importtf json_util
import datetime
from collections import defaultdict
# src/tenant_import/aws/aws_tf_import_step1.py
from tenant_import_to_tf.aws.step1.aws_to_tf_util_step1 import AwsToTfUtilStep1
from tenant_import_to_tf.aws.common.tf_utils import TfUtils

class AwsTfImportStep1:

    def __init__(self, step="step1"):
        self.utils = TfUtils()
        self.tf_util = AwsToTfUtilStep1()
        self.step = step

    def create_state(self):
        self.tf_util.create_state()

    def aws_elasticache_cluster(self, tenant_name):
        tenant_id = self.utils.get_tenant_id(tenant_name)
        awsclient = boto3.client('elasticache')
        response = awsclient.describe_cache_clusters()
        self.utils.save_json_to_log("aws_elasticache_cluster.json", response, self.step)
        aws_obj_list=[]
        for instance in response["CacheClusters"]:
            self.tf_util.aws_elasticache_cluster(instance)
            #todo: resolve tenant specific
            # tags = self.utils.getHashFromArray(instance["Tags"])
            # # print_json(tags)
            # tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
            # tenant_ec2_name = self.utils.getVal(tags, "Name")
            # # print(tenant_name_ec2)
            # if tenant_name == tenant_name_ec2 :
            #     name = self.utils.getVal(tags, "Name")
            #     self.tf_util.aws_instance(instance, name)
            #     #debug
            #     tenant_ec2_list.append(instance)
            #     print(tenant_name_ec2, name)
        return aws_obj_list
    def aws_s3_bucket(self, tenant_name):
        tenant_id = self.utils.get_tenant_id(tenant_name)
        awsclient = boto3.client('s3')
        response = awsclient.list_buckets()
        self.utils.save_json_to_log("aws_s3_bucket.json", response, self.step)
        aws_obj_list=[]
        for instance in response["Buckets"]:
            # pass
            # bucket = awsclient.get_bucket(instance['Name'], validate=False)
            # print(json.dumps(instance))
            #todoL: fetch security_group id name
            #if instance['Name'] !="cf-templates-n3v0h2x4m8ny-us-west-2":
            self.tf_util.aws_s3_bucket(instance)
            #todo: resolve tenant specific
            # tags = self.utils.getHashFromArray(instance["Tags"])
            # # print_json(tags)
            # tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
            # tenant_ec2_name = self.utils.getVal(tags, "Name")
            # # print(tenant_name_ec2)
            # if tenant_name == tenant_name_ec2 :
            #     name = self.utils.getVal(tags, "Name")
            #     self.tf_util.aws_instance(instance, name)
            #     #debug
            #     tenant_ec2_list.append(instance)
            #     print(tenant_name_ec2, name)
        return aws_obj_list

    def aws_db_instance(self, tenant_name):
        tenant_id = self.utils.get_tenant_id(tenant_name)
        awsclient = boto3.client('rds')
        response = awsclient.describe_db_instances()
        self.utils.save_json_to_log("aws_db_instance.json", response, self.step)
        aws_obj_list=[]
        for instance in response["DBInstances"]:
            #todo: fetch security_group id name
            self.tf_util.aws_db_instance(instance)
            #todo: resolve tenant specific
            # tags = self.utils.getHashFromArray(instance["Tags"])
            # # print_json(tags)
            # tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
            # tenant_ec2_name = self.utils.getVal(tags, "Name")
            # # print(tenant_name_ec2)
            # if tenant_name == tenant_name_ec2 :
            #     name = self.utils.getVal(tags, "Name")
            #     self.tf_util.aws_instance(instance, name)
            #     #debug
            #     tenant_ec2_list.append(instance)
            #     print(tenant_name_ec2, name)
        return aws_obj_list

    def aws_instance(self, tenant_name):
        tenant_id = self.utils.get_tenant_id(tenant_name)
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances()
        self.utils.save_json_to_log("aws_instance.json", response, self.step)
        tenant_ec2_list=[]
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                tags = self.utils.getHashFromArray(instance["Tags"])
                # print_json(tags)
                tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
                tenant_ec2_name = self.utils.getVal(tags, "Name")
                # print(tenant_name_ec2)
                if tenant_name == tenant_name_ec2 :
                    name = self.utils.getVal(tags, "Name")
                    self.tf_util.aws_instance(instance, name)
                    #debug
                    tenant_ec2_list.append(instance)
                    print(tenant_name_ec2, name)
        return tenant_ec2_list

    def aws_iam_role(self, tenant_name):
        tenant_id = self.utils.get_tenant_id(tenant_name)
        ec2 = boto3.client('iam')
        response = ec2.list_roles()
        self.utils.save_json_to_log("aws_iam_role.json", response, self.step)
        tenant_roles_list=[]
        for instance in response["Roles"]:
            name = self.utils.getVal(instance, "RoleName")
            if tenant_id == name :
                self.tf_util.aws_iam_role(instance)
                #debug
                tenant_roles_list.append(instance)
                arn = self.utils.getVal(instance, "Arn")
                print( name, arn)
        return tenant_roles_list

    def aws_security_group(self, tenant_name):
        tenant_id = self.utils.get_tenant_id(tenant_name)
        ec2 = boto3.client('ec2')
        response = ec2.describe_security_groups()
        self.utils.save_json_to_log("aws_security_group.json", response, self.step)
        tenant_sg_list = defaultdict(self.utils.def_value)
        for instance in response["SecurityGroups"]:
            group_name = self.utils.getVal(instance, "GroupName")
            group_id = self.utils.getVal(instance, "GroupId")
            # print( "1", group_name, group_id)
            if  group_name == tenant_id or group_name.startswith(tenant_id+"-"):
                self.tf_util.aws_security_group(instance)
                #debug
                tenant_sg_list[group_name] = instance
                print(group_name, group_id)
        return tenant_sg_list

    def aws_iam_instance_profile(self, tenant_name):
        tenant_id = self.utils.get_tenant_id(tenant_name)
        ec2 = boto3.client('iam')
        response = ec2.list_instance_profiles()
        self.utils.save_json_to_log("aws_iam_instance_profile.json", response, self.step)
        tenant_instance_profile_list = defaultdict(self.utils.def_value)
        for instance in response["InstanceProfiles"]:
            # print(instance)
            InstanceProfileName = self.utils.getVal(instance, "InstanceProfileName")
            InstanceProfileId = self.utils.getVal(instance, "InstanceProfileId")
            if  InstanceProfileName == tenant_id  :
                self.tf_util.aws_iam_instance_profile(instance)
                #debug
                tenant_instance_profile_list[InstanceProfileName] = instance
                print(InstanceProfileName, InstanceProfileId)
        return tenant_instance_profile_list



######## ####
def main(tenant_name="bigdata01"):
    tenant = AwsTfImportStep1()
    # ## ec2
    # tenant_ec2_list = tenant.get_tenant_ec2(tenant_name)
    # # tenant.print_json(tenant_ec2_list)
    # # ## vpc
    # tenant_vpc_list = tenant.get_tenant_vpcs(tenant_name)
    # # tenant.print_json(tenant_vpc_list)
    # # ## vpc
    # tenant_subnet_list = tenant.get_tenant_subnets(tenant_name)
    # # tenant.print_json(tenant_subnet_list)
    # # ## igw
    # tenant_route_tables_list = tenant.get_tenant_route_tables(tenant_name)
    # # tenant.print_json(tenant_route_tables_list)
    # # ## igw
    # tenant_az_list = tenant.get_tenant_azs(tenant_name)
    # # tenant.print_json(tenant_az_list)

    #we only need to create a tenant initially (above not needed)

    # ## sg
    aws_security_group = tenant.aws_security_group(tenant_name)
    # tenant.utils.print_json(aws_security_group)

    # ## roles
    aws_iam_roles = tenant.aws_iam_role(tenant_name)
    # tenant.utils.print_json(aws_iam_roles)

    # ## instance_profile
    aws_iam_instance_profiles = tenant.aws_iam_instance_profile(tenant_name)
    # tenant.utils.print_json(aws_iam_instance_profiles)

    ########### new ####################
    # ## aws_instance
    aws_aws_instances = tenant.aws_instance(tenant_name)
    # tenant.utils.print_json(aws_aws_instances)

    # ## aws_db_instance
    aws_db_instances = tenant.aws_db_instance(tenant_name)
    # tenant.utils.print_json(aws_db_instances)

    # ## aws_s3_bucket
    aws_s3_buckets = tenant.aws_s3_bucket(tenant_name)
    # tenant.utils.print_json(aws_s3_buckets)

    # ## aws_elasticache_cluster
    aws_elasticache_clusters = tenant.aws_elasticache_cluster(tenant_name)
    # tenant.utils.print_json(aws_elasticache_clusters)



    tenant.create_state()

if __name__ == '__main__':
    main()
    ######## ####
