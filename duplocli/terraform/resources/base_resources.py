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


class BaseResources:
    #
    tf_cloud_obj_list = []
    tf_cloud_sg_list = []
    resources_unique_ids =[]

    def __init__(self, params):
        self.params = params
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params, step=params.step, step_type=params.step_type)


    ########### helpers ###########
    def tf_cloud_resource(self, tf_resource_type, tf_cloud_obj, tf_variable_id=None, tf_import_id=None , skip_if_exists=False):
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



