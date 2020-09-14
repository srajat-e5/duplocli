from duplocli.terraform.params.import_parameters_base import ImportParametersBase


class HelmParams(ImportParametersBase):
    provider = "helm"

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
        super.__init__(HelmParams, parameters)
        self.provider = "helm"