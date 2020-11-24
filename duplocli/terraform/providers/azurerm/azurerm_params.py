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
        "provider": "azurerm",
        "zip_folder": "../work/output/zip",
        "temp_folder": "../work/output",

        #new
        "is_filter_resources_all": False,
        "filter_resources":"",

        # defaults
        "is_tenant": False,
        "tenant_name": None,
        "tenant_names": [],

        "is_infra": False,
        "infra_name": None,
        "infra_names": [],

        # we
        "import_module": None,
        "default_import_module": None,

        "state_file": None,
        "zip_file_path": None,

        "folder_prefix": "duplo_tf",

        # should not be part of export, but it could be a separate cmd.
        "download_aws_keys": "no",
        "url": "all",
        "tenant_id": "all",
        "api_token": "all",

        "is_tenant_id_needed": False,
        "aws_region": "us-west-2"


    }

    def __init__(self):
        super(AzurermParams, self).__init__(self.provider, self.attr_names, self.default_parameters)
        print(self.provider)

    def validate(self):
        super().validate()


