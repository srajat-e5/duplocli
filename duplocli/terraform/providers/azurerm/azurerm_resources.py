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


class AzureResource:
    def __init__(self, res):
        self.id = res.id
        self.name = res.name
        self._getType(res)

    def _getType(self, res):
        if "/" in res.type:
            arr = res.type.split("/")
            type_camel = arr[-1]
        else:
            type_camel = res.type
        self.type_name = "azurerm_{0}".format(snakecase(type_camel))
        if self.type_name == "azurerm_public_i_p_addresses":
            self.type_name = "azurerm_public_ip"

        self.type_name_singular = self.type_name[:-1]


#azurerm_metricalerts
azure_resoure_map = {
    "azurerm_route_tables": "azurerm_route_table",
    "azurerm_user_assigned_identities": "azurerm_user_assigned_identity",

    "azurerm_public_ip_addresses": "azurerm_public_ip",
    "azurerm_public_i_p_addresses": "azurerm_public_ip",

    "azurerm_metricalerts": "azurerm_monitor_metric_alert",
    "azurerm_disks": "azurerm_managed_disk",
    "azurerm_extensions": "azurerm_virtual_machine_extension",
    "azurerm_virtual_network_links": "azurerm_private_dns_zone_virtual_network_link",
    "azurerm_galleries": "azurerm_shared_image_gallery",

    "azurerm_hosting_environments": "azurerm_app_service_environment",
    "azurerm_server_farms": "",
    "azurerm_sites": "",
    "azurerm_load_balancers": "",

}
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

    resources_skip= [
        "azurerm_application_gateway",
        "azurerm_network_interface",
        "azurerm_network_security_group",
        "azurerm_route_table",
        'azurerm_image' #some bug in azurerm ---  test016122019 not accepting required === "hyper_v_generation": "V1" or "V2" or ""
    ]

    resources_proess = [
        'azurerm_storage_account',
        #'azurerm_image',
        'azurerm_snapshot',
        'azurerm_automation_account',
        'azurerm_virtual_machine',
        'azurerm_local_network_gateway',
        'azurerm_public_ip',
        'azurerm_virtual_network_gateway',
        'azurerm_virtual_network',
        'azurerm_availability_set',
        'azurerm_application_security_group',
        'azurerm_private_dns_zone',
        'azurerm_network_watcher'
    ]

    def __init__(self, params):
        try:
            self.params = params
            self.utils = TfUtils(params)
            self.file_utils = TfFileUtils(params, step=params.step, step_type=params.step_type)
            self.tenant_prefix = self.utils.get_tenant_id(params.tenant_name)
            self._load_azurerm_resources_json()
            self._init_azure_client()
            self._create_env_sh()
        except Exception as e:
            print("ERROR:AzurermResources:", "__init__", e)

    #### public methods #######

    def get_tenant_resources(self):
        ##
        self.get_all_resources()
        return self.tf_cloud_obj_list

    def get_infra_resources(self):
         ##
        self.get_all_resources()
        return self.tf_cloud_obj_list

    def get_tenant_key_pair_list(self):
        return None

    # def get_all_resources(self):
    #     ##
    #     self.get_all_resources()
    #     return self.tf_cloud_obj_list

    ########### helpers ###########

    def tf_cloud_resource(self, tf_resource_type, tf_cloud_obj, tf_variable_id=None, tf_import_id=None,
                          skip_if_exists=False):

        tf_resource_var_name = tf_variable_id
        tf_resource_type_sync_id = tf_import_id
        if tf_resource_var_name is None or tf_resource_type_sync_id is None:
            print("tf_cloud_resource 'tf_variable_id' 'tf_import_id' must be provided", tf_resource_type, tf_resource_var_name, tf_import_id )
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
            print(self.file_utils.stage_prefix(),
                  "Exception tf_resource_var_name should be unique : {0} {1} {2}".format(
                      tf_resource_type, tf_resource_var_name, tf_id))
            raise Exception("tf_resource_var_name should be unique {}".format(tf_id))
        # create array
        tf_resource = {"tf_resource_type": tf_resource_type, "tf_variable_id": tf_resource_var_name,
                       "tf_import_id": tf_resource_type_sync_id,
                       "module": self.file_utils.params.module}
        self.tf_cloud_obj_list.append(tf_resource)
        self.resources_unique_ids.append(tf_id)
        return tf_resource


    def _init_azure_client(self):
        try:
            if os.environ['AZURE_CLIENT_ID'] is None:
                json_env=self._load_env()
                subscription_id = json_env['AZURE_SUBSCRIPTION_ID']  # your Azure Subscription Id
                credentials = ServicePrincipalCredentials(
                    client_id=json_env['AZURE_CLIENT_ID'],
                    secret=json_env['AZURE_CLIENT_SECRET'],
                    tenant=json_env['AZURE_TENANT_ID']
                )
            else:
                subscription_id = os.environ.get(
                    'AZURE_SUBSCRIPTION_ID',
                    '11111111-1111-1111-1111-111111111111')  # your Azure Subscription Id
                credentials = ServicePrincipalCredentials(
                    client_id=os.environ['AZURE_CLIENT_ID'],
                    secret=os.environ['AZURE_CLIENT_SECRET'],
                    tenant=os.environ['AZURE_TENANT_ID']
                )

            self.resource_client = ResourceManagementClient(credentials, subscription_id)
            self.compute_client = ComputeManagementClient(credentials, subscription_id)
            self.storage_client = StorageManagementClient(credentials, subscription_id)
            self.network_client = NetworkManagementClient(credentials, subscription_id)
        except Exception as e:
            print("ERROR:AzurermResources:", "_init_azure_client", e)

    def _load_azurerm_resources_json(self):
        json_file = "azurerm_resources.json"#"{0}__resources.json".format(self.params.provider)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), json_file)
        if not os.path.exists(json_path):
            raise Exception("schema {0} not found".format(json_path))
        try:
            with open(json_path) as f:
                self.azurerm_resources = json.load(f)
        except Exception as e:
            print("ERROR:AzurermResources:", "_load_azurerm_resources_json", e)


    def _load_env(self):
        json_path = "/shell/.duplo_env.json"
        if not os.path.exists(json_path):
            return {}
        with open(json_path) as f:
            return json.load(f)

    def _create_env_sh(self):
        #Issues  with env variables in imprt script and python on shell docker. need a clean and final method
        self.env_list = []
        self.env_list.append("export ARM_SUBSCRIPTION_ID=\"{0}\"".format( os.environ.get('AZURE_SUBSCRIPTION_ID')))
        self.env_list.append("export ARM_CLIENT_ID=\"{0}\"".format( os.environ.get('AZURE_CLIENT_ID')))
        self.env_list.append("export ARM_CLIENT_SECRET=\"{0}\"".format( os.environ.get('AZURE_CLIENT_SECRET')))
        self.env_list.append("export ARM_TENANT_ID=\"{0}\"".format( os.environ.get('AZURE_TENANT_ID')))
        self.file_utils.create_azure_env_sh(self.env_list)

