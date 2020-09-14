####################### TfModule #############################################################
class TfModule:
    def __init__(self, is_tenant, is_key_download, name, tenant_id, tenant_token):
        self.is_tenant = is_tenant
        self.is_key_download = is_key_download
        self.name = name
        self.tenant_id = tenant_id
        self.tenant_token = tenant_token