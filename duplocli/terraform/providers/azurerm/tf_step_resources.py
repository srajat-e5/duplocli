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
from duplocli.terraform.providers.azurerm.tf_step_helper import AzureTfStepHelper

class AzureTfStepResource:
    def __init__(self, res):
        self.id = res.id
        self.name_origin = res.name
        self.name = res.name.lower()
        self._getType(res)

    def _getType(self, res):
        if "/" in res.type:
            arr = res.type.split("/")
            type_camel = arr[-1]
        else:
            type_camel = res.type
        arr_id = res.id.split("/")
        self.provider = ""
        if len(arr_id) > 6:
            self.provider = arr_id[6]

        self.type_name = "azurerm_{0}".format(snakecase(type_camel))
        self.type_name_orig = self.type_name

        if "azurerm_servers" == self.type_name:
            if self.provider.lower() == "Microsoft.DBForMySQL".lower():
                self.type_name = "azurerm_mysql_server"
            elif self.provider.lower() == "Microsoft.DBForPostgreSQL".lower():
                self.type_name = "azurerm_postgresql_server"
            elif self.provider.lower() == "Microsoft.Sql".lower():
                self.type_name = "azurerm_sql_server"
            else: #??????
                print("??????? NOT_OK_UN_RESOLVED_MICROSOFT======== ??????? ",self.provider," SHOULD ? azurerm_servers === Default to azurerm_sql_server")
                #self.type_name = "azurerm_sql_server"

        #??????? NOT_OK_UN_RESOLVED_MICROSOFT======== ???????  azurerm_databases === /subscriptions/3a1286e1-be22-46c9-8e79-adcc388bf66f/resourceGroups/cbtenant-sample/providers/Microsoft.Sql/servers/sqlserversample04/databases/master
        if "azurerm_databases" == self.type_name:
            if self.provider.lower() == "Microsoft.DBForMySQL".lower():
                self.type_name = "azurerm_MYsql_database"
            elif self.provider.lower() == "Microsoft.DBForPostgreSQL".lower():
                self.type_name = "azurerm_postgresql_database"
            elif self.provider.lower() == "Microsoft.Sql".lower():
                self.type_name = "azurerm_sql_database"
            else: #??????
                print("??????? NOT_OK_UN_RESOLVED_MICROSOFT======== ???????",self.provider,"  SHOULD ?  azurerm_databases === Default to azurerm_sql_database")
                #self.type_name = "azurerm_sql_database"

        # azurerm_mysql_server
        if self.type_name == "azurerm_public_i_p_addresses":
            self.type_name = "azurerm_public_ip"

        if "/serverFarms/" in self.id:  # azurerm_app_service_plan
            self.id = self.id.replace("/serverFarms/", "/serverfarms/")
        self.type_name_singular = self.type_name[:-1]


