from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import requests
from duplocli.terraform.providers.azurerm.tf_step_const import *
from duplocli.terraform.providers.azurerm.tf_step_helper import AzureTfStepHelper

dummy_values = {
    "cidr_block": "0.0.0.0/0",
    "ipv6_cidr_block": "0.0.0.0/0"
}


class AzurermTfImportStep1(AzureBaseTfImportStep):
    tf_import_script_index = 1
    def __init__(self, params):
        super(AzurermTfImportStep1, self).__init__(params)
        self.helper = AzureTfStepHelper(params)

    ############ execute_step public resources ##########
    def execute(self, cloud_obj_list=[]):
        try:
            #self._copy_resources_file_to_all_steps(cloud_obj_list)
            self._tf_resources(cloud_obj_list)
            self._create_tf_state()
        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:Step1:1 execute {0}".format(e))
        try:
            found = self._pull_additional_sub_res(cloud_obj_list)
            if found:
                ##
                self.file_utils.tf_import_script_backup_file(self.tf_import_script_index)
                self.tf_import_script_index = self.tf_import_script_index + 1
                ##
                # self._copy_resources_file_to_all_steps(cloud_obj_list)
                self._tf_resources(self.helper.cloud_obj_list)
                self._create_tf_state()
        except Exception as e:
            self.file_utils._save_errors(e, "ERROR:Step1:2 execute {0}".format(e))

        try:
            self._copy_resources_file_to_all_steps(cloud_obj_list)
        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:Step1:3 execute {0}".format(e))
        return self.file_utils.tf_main_file()

    def get_tenant_key_pair_list(self):
        return None

    ############ main.tf.json + script + generate state ##########
    def _copy_resources_file_to_all_steps(self, cloud_obj_list):
        self.file_utils.save_to_json(self.file_utils.tf_resources_file(), cloud_obj_list)
        self.file_utils.save_to_json(self.file_utils.tf_resources_file_for_step("step2"), cloud_obj_list)
        self.file_utils.save_to_json(self.file_utils.tf_resources_file_for_step("step3"), cloud_obj_list)
        self.file_utils.save_to_json(self.file_utils.tf_resources_file_for_step("step4"), cloud_obj_list)

    def _create_tf_state(self):
        super()._create_tf_state()
        self.file_utils.create_state(self.file_utils.tf_run_script())

    def _pull_additional_sub_res(self, cloud_obj_list):
        found=False
        # for cloud_obj in cloud_obj_list:
        # if "azurerm_virtual_machine_scale_set" in cloud_obj_list:
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()
        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception(
                "Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")
        self.state_dict = self.file_utils.load_json_file(self.state_read_from_file)
        resources = self.state_dict['resources']
        for resource in resources:
            try:
                tf_resource_type = resource["type"]
                found1 = self._child_res_azurerm_virtual_machine_scale_set(tf_resource_type, resource)
                if found1:
                    found=True
            except Exception as e:
                self.file_utils._save_errors(e, "ERROR:Step2: _tf_resources {0}".format(e))
                print("ERROR:Step2:", "_tf_resources", e, resource)

        return found

            # network_profile ip_configuration load_balancer_backend_address_pool_ids
            # "load_balancer_backend_address_pool_ids": [
            #     "/subscriptions/3a1286e1-be22-46c9-8e79-adcc388bf66f/resourceGroups/MC_duploinfra-azdev_azdev_francecentral/providers/Microsoft.Network/loadBalancers/kubernetes/backendAddressPools/aksOutboundBackendPool",
            #     "/subscriptions/3a1286e1-be22-46c9-8e79-adcc388bf66f/resourceGroups/MC_duploinfra-azdev_azdev_francecentral/providers/Microsoft.Network/loadBalancers/kubernetes/backendAddressPools/kubernetes"
            # ],
    def _child_res_azurerm_virtual_machine_scale_set(self, tf_resource_type, resource):
        found = False
        try:
            if tf_resource_type == "azurerm_virtual_machine_scale_set":
                attributes = resource['instances'][0]['attributes']
                if "network_profile" in attributes:
                    network_profiles = attributes["network_profile"]
                    for network_profile in network_profiles:
                        if "ip_configuration" in network_profile:
                            ip_configurations = network_profile["ip_configuration"]
                            for ip_configuration in ip_configurations:
                                if "load_balancer_backend_address_pool_ids" in ip_configuration:
                                    load_balancer_backend_address_pool_ids = ip_configuration[
                                        "load_balancer_backend_address_pool_ids"]
                                    for load_balancer_backend_address_pool_id in load_balancer_backend_address_pool_ids:
                                        print("load_balancer_backend_address_pool_id",
                                              load_balancer_backend_address_pool_id)
                                        found = True
                                        # "/subscriptions/29474c73-cd93-48f0-80ee-9577a54e2227/resourceGroups/MC_duploinfra-demo_test_westus2
                                        # /providers/Microsoft.Network/loadBalancers/kubernetes/backendAddressPools/aksOutboundBackendPool",
                                        metadata = self.helper._parse_id_metadata(load_balancer_backend_address_pool_id)

                                        self.helper.tf_cloud_resource("azurerm_lb_backend_address_pool", metadata,
                                                                      tf_variable_id=metadata["resource_name"],
                                                                      tf_import_id=load_balancer_backend_address_pool_id,
                                                                      skip_if_exists=True)
                                        return found

        except Exception as e:
            pass
        return found
    ############ aws tf resources ##########
    def _tf_resources(self, cloud_obj_list):
        for cloud_obj in cloud_obj_list:
            try:
                self._tf_resource(cloud_obj)
            except Exception as e:
                self.file_utils._save_errors(e,"ERROR:Step1: _tf_resources {0}".format(e))

    def _tf_resource(self, cloud_obj):
        tf_resource_type = cloud_obj['tf_resource_type']
        resource_obj = self._init_tf_resource(cloud_obj)
        try:
            schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
            for required_name in schema.required:
                if required_name in dummy_values:
                    resource_obj[required_name] = dummy_values[required_name]
                else:
                    # keep an eye --- we are neglecting data types ! until we get error ?
                    resource_obj[required_name] = "xxxx"
        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:Step1: _tf_resource {0}".format(e))
        return resource_obj

    def _init_tf_resource(self, cloud_obj):
        tf_resource_type = cloud_obj['tf_resource_type']
        tf_resource_var_name = cloud_obj['tf_variable_id']
        tf_resource_type_sync_id = cloud_obj['tf_import_id']
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        tf_resource_type_root[tf_resource_var_name] = resource_obj
        self.tf_import_sh_list.append(
            'terraform import "' + tf_resource_type + '.' + tf_resource_var_name + '"  "' + tf_resource_type_sync_id + '"')
        return resource_obj
