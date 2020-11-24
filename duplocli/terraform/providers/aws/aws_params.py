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
        "provider": "aws",
        "zip_folder": "../work/output/zip",
        "temp_folder": "../work/output",

        # new
        "is_filter_resources_all":False,
        "filter_resources": "",
        # defaults
        "is_tenant": False,
        "tenant_name": "infra",
        "tenant_names": [],

        "is_infra": False,
        "infa_name": None,
        "infra_names": [],

        "state_file": None,
        "zip_file_path": None,

        "folder_prefix":"duplo_tf",

        "import_module": None,
        "default_import_module": "infra",

        #sould not be part of terraform code but a extra cmd line call
        "download_aws_keys": "no",
        "url": None,
        "tenant_id": None,
        "api_token": None,
        "is_tenant_id_needed": False,

        "aws_region": "us-west-2"

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
