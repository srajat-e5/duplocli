from duplocli.terraform.params.param_base import ParamBase
from duplocli.terraform.params.arg_parse import ArgParse, TfModule

class AzurermParams(ParamBase) :
    provider = "azurerm"
    attr_names = ["tenant_name",
                  "import_module",
                  "import_name",
                  "infra_name",
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

        "tenant_name": "infra",
        "import_module": "infra",
        "default_import_module": "infra",

        "state_file": None,
        "zip_file_path": None,

        "download_aws_keys": "no",
        "url": "all",
        "tenant_id": "all",
        "api_token": "all",

        "is_tenant_id_needed": False,
        "import_module": "tenant",
        "aws_region": "us-west-2",
        "provider": "azurerm"

    }


    def __init__(self):
        super(AzurermParams, self).__init__(self.provider, self.attr_names, self.default_parameters )


    def validate(self):
        super().validate()

        # validate params
        # if self.import_module in ["infra", "all"]:
        #     pass #required_fields = ["aws_region"]
        # else:
        #     required_fields = ["tenant_name", "aws_region"]
        # self._check_required_fields(required_fields)

