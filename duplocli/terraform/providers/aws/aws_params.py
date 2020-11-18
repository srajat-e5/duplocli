from duplocli.terraform.params.param_base import ParamBase
from duplocli.terraform.params.arg_parse import ArgParse, TfModule


class AwsParams(ParamBase):
    provider = "aws"
    attr_names = ["tenant_name",
                  "import_module",
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

        "state_file": None,
        "zip_file_path": None,

        "is_infra": False,
        "is_tenant": False,

        "folder_prefix":"duplo_tf",

        "tenant_name": "infra",
        "import_module": None,
        "default_import_module": "infra",

        "download_aws_keys": "no",
        "url": None,
        "tenant_id": None,
        "api_token": None,
        "is_tenant_id_needed": False,

        "aws_region": "us-west-2",
        "provider": "aws"
    }

    def __init__(self):
        super(AwsParams, self).__init__(self.provider, self.attr_names, self.default_parameters)

    def validate(self):
        super().validate()
        # validate params
        if self.import_module in ["infra", "all"]:
            required_fields = ["aws_region"]
        else:
            required_fields = ["tenant_name", "aws_region"]
        self._check_required_fields(required_fields)
