import json
import random
from datetime import datetime
# import datetime
from collections import defaultdict
import os
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.sql import SqlManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from haikunator import Haikunator
from stringcase import pascalcase, snakecase

from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.providers.azurerm.tf_step_const import *

class AzureTfStepHelper:
    resources_tf_unique_ids = {}
    cloud_obj_list = []
    resources_unique_ids = []

    def __init__(self, params):
        try:

            random.seed(datetime.now())
            self.params = params
            self.utils = TfUtils(params)
            self.file_utils = TfFileUtils(params, step=params.step, step_type=params.step_type)
        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:Helper: __init__ {0}".format(e))
            print("ERROR:Helper:", "__init__", e)

    def _parse_id_metadata(self, tf_import_id):
        res_metadata={}
        try:
            tf_import_id_arr = tf_import_id.split("/")
            new_id_arr = tf_import_id_arr[1:5]
            new_id_temp = "/".join(new_id_arr)
            tf_import_id_new = "/{0}".format(new_id_temp)
            res_name = tf_import_id_arr[4].lower().strip()
            res_metadata["resource_group_name"] = res_name
            res_metadata["resource_group_id"] = tf_import_id_new
            res_metadata["resource_name"] = tf_import_id_arr[-1]
            for i in range(1,len(tf_import_id_arr),2):
                key = tf_import_id_arr[i]
                val = tf_import_id_arr[i+1]
                res_metadata[key] = val
                #if i > 5:
                res_metadata["key_{0}".format(i)] = key
                res_metadata["val_{0}".format(i)] = val


        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:Helper: _parse_id_metadata {0}".format(e))
            print("ERROR:Helper:", "_parse_id_metadata", e)
        return res_metadata

    def _get_unique_sub_src_name(self, id, name):
        random.seed(datetime.now())
        rndint= random.randint(10, 9999)
        id_metadata = self._parse_id_metadata(id)
        res_grp_name = "s{0}".format(rndint) #id_metadata["resourceGroups"].replace("_","").replace("-","")
        var_name = "{0}-{1}".format(res_grp_name, name)

        return var_name

    def set_cloud_obj_list(self, cloud_obj_list):
        self.cloud_obj_list = cloud_obj_list
        self.resources_unique_ids = self._resources_unique_ids(cloud_obj_list)
        # self.resources_tf_unique_ids = []

    def _resources_unique_ids(self, cloud_obj_list=[]):
        resources_unique_ids = []
        for tf_resource in cloud_obj_list:
            tf_id = tf_resource["tf_id"]
            resources_unique_ids.append(tf_id)
            self.resources_tf_unique_ids.append(tf_id)
        return resources_unique_ids

    def tf_cloud_resource(self, tf_resource_type, tf_cloud_obj, tf_variable_id=None, tf_import_id=None,
                          skip_if_exists=False):
        # TODO: move totally to helper
        tf_resource = self._tf_cloud_resource(tf_resource_type, tf_cloud_obj, tf_variable_id, tf_import_id,
                                                     skip_if_exists)
        if tf_resource:
            tf_resource_var_name = tf_resource["tf_variable_id"]
            tf_resource_type = tf_resource["tf_import_id"]
            tf_id = tf_resource["tf_id"]

            if tf_id in self.resources_unique_ids:
                if skip_if_exists:
                    # print(self.file_utils.stage_prefix(),
                    #       "SKIP: already exists - tf_resource_var_name should be unique : {0} {1} {2}".format(
                    #           tf_resource_type, tf_resource_var_name, tf_id))
                    return
                print(self.file_utils.stage_prefix(),
                      "Exception tf_resource_var_name should be unique : {0} {1} {2}".format(
                          tf_resource_type, tf_resource_var_name, tf_id))
                raise Exception("tf_resource_var_name should be unique {}".format(tf_id))

            # create array
            self.cloud_obj_list.append(tf_resource)
            self.resources_unique_ids.append(tf_id)
            return tf_resource

    def _tf_cloud_resource(self, tf_resource_type, tf_cloud_obj, tf_variable_id, tf_import_id,
                           skip_if_exists):
        if tf_variable_id[0].isdigit():
            tf_variable_id = "s-{0}".format(tf_variable_id)
        if tf_resource_type in ["azurerm_subnet", "azurerm_lb_backend_address_pool", "azurerm_public_ip"]:
            #subnet names not usnique across res group or vnet?
            if tf_import_id not in self.resources_tf_unique_ids:
                tf_variable_id =  self._get_unique_sub_src_name(tf_import_id, tf_variable_id)
                self.resources_tf_unique_ids[tf_import_id]="{0}.{1}.name".format(tf_resource_type, tf_variable_id)
            else:
                #alread in
                return
        tf_resource_var_name = tf_variable_id
        tf_resource_type_sync_id = tf_import_id
        if tf_resource_var_name is None or tf_resource_type_sync_id is None:
            print("tf_cloud_resource 'tf_variable_id' 'tf_import_id' must be provided", tf_resource_type,
                  tf_resource_var_name, tf_import_id)
            raise Exception("tf_cloud_resource 'tf_variable_id' 'tf_import_id' must be provided")

        tf_resource_type = tf_resource_type.strip()
        tf_resource_type_sync_id = tf_resource_type_sync_id.strip()
        tf_resource_var_name = tf_resource_var_name.lower().strip()
        tf_resource_var_name = tf_resource_var_name.replace(".", "-").replace("/", "-"). \
            replace(" ", "-").replace("(", "-").replace(")", "-").replace("--", "-")
        tf_id = "{}.{}".format(tf_resource_type, tf_resource_var_name)

        # if tf_id in self.resources_unique_ids:
        #     if skip_if_exists:
        #         # print(self.file_utils.stage_prefix(),
        #         #       "SKIP: already exists - tf_resource_var_name should be unique : {0} {1} {2}".format(
        #         #           tf_resource_type, tf_resource_var_name, tf_id))
        #         return
        #     print(self.file_utils.stage_prefix(),
        #           "Exception tf_resource_var_name should be unique : {0} {1} {2}".format(
        #               tf_resource_type, tf_resource_var_name, tf_id))
        #     raise Exception("tf_resource_var_name should be unique {}".format(tf_id))

        # create array
        tf_resource = {"tf_resource_type": tf_resource_type, "tf_variable_id": tf_resource_var_name,
                       "tf_import_id": tf_resource_type_sync_id,
                       "tf_id": tf_id,
                       "module": self.file_utils.params.module}
        return tf_resource