class AzurermResources:
    # tf_cloud_obj_list = []
    # resources_unique_ids = []
    subnet_dict = {}
    res_groups_subnet_unique_dict = []
    res_groups_subnet_unique_dict2 = []

    def __init__(self, params):
        try:
            self.helper = AzureTfStepHelper(params)
            self.filter_all = params.filter_resources =="all" or AzureTfStepConst.DEBUG_EXPORT_ALL
            if self.filter_all:
                self.resources_skip = AzureTfStepConst.resources_skip_all
            else:
                self.resources_skip = AzureTfStepConst.resources_skip

            self.params = params
            self.utils = TfUtils(params)
            self.file_utils = TfFileUtils(params, step=params.step, step_type=params.step_type)
            self.tenant_prefix = self.utils.get_tenant_id(params.tenant_name)
            self._load_azurerm_resources_json()
            self._init_azure_client()
            self._create_env_sh()
        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:step0:resources: __init__ {0}".format(e))
            print("ERROR:AzurermResources:", "__init__", e)

    #### public methods #######
    def get_all_resources(self):
        self._all_resources()
        return self.helper.cloud_obj_list

    def get_tenant_key_pair_list(self):
        ##no impl for now
        return None

    ###### azure client ######

    def _init_azure_client(self):
        try:
            if os.environ['AZURE_CLIENT_ID'] is None:
                json_env = self._load_env()
                subscription_id = json_env['AZURE_SUBSCRIPTION_ID']  # your Azure Subscription Id
                credentials = ServicePrincipalCredentials(
                    client_id=json_env['AZURE_CLIENT_ID'],
                    secret=json_env['AZURE_CLIENT_SECRET'],
                    tenant=json_env['AZURE_TENANT_ID']
                )
            else:
                PYTHONUNBUFFERED = 1

                AZURE_SUBSCRIPTION_ID = None
                AZURE_TENANT_ID = None
                AZURE_CLIENT_ID = None
                AZURE_CLIENT_SECRET = None


                subscription_id = AZURE_SUBSCRIPTION_ID or os.environ['AZURE_SUBSCRIPTION_ID']  # your Azure Subscription Id
                credentials = ServicePrincipalCredentials(
                    client_id= AZURE_CLIENT_ID or os.environ['AZURE_CLIENT_ID'],
                    secret=AZURE_CLIENT_SECRET or os.environ['AZURE_CLIENT_SECRET'],
                    tenant=AZURE_TENANT_ID or os.environ['AZURE_TENANT_ID']
                )


            self.az_resource_client = ResourceManagementClient(credentials, subscription_id)
            self.az_compute_client = ComputeManagementClient(credentials, subscription_id)
            self.az_storage_client = StorageManagementClient(credentials, subscription_id)
            self.az_network_client = NetworkManagementClient(credentials, subscription_id)
            self.az_sql_client = SqlManagementClient(credentials, subscription_id)

           #self.az_network_client.load_balancers

            # self.az_sql_client.firewall_rules.list_by_server(resource_group_name, server_name)

        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:step0:resources: _init_azure_client {0}".format(e))
            print("ERROR:AzurermResources:", "_init_azure_client", e)

    def _load_env(self):
        json_path = "/shell/.duplo_env.json"
        if not os.path.exists(json_path):
            return {}
        with open(json_path) as f:
            return json.load(f)

    def _create_env_sh(self):
        # Issues  with env variables in imprt script and python on shell docker. need a clean and final method
        self.env_list = []
        self.env_list.append("export ARM_SUBSCRIPTION_ID=\"{0}\"".format(os.environ.get('AZURE_SUBSCRIPTION_ID')))
        self.env_list.append("export ARM_CLIENT_ID=\"{0}\"".format(os.environ.get('AZURE_CLIENT_ID')))
        self.env_list.append("export ARM_CLIENT_SECRET=\"{0}\"".format(os.environ.get('AZURE_CLIENT_SECRET')))
        self.env_list.append("export ARM_TENANT_ID=\"{0}\"".format(os.environ.get('AZURE_TENANT_ID')))
        self.file_utils.create_azure_env_sh(self.env_list)




    ########## filter_resource ################
    def tf_cloud_resource(self, tf_resource_type, tf_cloud_obj, tf_variable_id=None, tf_import_id=None,
                          skip_if_exists=False):
        return self.helper.tf_cloud_resource(tf_resource_type, tf_cloud_obj, tf_variable_id=tf_variable_id,
                               tf_import_id=tf_import_id,  skip_if_exists=skip_if_exists)

    ########## filter_resource ################
    def _all_resources(self):
        print("\n\n\n===============DEBUG=======================================")
        if True:
            self.tenant_resource_debug()
        print("======================DEBUG================================\n\n\n")
        self.resources_only_debug = False  # True  #False
        # trac info
        self.unique_processed_resouces = []
        self.unique_skip_resouces = []
        self.unique_unsupported_resouces = []

        # helper
        azure_name_to_resoure_map_keys = AzureTfStepConst.azure_name_to_resoure_map.keys()
        # results
        arrAzureResources = []
        # loop all azure resources
        instances = self._get_resources_root()
        for instance in instances:
            # small hack to filter tenant_name
            res = AzureTfStepResource(instance)
            if self.filter_resource(instance.id):
                arrAzureResources.append(res)
                try:
                    if res.type_name in azure_name_to_resoure_map_keys:
                        res.type_name = AzureTfStepConst.azure_name_to_resoure_map[res.type_name]
                        azurerm_resources_found = True
                    elif res.type_name_singular in azure_name_to_resoure_map_keys:
                        res.type_name = self.azure_name_to_resoure_map[res.type_name_singular]
                        azurerm_resources_found = True
                    elif res.type_name in self.azurerm_resources:
                        azurerm_resources_found = True
                    elif res.type_name_singular in self.azurerm_resources:
                        res.type_name = res.type_name_singular
                        azurerm_resources_found = True
                    else:
                        print("??????? NOT_OK_UN_RESOLVED_MICROSOFT======== ??????? ", res.type_name, "===", res.id)
                        azurerm_resources_found = False

                    if azurerm_resources_found:
                        if self.should_import_resource_type(res):
                            self.tf_cloud_resource(res.type_name, instance, tf_variable_id=res.name,
                                                   tf_import_id=res.id, skip_if_exists=True)
                            #additionaly always include respource group
                            id_metadata = self.helper._parse_id_metadata(res.id)
                            self._tf_cloud_resource_group(id_metadata, res.id, "azurerm_resource_group", instance)
                            self._tf_cloud_resource_vn_subnets(id_metadata,res.id,res.type_name, instance)
                            self._tf_cloud_resource_lb_backend_ports(id_metadata,res.id,res.type_name, instance)
                            #
                            # #additionaly for sql add firewall -- we need list of firewalls
                            # if res.type_name  in ["azurerm_mysql_server","azurerm_postgresql_server"]:
                            #     self.tf_cloud_resource("azurerm_mysql_firewall_rule", instance, tf_variable_id=res.name+ "_connectionSecurity",
                            #                        tf_import_id=res.id+"/firewallRules/connectionSecurity", skip_if_exists=True)
                        else:
                            print("========ABORT 1 SKIPPED", res.type_name, "===", res.id)
                    else:
                        print("======== ABORT 2 NOT_FOUND: not supported by azurerm terraform?", res.type_name, "===",
                              res.id)
                except Exception as e:
                    self.file_utils._save_errors(e,"ERROR:step0:resources: get_all_resources {0}".format(e))
                    print("ERROR:AzurermResources:", "get_all_resources", e)
                    print("========ABORT 3 ERROR", res.type_name, "===", res.id)

        print("AzurermResource s===============len(arrAzureResources)=============", len(arrAzureResources))
        print("unique_processed_resouces", len(self.unique_processed_resouces), self.unique_processed_resouces)
        print("unique_skip_resouces", len(self.unique_skip_resouces), self.unique_skip_resouces)
        print("unique_unsupported_resouces", len(self.unique_unsupported_resouces), self.unique_unsupported_resouces)
        print("AzurermResources ======================================================\n\n\n")
        return arrAzureResources
    ########## filter_resource ################
    # duplocloud/shell:terraform_kubectl_azure_test_v26

    def _filter_resource_tenant(self, id):
        if len(self.params.tenant_names) > 0:
            id = id.lower()
            for filter_name in self.params.tenant_names:
                filter_name = filter_name.lower()
                if "/resourcegroups/duploservices-{0}".format(filter_name) in id:
                    return True
                if "/resourcegroups/duploservices-{0}-lb".format(filter_name) in id:
                    return True
                if "/resourcegroups/duplomgapp-mgr-{0}".format(filter_name) in id:
                    return True
                #this is hack? will include all
                if filter_name in id:
                    return True
        return True

    def _filter_resource_infra(self, id):
        if len(self.params.infra_names) > 0:
            id = id.lower()
            for filter_name in self.params.infra_names:
                filter_name = filter_name.lower()
                if "/resourcegroups/duploinfra-{0}".format(filter_name) in id:
                    return True
                if "/resourcegroups/duplobackups-{0}".format(filter_name) in id:
                    return True
                # this is hack? will include all
                if filter_name in id:
                    return True
        return True


    def filter_resource(self, id):
        #############
        if  self.filter_all:
            return True
        if self.params.is_tenant: #if self.params.import_module == "tenant":
             if self._filter_resource_tenant(id):
                return True
        if self.params.is_infra: #elif self.params.import_module == "infra":
            if self._filter_resource_infra(id):
                return True
        return False

    def should_import_resource_type(self, res):
        if res.type_name not in self.azurerm_resources:
            if res.type_name not in self.unique_unsupported_resouces:
                self.unique_unsupported_resouces.append(res.type_name)
                print("NOT_OK_UN_RESOLVED_MICROSOFT: not supported?: TypeName?", res.type_name, "===", res.id)
            return False

        ############# DEBUG #############
        # test only few imports at a time
        if self.resources_only_debug:
            if res.type_name in ['azurerm_container_group',
                                 'azurerm_virtual_machine']:  # ,'azurerm_network_interface']:
                if res.type_name not in self.unique_processed_resouces:
                    self.unique_processed_resouces.append(res.type_name)
                print("OK:DEBUG:", res.type_name, "===", res.id)
                return True
            else:
                if res.type_name not in self.unique_skip_resouces:
                    self.unique_skip_resouces.append(res.type_name)
                print("NOT_OK_SKIP_LIST:DEBUG:", res.type_name, "===", res.id)
                return False
        ############# DEBUG #############

        if res.type_name in self.resources_skip:
            if res.type_name not in self.unique_skip_resouces:
                self.unique_skip_resouces.append(res.type_name)
            print("NOT_OK_SKIP_LIST:", res.type_name, "===", res.id)
            return False
        if res.type_name not in self.unique_processed_resouces:
            self.unique_processed_resouces.append(res.type_name)
        # print("OK:", res.type_name, "===", res.id)
        return True


    ########## filter_resource ################
    ########## filter_resource ################
    ########## filter_resource ################

    def _tf_cloud_resource_group(self, id_metadata, tf_import_id, type_name, tf_cloud_obj):
        res_name = id_metadata["resource_group_name"]
        tf_import_id_new = id_metadata["resource_group_id"]
        self.tf_cloud_resource(type_name, tf_cloud_obj, tf_variable_id=res_name,
                               tf_import_id=tf_import_id_new, skip_if_exists=True)
        if type_name not in self.unique_processed_resouces:
            self.unique_processed_resouces.append(type_name)

    def _tf_cloud_resource_vn_subnets(self, id_metadata, tf_import_id, type_name, tf_cloud_obj):
        resource_group_name = id_metadata["resource_group_name"]
        # resource_group_id = id_metadata["resource_group_id"]
        process = self._fetch_subnets(resource_group_name)
        if process:
            type_name = "azurerm_subnet"
            for id in self.subnet_dict:
                try:
                    res = self.subnet_dict[id]
                    # print("_tf_cloud_resource_vn_subnets", resource_group_name, id)
                    self.tf_cloud_resource("azurerm_subnet", tf_cloud_obj, tf_variable_id=res.name,
                                           tf_import_id=res.id, skip_if_exists=True)
                    if type_name not in self.unique_processed_resouces:
                        self.unique_processed_resouces.append(type_name)
                    id_metadata = self.helper._parse_id_metadata(res.id)
                    self._tf_cloud_resource_group(id_metadata, res.id, "azurerm_resource_group", res)
                except Exception as e:
                    self.file_utils._save_errors(e,"ERROR:step0:_tf_cloud_resource_vn_subnets:  {0}".format(e))
                    print("ERROR:step0:: ", "_tf_cloud_resource_vn_subnets", e)

    def _tf_cloud_resource_lb_backend_ports(self, id_metadata, tf_import_id, type_name, tf_cloud_obj):
        pass
        # resource_group_name = id_metadata["resource_group_name"]
        # # resource_group_id = id_metadata["resource_group_id"]
        # process = self._get_backend_ports(resource_group_name)
        # type_name="azurerm_subnet"
        # if process:
        #    for id in self.subnet_dict:
        #        subnet = self.subnet_dict[id]
        #        self.tf_cloud_resource(type_name, tf_cloud_obj, tf_variable_id=subnet.name,
        #                               tf_import_id=subnet.id, skip_if_exists=True)
        #        if type_name not in self.unique_processed_resouces:
        #            self.unique_processed_resouces.append(type_name)

    ########### helpers ###########

    def _get_resources_root(self):
        instance_root = []
        for instance in self.az_resource_client.resources.list():
            instance_root.append(instance)
        return instance_root

    def _get_backend_ports(self, res_group_name):
        found_new = False
        try:
            if res_group_name in self.res_groups_subnet_unique_dict2:
                return found_new
            self.res_groups_subnet_unique_dict2.append(res_group_name)

            load_balancers = self.az_network_client.load_balancers.list(res_group_name)
            for load_balancer in load_balancers:
                load_balancer_name = load_balancer.name
                try:
                    load_balancer_backend_address_pools = self.az_network_client.backend_address_pools.list(
                        res_group_name, load_balancer_name)
                    for load_balancer_backend_address in load_balancer_backend_address_pools:
                        self.subnet_dict[load_balancer_backend_address.id] = load_balancer_backend_address
                        found_new = True
                except Exception as e:
                    self.file_utils._save_errors(e, "ERROR:step0:resources: _get_backend_ports {0}".format(e))
                    print("ERROR:AzurermResources:1", "_get_backend_ports", e)
        except Exception as e:
            self.file_utils._save_errors(e, "ERROR:step0:resources:2 _get_backend_ports {0}".format(e))
            print("ERROR:AzurermResources:2", "_get_backend_ports", e)
        return found_new

    def _fetch_subnets(self, res_group_name):
        found_new = False
        try:
            # if res_group_name in self.res_groups_subnet_unique_dict:
            #     return found_new
            # self.res_groups_subnet_unique_dict.append(res_group_name)

            virtual_networks = self.az_network_client.virtual_networks.list(res_group_name)
            for virtual_network in virtual_networks:
                virtual_network_name = virtual_network.name
                try:
                    # print("_fetch_subnets 1", res_group_name, virtual_network_name)
                    subnets = self.az_network_client.subnets.list(res_group_name, virtual_network_name)
                    for subnet in subnets:
                        print("_fetch_subnets 2", res_group_name, virtual_network_name, subnet.id)
                        self.subnet_dict[subnet.id] = subnet
                        found_new = True
                except Exception as e:
                    self.file_utils._save_errors(e, "ERROR:step0:resources: _get_subnets {0}".format(e))
                    print("ERROR:AzurermResources:1", "_get_subnets", e)
        except Exception as e:
            self.file_utils._save_errors(e, "ERROR:step0:resources:2 _get_subnets {0}".format(e))
            print("ERROR:AzurermResources:2", "_get_subnets", e)
        return found_new

    def _load_azurerm_resources_json(self):
        json_file = "azurerm_resources.json"  # "{0}__resources.json".format(self.params.provider)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), json_file)
        if not os.path.exists(json_path):
            raise Exception("schema {0} not found".format(json_path))
        try:
            with open(json_path) as f:
                self.azurerm_resources = json.load(f)
        except Exception as e:
            self.file_utils._save_errors(e, "ERROR:step0:resources: _load_azurerm_resources_json {0}".format(e))
            print("ERROR:AzurermResources:", "_load_azurerm_resources_json", e)

        ######

    def tenant_resource_debug(self):
        for instance in self.az_resource_client.resources.list():
            id = instance.id
            if self.params.is_tenant:
                # if self.params.import_module == "tenant":
                filter_tenant_str = "/resourcegroups/duploservices-{0}".format(self.params.tenant_name.lower())
                if filter_tenant_str in id.lower():
                    print("*****##tenant##*****  resourcegroups match? filter_resource ",
                          self.params.tenant_name.lower(), id)
                elif self.params.tenant_name.lower() in id.lower():
                    print("*****##tenant##*****  only tenant found? filter_resource ", self.params.tenant_name.lower(),
                          id)
                else:
                    pass  # print("*****##tenant##*****  not found? filter_resource ", self.params.tenant_name.lower(), id)
            if self.params.is_infra:
                # if self.params.import_module == "infra":
                filter_tenant_str = "/resourcegroups/duploinfra-{0}".format(self.params.infra_name.lower())
                if filter_tenant_str in id.lower():
                    print("*****##infra##*****  complete match? filter_resource ", self.params.infra_name.lower(), id)
                elif self.params.infra_name.lower() in id.lower():
                    print("*****##infra##*****  only infra-name found? filter_resource ",
                          self.params.infra_name.lower(),
                          id)
                else:
                    pass  # print("*****##infra##*****  not found? filter_resource ", self.params.infra_name.lower(), id)

        return True