#duplocloud/shell:terraform_kubectl_azure_test_v26
    def filter_resource(self, id):
        if self.params.import_module == "tenant":
            filter_tenant_str = "/resourcegroups/duploservices-{0}".format(self.params.tenant_name.lower())
            if filter_tenant_str in id.lower():
                return True
            else:
                return False
        elif self.params.import_module == "infra":
            filter_tenant_str = "/resourcegroups/duploinfra-{0}".format(self.params.tenant_name.lower())
            if filter_tenant_str in id.lower():
                return True
            else:
                return False
        return True


    def get_all_resources(self):
        print("======================================================")
        arrAzureResources = []
        unique_processed_resouces = []
        unique_skip_resouces = []
        for instance in self.resource_client.resources.list():
            # small hack to filter tenant_name
            res = AzureResource(instance)
            if self.filter_resource(instance.id):
                arrAzureResources.append(res)
                try:
                    # print(res.type_name)
                    if res.type_name_singular in  self.azurerm_resources:
                        res.type_name = res.type_name_singular
                        if res.type_name in self.resources_skip:
                            if res.type_name not in unique_skip_resouces:
                                unique_skip_resouces.append(res.type_name)
                            print("FOUND and SKIP", res.type_name , "===", res.id)
                        else:
                            if res.type_name not in unique_processed_resouces:
                                unique_processed_resouces.append(res.type_name)
                            print("FOUND", res.type_name, "===", res.id)
                            self.tf_cloud_resource(res.type_name, instance, tf_variable_id= res.name,
                                               tf_import_id=res.id, skip_if_exists=True)
                    elif res.type_name in  self.azurerm_resources:
                        if res.type_name in self.resources_skip:
                            if res.type_name not in unique_skip_resouces:
                                unique_skip_resouces.append(res.type_name)
                            print("FOUND and SKIP", res.type_name, "===", res.id)
                        else:
                            if res.type_name not in unique_processed_resouces:
                                unique_processed_resouces.append(res.type_name)
                            print("FOUND", res.type_name, "===", res.id)
                            self.tf_cloud_resource(res.type_name, instance, tf_variable_id=res.name,
                                               tf_import_id=res.id, skip_if_exists=True)
                    else:
                        print("======== NOT_FOUND", res.type_name, "===", res.id)
                except Exception as e:
                    print("ERROR:AzurermResources:", "get_all_resources", e)

        print("===============len(arrAzureResources)=============", len(arrAzureResources), "==========================")
        print("unique_processed_resouces", len(unique_processed_resouces), unique_processed_resouces)
        print("unique_skip_resouces", len(unique_skip_resouces), unique_skip_resouces)
        print("======================================================")
        return arrAzureResources

