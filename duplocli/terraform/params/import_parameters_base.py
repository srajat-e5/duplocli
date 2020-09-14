import psutil

from duplocli.terraform.params.tf_args_helper import TfArgsHelper


class ImportParametersBase(TfArgsHelper):
    provider = ""
    step_type = "infra"
    step = "step1"
    default_params_path = "duplocli/terraform/json_import_tf_parameters_default.json"
    is_tenant_id_needed = False
    def __init__(self, attr_names):
        super().__init__()
        self.attr_names = attr_names
        if psutil.WINDOWS:
            self.default_params_path = self.default_params_path.replace("/", "\\")

    def set_step_type(self, step_type):
        self.step_type = step_type
        self.module = step_type
        if step_type in self.modules():
            self.tf_module = self.get_tf_module(step_type)

    def set_step(self, step):
        self.step = step

    def validate(self):
        self.validate_and_update_modules()

    def modules(self):
        return list(self.tf_modules.keys())

    def get_tf_module(self, tenant_name):
        return  self.tf_modules[tenant_name]
