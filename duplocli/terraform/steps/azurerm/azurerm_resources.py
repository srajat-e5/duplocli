import json
import datetime
from collections import defaultdict
import os
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from haikunator import Haikunator
from stringcase import pascalcase, snakecase

from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.resources.base_resources import BaseResources


class AzurermResources:
    debug_print_out = False
    debug_json = True
    create_key_pair = False
    #
    aws_vpc_list = {}
    #
    tf_cloud_obj_list = []
    tf_cloud_sg_list = []
    resources_unique_ids = []

    def __init__(self, params):
        self.params = params
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params, step=params.step, step_type=params.step_type)
        self.tenant_prefix = self.utils.get_tenant_id(params.tenant_name)

    #### public methods #######

    def get_tenant_resources(self):
        ##
        return self.tf_cloud_obj_list

    def get_infra_resources(self):
         ##
        return self.tf_cloud_obj_list

    def get_tenant_key_pair_list(self):
        return None

    ########### helpers ###########
    def tf_cloud_resource(self, tf_resource_type, tf_cloud_obj, tf_variable_id=None, tf_import_id=None,
                          skip_if_exists=False):
        tf_resource_var_name = tf_variable_id
        tf_resource_type_sync_id = tf_import_id
        if tf_resource_var_name is None or tf_resource_type_sync_id is None:
            raise Exception("tf_cloud_resource 'tf_variable_id' 'tf_import_id' must be provided")
        # self.file_utils.print_json(tf_cloud_obj)
        tf_resource_type = tf_resource_type.strip()
        tf_resource_type_sync_id = tf_resource_type_sync_id.strip()
        tf_resource_var_name = tf_resource_var_name.strip()
        tf_resource_var_name = tf_resource_var_name.replace(".", "-").replace("/", "-")
        tf_id = "{}.{}".format(tf_resource_type, tf_resource_var_name)
        if tf_id in self.resources_unique_ids:
            if skip_if_exists:
                print(self.file_utils.stage_prefix(),
                      "SKIP: already exists - tf_resource_var_name should be unique : {0} {1} {2}".format(
                          tf_resource_type, tf_resource_var_name, tf_id))
                return
            raise Exception("tf_resource_var_name should be unique {}".format(tf_id))
        # create array
        tf_resource = {"tf_resource_type": tf_resource_type, "tf_variable_id": tf_resource_var_name,
                       "tf_import_id": tf_resource_type_sync_id,
                       "module": self.file_utils.params.module}
        self.tf_cloud_obj_list.append(tf_resource)
        self.resources_unique_ids.append(tf_id)
        return tf_resource



def get_all_resources():


    subscription_id = os.environ.get(
        'AZURE_SUBSCRIPTION_ID',
        '11111111-1111-1111-1111-111111111111')  # your Azure Subscription Id
    credentials = ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'],
        secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant=os.environ['AZURE_TENANT_ID']
    )


    resource_client = ResourceManagementClient(credentials, subscription_id)
    compute_client = ComputeManagementClient(credentials, subscription_id)
    storage_client = StorageManagementClient(credentials, subscription_id)
    network_client = NetworkManagementClient(credentials, subscription_id)

    ###########
    # Prepare #
    ###########
    # for vm in compute_client.virtual_machines.list_all():
    #     print("\tVM: {}".format(vm.name))
    #
    # # for vm in resource_client.resources.list():
    # #     print("\t  '{}':'{}'   ,".format(vm.name, vm.id.split("/")))
    # #
    #
    #
    #
    # lsrsrc = resource_client.resources.list_by_resource_group("duploservices-azdemo1")
    # print(lsrsrc)
    #
    # for vm in lsrsrc:
    #     # print("\t{}: {}  {}  {}  {}".format(vm.type, vm.name, vm.kind, vm.sku ,vm    ) )
    #     print("\t  '{}':'{}'   ,".format(  vm.name, vm.id.split("/")))
    #
    # print(lsrsrc)


    # for vm in resource_client.resources.list():
    #     print("\t  '{}':'{}'   ,".format(vm.name, vm.id.split("/")))
    #

    resourceGroups = {}
    print("======================================================")
    for vm in resource_client.resources.list():
        print(vm.id)
    print("======================================================")

    for vm in resource_client.resources.list():
        arr = (vm.id  ).split("/")
        arr.pop(0)
        count = len(arr)
        print(vm.id)
        resource = {'id':vm.id}
        for i in range(0, count, 2):
            key = arr[i]
            if count > i+1:
                value = arr[i+1 ]
            else:
                value =""
            resource[key] = value
            if value == vm.name:
                resource["providerApiName"] = key
                resource["providerApiValue"] = value
                resource["providerApiValueSnake"] = snakecase(key)

                resource["name"] = vm.name
            # print(i, i + 1, key, "=", value)
        if  'resourceGroups'  in resource.keys():
            resourceGroupsKey = resource['resourceGroups']
            if not resourceGroupsKey in resourceGroups.keys():
                resourceGroups[resourceGroupsKey] = []
            # print("INVALID '{}': {} {}    ,".format(vm.name, resource.keys(), resource))
            resourceGroups[resourceGroupsKey].append(resource)
        else:
            print("INVALID '{}': {}    ,".format(vm.name, resource))
        print("'{}': {}    ,".format(vm.name, resource ))

    print("resources" )
    print("{}".format(resourceGroups))

    getResourceGroups(resourceGroups)
    jsonStr = json.dumps(resourceGroups)
    print(jsonStr)

def getResourceGroups(resourceGroups):
    for key in resourceGroups.keys():
        print("'{}': {}    ,".format(key, len(resourceGroups[key]) ))
        for resourceGroup in resourceGroups[key]:
            if 'name' in resourceGroup.keys():
                print(" {} : {}/{}/{}   ,".format(resourceGroup['name'],  resourceGroup['providers'],  resourceGroup['providerApiName'],  resourceGroup['providerApiValue'] ))
            else:
             print("name???? {}  ,".format(resourceGroup ))
    print(   resourceGroups.keys() )
    return resourceGroups.keys()


if __name__ == "__main__":
    # os.environ['AZURE_SUBSCRIPTION_ID'] = ""
    # os.environ['AZURE_TENANT_ID'] = ""
    # os.environ['AZURE_CLIENT_ID'] = ""
    # os.environ['AZURE_CLIENT_SECRET'] = ""

    # os.system('bash /Users/brighu/_go/azure.sh ')
    get_all_resources()

