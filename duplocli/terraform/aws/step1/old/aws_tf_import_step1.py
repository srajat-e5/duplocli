# import boto3
# import json
# # from bson importtf json_util
# import datetime
# from collections import defaultdict
# # src/tenant_import/aws/aws_tf_import_step1.py
# from duplocli.terraform.aws.common.tf_utils import TfUtils
# from duplocli.terraform.aws.step1.aws_to_tf_util_step1 import AwsToTfUtilStep1
#
# class AwsTfImportStep1:
#
#     step = "step1"
#     debug = False
#
#     def __init__(self, tenant_name="bigdata01", aws_az="us-west-2"):
#         self.utils = TfUtils()
#         self.aws_az = aws_az
#         self.tenant_name = tenant_name
#         self.tenant_id = self.utils.get_tenant_id(tenant_name)
#         self.tf_util = AwsToTfUtilStep1( tenant_name=tenant_name, aws_az=aws_az) #could be options={}
#
#     def execute_step(self):
#         self.aws_security_group()
#         self.aws_iam_role()
#         self.aws_iam_instance_profile()
#         self.aws_instance()
#         self.aws_db_instance()
#         self.aws_s3_bucket()
#         self.aws_elasticache_cluster()
#         self.create_state()
#
#     ###########
#     def create_state(self):
#         self.tf_util.create_state()
#
#     def aws_elasticache_cluster(self):
#         awsclient = boto3.client('elasticache')
#         response = awsclient.describe_cache_clusters()
#         if self.debug:
#             self.utils.save_json_to_log("aws_elasticache_cluster.json", response, self.step)
#         aws_obj_list=[]
#         for instance in response["CacheClusters"]:
#             self.tf_util.aws_elasticache_cluster(instance)
#             #todo: resolve tenant specific
#
#         if self.debug:
#             self.utils.print_json(aws_obj_list)
#         return self
#
#     def aws_s3_bucket(self):
#         awsclient = boto3.client('s3')
#         response = awsclient.list_buckets()
#         if self.debug:
#             self.utils.save_json_to_log("aws_s3_bucket.json", response, self.step)
#         aws_obj_list=[]
#         for instance in response["Buckets"]:
#             # pass
#             aws_name=instance['Name']
#             if aws_name.startswith(self.tenant_id+"-"):
#                 self.tf_util.aws_s3_bucket(instance)
#                 aws_obj_list.append(instance)
#                 print("**** aws import : aws_s3_bucket ", instance['Name'])
#             #todo: resolve tenant specific
#         if len(aws_obj_list) ==0 :
#             print("**** aws import : aws_s3_bucket ", "NOT_FOUND ANY")
#         if self.debug:
#             self.utils.print_json(aws_obj_list)
#         return self
#
#     def aws_db_instance(self):
#         awsclient = boto3.client('rds')
#         response = awsclient.describe_db_instances()
#         if self.debug:
#             self.utils.save_json_to_log("aws_db_instance.json", response, self.step)
#         aws_obj_list=[]
#         for instance in response["DBInstances"]:
#             arn = instance['DBInstanceArn']
#             tags = awsclient.list_tags_for_resource(ResourceName=arn)
#             tags_dict = self.utils.getHashFromArray(tags['TagList'])
#             tannant_id_instance = self.utils.getVal(tags_dict, "Name")
#             if tannant_id_instance == self.tenant_id:
#                 self.tf_util.aws_db_instance(instance)
#                 aws_obj_list.append(instance)
#                 print("**** aws import : aws_db_instance", instance['DBInstanceIdentifier'], arn)
#             #todo: resolve tenant specific
#         if len(aws_obj_list) ==0 :
#             print("**** aws import : aws_db_instance ", "NOT_FOUND ANY")
#         if self.debug:
#             self.utils.print_json(aws_obj_list)
#         return self
#
#     def aws_instance(self):
#         awsclient = boto3.client('ec2')
#         response = awsclient.describe_instances()
#         if self.debug:
#             self.utils.save_json_to_log("aws_instance.json", response, self.step)
#         aws_obj_list=[]
#         for reservation in response["Reservations"]:
#             for instance in reservation["Instances"]:
#                 tags = self.utils.getHashFromArray(instance["Tags"])
#                 tenant_name_ec2 =  self.utils.getVal(tags, "TENANT_NAME")
#                 if self.tenant_name == tenant_name_ec2 :
#                     name = self.utils.getVal(tags, "Name")
#                     self.tf_util.aws_instance(instance, name)
#                     aws_obj_list.append(instance)
#                     print("**** aws import : aws_instance " ,tenant_name_ec2, name)
#         if len(aws_obj_list) ==0 :
#             print("**** aws import : aws_instance ", "NOT_FOUND ANY")
#         if self.debug:
#             self.utils.print_json(aws_obj_list)
#         return self
#
#     def aws_iam_role(self):
#         awsclient = boto3.client('iam')
#         response = awsclient.list_roles()
#         if self.debug:
#             self.utils.save_json_to_log("aws_iam_role.json", response, self.step)
#         aws_obj_list=[]
#         for instance in response["Roles"]:
#             name = self.utils.getVal(instance, "RoleName")
#             if self.tenant_id == name :
#                 self.tf_util.aws_iam_role(instance)
#                 arn = self.utils.getVal(instance, "Arn")
#                 print("**** aws import : aws_iam_role " ,name, arn)
#                 aws_obj_list.append(instance)
#         if len(aws_obj_list) ==0 :
#             print("**** aws import : aws_iam_role ", "NOT_FOUND ANY")
#         if self.debug:
#             self.utils.print_json(aws_obj_list)
#         return self
#
#     def aws_security_group(self):
#         awsclient = boto3.client('ec2')
#         response = awsclient.describe_security_groups()
#         if self.debug:
#             self.utils.save_json_to_log("aws_security_group.json", response, self.step)
#         aws_obj_list = defaultdict(self.utils.def_value)
#         for instance in response["SecurityGroups"]:
#             group_name = self.utils.getVal(instance, "GroupName")
#             group_id = self.utils.getVal(instance, "GroupId")
#             # print( "1", group_name, group_id)
#             if  group_name == self.tenant_id or group_name.startswith(self.tenant_id+"-"):
#                 self.tf_util.aws_security_group(instance)
#                 print("**** aws import : aws_security_group " ,group_name, group_id)
#                 aws_obj_list[group_name] = instance
#         if len(aws_obj_list) ==0 :
#             print("**** aws import : aws_security_group ", "NOT_FOUND ANY")
#         if self.debug:
#             self.utils.print_json(aws_obj_list)
#         return self
#
#     def aws_iam_instance_profile(self):
#         awsclient = boto3.client('iam')
#         response = awsclient.list_instance_profiles()
#         if self.debug:
#             self.utils.save_json_to_log("aws_iam_instance_profile.json", response, self.step)
#         aws_obj_list = defaultdict(self.utils.def_value)
#         for instance in response["InstanceProfiles"]:
#             # print(instance)
#             InstanceProfileName = self.utils.getVal(instance, "InstanceProfileName")
#             InstanceProfileId = self.utils.getVal(instance, "InstanceProfileId")
#             if  InstanceProfileName == self.tenant_id  :
#                 self.tf_util.aws_iam_instance_profile(instance)
#                 print("**** aws import : aws_iam_instance_profile " , InstanceProfileName, InstanceProfileId)
#                 aws_obj_list[InstanceProfileName] = instance
#         if len(aws_obj_list) ==0 :
#             print("**** aws import : aws_iam_instance_profile ", "NOT_FOUND ANY")
#         if self.debug:
#             self.utils.print_json(aws_obj_list)
#         return self
#
# # if __name__ == '__main__':
#     # utils = TfUtils()
#     # awsclient = boto3.client('rds')
#     # response = awsclient.describe_db_instances()
#     # # utils.print_json(response)
#     # aws_obj_list = []
#     # for instance in response["DBInstances"]:
#     #     # todo: fetch security_group id name
#     #     # name = instance['DBInstanceIdentifier']
#     #     arn = instance['DBInstanceArn']
#     #     # arn:aws:rds:ap-southeast-1::db:mydbrafalmarguzewicz
#     #     tags = awsclient.list_tags_for_resource(ResourceName=arn)
#     #     tags_dict = utils.getHashFromArray(tags['TagList'])
#     #     utils.print_json(tags_dict)
#     #     print("**** aws import : aws_db_instance", instance['DBInstanceIdentifier'])
#     #     # todo: resolve tenant specific
