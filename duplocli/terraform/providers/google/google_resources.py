class GoogleResources:
    debug_print_out = False
    debug_json = True
    create_key_pair = False
    #
    vpc_list = {}

    def __init__(self, params):
        self.tenant_prefix = self.utils.get_tenant_id(params.tenant_name)

    def get_tenant_resources(self):
        return self.tf_cloud_obj_list

    def get_infra_resources(self):
        return self.tf_cloud_obj_list

