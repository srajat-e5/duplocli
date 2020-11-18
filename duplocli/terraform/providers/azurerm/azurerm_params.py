from duplocli.terraform.params.param_base import ParamBase
from duplocli.terraform.params.arg_parse import ArgParse, TfModule


class AzurermParams(ParamBase):
    provider = "azurerm"
    attr_names = ["tenant_name",
                  "infra_name",
                  "import_module", #absolete
                  "import_name",
                  "zip_file_path",
                  "params_json_file_path",
                  "download_aws_keys",
                  "tenant_id",
                  "api_token",
                  "url",
                  "aws_region"]

    default_parameters = {
        "zip_folder": "../work/output/zip",
        "temp_folder": "../work/output",

        # defaults
        "tenant_name": None,
        "infra_name": None,
        "is_infra": False,
        "is_tenant": False,

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
        super().validate()