#
#
# def get_all_resources():
#     subscription_id = os.environ.get(
#         'AZURE_SUBSCRIPTION_ID',
#         '11111111-1111-1111-1111-111111111111')  # your Azure Subscription Id
#     credentials = ServicePrincipalCredentials(
#         client_id=os.environ['AZURE_CLIENT_ID'],
#         secret=os.environ['AZURE_CLIENT_SECRET'],
#         tenant=os.environ['AZURE_TENANT_ID']
#     )
#
#
#     resource_client = ResourceManagementClient(credentials, subscription_id)
#     compute_client = ComputeManagementClient(credentials, subscription_id)
#     storage_client = StorageManagementClient(credentials, subscription_id)
#     network_client = NetworkManagementClient(credentials, subscription_id)
#
#     ###########
#     # Prepare #
#     ###########
#     # for vm in compute_client.virtual_machines.list_all():
#     #     print("\tVM: {}".format(vm.name))
#     #
#     # # for vm in resource_client.resources.list():
#     # #     print("\t  '{}':'{}'   ,".format(vm.name, vm.id.split("/")))
#     # #
#     #
#     #
#     #
#     # lsrsrc = resource_client.resources.list_by_resource_group("duploservices-azdemo1")
#     # print(lsrsrc)
#     #
#     # for vm in lsrsrc:
#     #     # print("\t{}: {}  {}  {}  {}".format(vm.type, vm.name, vm.kind, vm.sku ,vm    ) )
#     #     print("\t  '{}':'{}'   ,".format(  vm.name, vm.id.split("/")))
#     #
#     # print(lsrsrc)
#
#
#     # for vm in resource_client.resources.list():
#     #     print("\t  '{}':'{}'   ,".format(vm.name, vm.id.split("/")))
#     #
#
#     resourceGroups = {}
#     print("======================================================")
#     arrAzureResource=[]
#     for vm in resource_client.resources.list():
#         arrAzureResource.append( AzureResource(vm))
#     print("======================================================")
#     print("======================================================")
#     for vm in resource_client.resources.list():
#         print(vm.name,vm.type, vm.id)
#     print("======================================================")
#     print("======================================================")
#     for vm in resource_client.resources.list():
#         print(vm )
#     print("======================================================")
#     for vm in resource_client.resources.list():
#         arr = (vm.id  ).split("/")
#         arr.pop(0)
#         count = len(arr)
#         print(vm.id)
#         resource = {'id':vm.id}
#         for i in range(0, count, 2):
#             key = arr[i]
#             if count > i+1:
#                 value = arr[i+1 ]
#             else:
#                 value =""
#             resource[key] = value
#             if value == vm.name:
#                 resource["providerApiName"] = key
#                 resource["providerApiValue"] = value
#                 resource["providerApiValueSnake"] = snakecase(key)
#
#                 resource["name"] = vm.name
#             # print(i, i + 1, key, "=", value)
#         if  'resourceGroups'  in resource.keys():
#             resourceGroupsKey = resource['resourceGroups']
#             if not resourceGroupsKey in resourceGroups.keys():
#                 resourceGroups[resourceGroupsKey] = []
#             # print("INVALID '{}': {} {}    ,".format(vm.name, resource.keys(), resource))
#             resourceGroups[resourceGroupsKey].append(resource)
#         else:
#             print("INVALID '{}': {}    ,".format(vm.name, resource))
#         print("'{}': {}    ,".format(vm.name, resource ))
#
#     print("resources" )
#     print("{}".format(resourceGroups))
#
#     getResourceGroups(resourceGroups)
#     jsonStr = json.dumps(resourceGroups)
#     print(jsonStr)
#
# def getResourceGroups(resourceGroups):
#     for key in resourceGroups.keys():
#         print("'{}': {}    ,".format(key, len(resourceGroups[key]) ))
#         for resourceGroup in resourceGroups[key]:
#             if 'name' in resourceGroup.keys():
#                 print(" {} : {}/{}/{}   ,".format(resourceGroup['name'],  resourceGroup['providers'],  resourceGroup['providerApiName'],  resourceGroup['providerApiValue'] ))
#             else:
#              print("name???? {}  ,".format(resourceGroup ))
#     print(   resourceGroups.keys() )
#     return resourceGroups.keys()
#
#
# def getResourceGroups(resourceGroups):
#     for key in resourceGroups.keys():
#         print("'{}': {}    ,".format(key, len(resourceGroups[key]) ))
#         for resourceGroup in resourceGroups[key]:
#             if 'name' in resourceGroup.keys():
#                 print(" {} : {}/{}/{}   ,".format(resourceGroup['name'],  resourceGroup['providers'],  resourceGroup['providerApiName'],  resourceGroup['providerApiValue'] ))
#             else:
#              print("name???? {}  ,".format(resourceGroup ))
#     print(   resourceGroups.keys() )
#     return resourceGroups.keys()

# if __name__ == "__main__":
#     # os.environ['AZURE_SUBSCRIPTION_ID'] = ""
#     # os.environ['AZURE_TENANT_ID'] = ""
#     # os.environ['AZURE_CLIENT_ID']  = ""
#     # os.environ['AZURE_CLIENT_SECRET'] = ""
#
#
#     # os.system('bash /Users/brighu/_go/azure.sh ')
#     params =  AzurermImportParameters( )
#     params.step ="step1"
#     params.step_type  = "step1"
#     obj = AzurermResources(params)
#     list = obj.get_all_resources()
#     print(list)

