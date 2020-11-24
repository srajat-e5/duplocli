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


class AzureTfStepConst:
    # azurerm_metricalerts
    todo_unknown_res = {
        "azurerm_app_certificate_order": "resourceGroups/duploinfra-demo/providers/Microsoft.CertificateRegistration/certificateOrders/duplocloud",
        "azurerm_restore_point_collections": "../resourceGroups/AzureBackupRG_westus2_1/providers/Microsoft.Compute/restorePointCollections/AzureBackup_duploservices-a002-ctscan-web02-pqeypp_7...",
        "azurerm_versions": "../resourceGroups/SharedGalleryRG/providers/Microsoft.Compute/galleries/myGallery/images/testcompliance/versions/20.0.0",
        "azurerm_monitor_metric_alert": "resourceGroups/duploservices-azdemo1/providers/Microsoft.Insights/metricalerts/testmetrics2-servers-storage_percent",
        "azurerm_network_intent_policies": "../resourceGroups/duploinfra-azdev/providers/Microsoft.Network/networkIntentPolicies/mi_default_8221d37b-1b37-4a6d-9fab-edfae4814b2a_10-228-2-0-24"
    }
    supported_corum = ['azurerm_kubernetes_cluster', 'azurerm_resource_group', 'azurerm_subnet',
                       'azurerm_key_vault', 'azurerm_network_security_group', 'azurerm_virtual_network',
                       'azurerm_storage_account', 'azurerm_availability_set', 'azurerm_mysql_server',
                       'azurerm_user_assigned_identity', 'azurerm_application_security_group',
                       'azurerm_app_service_plan', 'azurerm_app_service', 'azurerm_virtual_machine_scale_set',
                       'azurerm_lb', 'azurerm_route_table']

    supported_corum_all = ['azurerm_availability_set', 'azurerm_resource_group', 'azurerm_sql_server',
                           'azurerm_user_assigned_identity', 'azurerm_application_security_group',
                           'azurerm_app_service_plan', 'azurerm_app_service', 'azurerm_kubernetes_cluster',
                           'azurerm_subnet', 'azurerm_key_vault', 'azurerm_network_security_group',
                           'azurerm_virtual_network', 'azurerm_storage_account', 'azurerm_mysql_server',
                           'azurerm_managed_disk', 'azurerm_virtual_machine', 'azurerm_virtual_machine_extension',
                           'azurerm_network_interface', 'azurerm_public_ip', 'azurerm_virtual_machine_scale_set',
                           'azurerm_lb', 'azurerm_route_table', 'azurerm_network_watcher']

    supported_incloud_all = ['azurerm_storage_account', 'azurerm_resource_group', 'azurerm_log_analytics_workspace',
                             'azurerm_log_analytics_solution', 'azurerm_managed_application_definition',
                             'azurerm_managed_application', 'azurerm_custom_provider', 'azurerm_snapshot',
                             'azurerm_image', 'azurerm_key_vault', 'azurerm_subnet',
                             'azurerm_network_security_group',
                             'azurerm_public_ip', 'azurerm_virtual_network', 'azurerm_automation_account',
                             'azurerm_automation_runbook', 'azurerm_managed_disk', 'azurerm_virtual_machine',
                             'azurerm_virtual_machine_extension', 'azurerm_kubernetes_cluster',
                             'azurerm_user_assigned_identity', 'azurerm_virtual_network_gateway_connection',
                             'azurerm_dns_zone', 'azurerm_local_network_gateway', 'azurerm_network_interface',
                             'azurerm_route_table', 'azurerm_virtual_network_gateway', 'azurerm_availability_set',
                             'azurerm_logic_app_workflow', 'azurerm_application_security_group',
                             'azurerm_container_group',
                             'azurerm_mysql_server', 'azurerm_postgresql_server', 'azurerm_private_dns_zone',
                             'azurerm_private_dns_zone_virtual_network_link', 'azurerm_app_service_certificate',
                             'azurerm_app_service_plan', 'azurerm_app_service', 'azurerm_virtual_machine_scale_set',
                             'azurerm_lb', 'azurerm_network_watcher', 'azurerm_shared_image_gallery',
                             'azurerm_sql_server']

    ####################
    DEBUG_EXPORT_ALL = False  # False True

    resources_skip = [
        "azurerm_monitor_metric_alert",
        "azurerm_snapshot",
        "azurerm_private_dns_zone_virtual_network_link",
        "azurerm_app_service_certificate",
        "azurerm_public_ip",
        "azurerm_container_group"
    ]
    resources_skip_all = ["azurerm_monitor_metric_alert"]

    ###
    azure_name_to_resoure_map = {
        "azurerm_workflows": "azurerm_logic_app_workflow",
        "azurerm_applications": "azurerm_managed_application",
        "azurerm_application_definitions": "azurerm_managed_application_definition",
        "azurerm_managed_clusters": "azurerm_kubernetes_cluster",
        "azurerm_load_balancers": "azurerm_lb",
        "azurerm_servers": "azurerm_sql_server",
        "azurerm_resource_providers": "azurerm_custom_provider",
        "azurerm_deployment_scripts": "azurerm_template_deployment",
        "azurerm_extensions": "azurerm_virtual_machine_extension",
        "azurerm_certificates": "azurerm_app_service_certificate",  # for web
        "azurerm_server_farms": "azurerm_app_service_plan",
        "azurerm_sites": "azurerm_app_service",
        #
        "azurerm_route_tables": "azurerm_route_table",
        "azurerm_user_assigned_identities": "azurerm_user_assigned_identity",

        "azurerm_public_i_p_addresses": "azurerm_public_ip",
        "azurerm_public_ip_addresses": "azurerm_public_ip",
        "azurerm_vaults": "azurerm_key_vault",
        "azurerm_connections": "azurerm_virtual_network_gateway_connection",
        "azurerm_dnszones": "azurerm_dns_zone",
        "azurerm_runbooks": "azurerm_automation_runbook",
        "azurerm_certificate_orders": "azurerm_app_certificate_order",
        "azurerm_disks": "azurerm_managed_disk",
        "azurerm_workspaces": "azurerm_log_analytics_workspace",
        "azurerm_solutions": "azurerm_log_analytics_solution",
        "azurerm_metricalerts": "azurerm_monitor_metric_alert",
        "azurerm_virtual_network_links": "azurerm_private_dns_zone_virtual_network_link",
        "azurerm_galleries": "azurerm_shared_image_gallery",
        # "azurerm_extensions": "",
        #
        # "azurerm_metricalerts": "azurerm_monitor_metric_alert",
        # "azurerm_disks": "azurerm_managed_disk",
        # "azurerm_extensions": "azurerm_virtual_machine_extension",
        # "azurerm_virtual_network_links": "azurerm_private_dns_zone_virtual_network_link",
        # "azurerm_galleries": "azurerm_shared_image_gallery",
        #
        # "azurerm_hosting_environments": "azurerm_app_service_environment",
        # "azurerm_server_farms": "",
        # "azurerm_sites": "",
        # "azurerm_load_balancers": "",
        "A": ""

    }

    # resources_skip111 = [
    #     'azurerm_automation_account',
    #     'azurerm_availability_set',
    #     'azurerm_local_network_gateway',
    #     'azurerm_network_watcher',
    #     'azurerm_private_dns_zone',
    #
    #     'azurerm_snapshot',
    #     "azurerm_app_certificate_order",
    #     "azurerm_extensions",
    #     "azurerm_certificates",
    #     #
    #     "azurerm_automation_runbook",
    #     "azurerm_dns_zone",
    #     "azurerm_key_vault",  ###### needed ###
    #     "azurerm_monitor_metric_alert",  ###### needed ###
    #     "azurerm_network_security_group",  ###### needed ###
    #     "azurerm_route_table",  ###### needed ###
    #     #
    #     "azurerm_storage_account",  ###### needed ###
    #     "azurerm_virtual_machine",  ###### needed ###
    #     "azurerm_image",
    #
    #     ""
    #     # some bug in azurerm ---  test016122019 not accepting required === "hyper_v_generation": "V1" or "V2" or ""
    # ]
    # connectionSecurity
    # resources_skip = [
    #
    #     'azurerm_automation_account',
    #     'azurerm_availability_set',
    #     'azurerm_local_network_gateway',
    #     'azurerm_network_watcher',
    #     'azurerm_private_dns_zone',
    #
    #     'azurerm_snapshot',
    #     "azurerm_app_certificate_order",
    #     "azurerm_extensions",
    #     "azurerm_certificates",
    #     #
    #     "azurerm_automation_runbook",
    #     "azurerm_dns_zone",
    #     "azurerm_key_vault",  ###### needed ###
    #     "azurerm_monitor_metric_alert",  ###### needed ###
    #     "azurerm_network_security_group",  ###### needed ###
    #     "azurerm_route_table",  ###### needed ###
    #     #
    #     "azurerm_storage_account",  ###### needed ###
    #     "azurerm_virtual_machine",  ###### needed ###
    #     "azurerm_image",
    #
    #     ""
    #     # some bug in azurerm ---  test016122019 not accepting required === "hyper_v_generation": "V1" or "V2" or ""
    # ]
    # resources_skip_not_supported = [
    #     "azurerm_workspaces",
    #     "azurerm_solutions",
    #     "azurerm_runbooks",
    #     "azurerm_certificate_orders",
    #     "azurerm_disks",
    #     "azurerm_extensions",
    #     "azurerm_vaults",
    #     "azurerm_connections",
    #     "azurerm_dnszones",
    #     "azurerm_metricalerts",
    #     "azurerm_user_assigned_identities",
    #     "azurerm_virtual_network_links",
    #     "azurerm_certificates",
    #     "azurerm_galleries"
    #     # some bug in azurerm ---  test016122019 not accepting required === "hyper_v_generation": "V1" or "V2" or ""
    # ]
    # waf
    # lb
    # azurerm_application_gateway
    #     resources_proess = [
    #         # 'azurerm_storage_account',
    #         # "azurerm_network_security_group",
    #         #'azurerm_image',
    #         'azurerm_snapshot',
    #         'azurerm_automation_account',
    #         'azurerm_virtual_machine',
    #         'azurerm_local_network_gateway',
    #         'azurerm_public_ip',
    #         'azurerm_virtual_network_gateway',
    #         'azurerm_virtual_network',
    #         'azurerm_availability_set',
    #         'azurerm_application_security_group',
    #         'azurerm_private_dns_zone',
    #         'azurerm_network_watcher'
    #     ]

