from duplocli.terraform.params.import_parameters_base import ImportParametersBase


class AwsParams(ImportParametersBase):
    provider = "aws"
    def __init__(self):
        parameters = ["tenant_name",
                      "import_module",
                      "import_name",
                      "zip_file_path",
                      "params_json_file_path",
                      "download_aws_keys",
                      "tenant_id",
                      "api_token",
                      "url",
                      "aws_region"]
        super(AwsParams, self).__init__(parameters)
        self.provider = "aws"

    def validate(self):
        super().validate()
        # validate params
        if self.import_module in ["infra", "all"]:
            required_fields = ["aws_region"]
        else:
            required_fields = ["tenant_name", "aws_region"]
        self._check_required_fields(required_fields)