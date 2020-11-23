from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import requests

dummy_values = {
    "cidr_block": "0.0.0.0/0",
    "ipv6_cidr_block": "0.0.0.0/0"
}


class AzurermTfImportStep1(AzureBaseTfImportStep):

    def __init__(self, params):
        super(AzurermTfImportStep1, self).__init__(params)

    ############ execute_step public resources ##########
    def execute(self, cloud_obj_list=[]):
        try:
            self._copy_resources_file_to_all_steps(cloud_obj_list)
            self._tf_resources(cloud_obj_list)
            self._create_tf_state()
        except Exception as e:
            self.file_utils._save_errors("ERROR:Step1: execute {0}".format(e))

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

    def _pull_additional_sub_res(self):
        if "azurerm_virtual_machine_scale_set" in self.cloud_obj_list:
            self.state_read_from_file = self.file_utils.tf_state_file_srep1()
            if not self.file_utils.file_exists(self.state_read_from_file):
                raise Exception(
                    "Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")
            self.state_dict = self.file_utils.load_json_file(self.state_read_from_file)
            # network_profile ip_configuration load_balancer_backend_address_pool_ids
            # "load_balancer_backend_address_pool_ids": [
            #     "/subscriptions/3a1286e1-be22-46c9-8e79-adcc388bf66f/resourceGroups/MC_duploinfra-azdev_azdev_francecentral/providers/Microsoft.Network/loadBalancers/kubernetes/backendAddressPools/aksOutboundBackendPool",
            #     "/subscriptions/3a1286e1-be22-46c9-8e79-adcc388bf66f/resourceGroups/MC_duploinfra-azdev_azdev_francecentral/providers/Microsoft.Network/loadBalancers/kubernetes/backendAddressPools/kubernetes"
            # ],

    ############ aws tf resources ##########
    def _tf_resources(self, cloud_obj_list):
        for cloud_obj in cloud_obj_list:
            try:
                self._tf_resource(cloud_obj)
            except Exception as e:
                self.file_utils._save_errors("ERROR:Step1: _tf_resources {0}".format(e))

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
            self.file_utils._save_errors("ERROR:Step1: _tf_resource {0}".format(e))
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
