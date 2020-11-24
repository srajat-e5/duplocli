from duplocli.terraform.params.param_base import ParamBase
from duplocli.terraform.params.arg_parse import ArgParse, TfModule


class AzurermParams(ParamBase):
    provider = "azurerm"
    attr_names = ["tenant_name",
                  "infra_name",
                  "import_name",
                  "zip_file_path",
                  "params_json_file_path",
                  #new
                  "filter_resources",
                  # absolete
                  "import_module",
                  # absolete
                  "download_aws_keys",
                  "tenant_id",
                  "api_token",
                  "url",
                  "aws_region"]

    default_parameters = {
        "zip_folder": "../work/output/zip",
        "temp_folder": "../work/output",

        #new
        "filter_resources":"",
        # defaults
        "is_infra": False,
        "tenant_name": None,
        "infra_names": [],

        "is_tenant": False,
        "tenant_name": None,
        "infra_names": [],



        # we
        "import_module": None,
        "default_import_module": None,

        "state_file": None,
        "zip_file_path": None,

        "folder_prefix": "duplo_tf",

        "download_aws_keys": "no",  # should not be part of export, but it could be a separate cmd.
        "url": "all",
        "tenant_id": "all",
        "api_token": "all",

        "is_tenant_id_needed": False,
        "aws_region": "us-west-2",
        "provider": "azurerm"

    }

    def __init__(self):
        super(AzurermParams, self).__init__(self.provider, self.attr_names, self.default_parameters)
        print(self.provider)

    def validate(self):
        self.check_multiple_tenants_infra()
        super().validate()

    def _split_tenants_infra(self, str_names):
        arr_names_new = []
        if str_names is not None:
            if "," in str_names:
                arr_names = self.str_names.split(",")
                for arr_name in arr_names:
                    arr_names_new.strip()
                    if len(arr_name) > 0 :
                        arr_names_new.append(arr_names_new)
        return arr_names_new

    def check_multiple_tenants_infra(self):
        self.tenant_names = self._split_tenants_infra(self.tenant_name)
        self.infra_names = self._split_tenants_infra(self.infra_name)
