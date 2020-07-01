import psutil
import os
import datetime
import argparse
from duplocli.terraform.common.tf_file_utils import TfFileUtils

# app params for all providers = aws/azure
arg_params = {
    "import_module": {"short_name": "m", "disc": "import_module=infra, tenant, tenant_list, all. default is tenant,"},
    "import_name": {"short_name": "i", "disc": "zip file path to save imported terraform files in zip format "},
    "zip_file_path": {"short_name": "o", "disc": "zip file path to save imported terraform files in zip format"},
    "download_aws_keys": {"short_name": "k", "disc": "Aws keypair=yes/no, private key used for ssh into EC2 servers"},
    "tenant_name": {"short_name": "n", "disc": "Tenant Name(s) comma separated e.g. webdev or  webdev,website,default"},
    "tenant_id": {"short_name": "t", "disc": "TenantId(s) comma separated e.g.  xxxxxx,yyy,97a833a4-2662-4e9c-9867-222565ec5cb6"},
    "api_token": {"short_name": "a", "disc": "Duplo API Token. API Token must be with admin rights for multi-tenant."},
    "url": {"short_name": "u", "disc": "Duplo URL  e.g. https://msp.duplocloud.net"},
    "params_json_file_path": {"short_name": "j", "disc": "All params passed as single JSON file."},
    "aws_region": {"short_name": "r", "disc": "AWSREGION  e.g. us-west2"}
}

####################### ImportParametersBase #############################################################
class ImportParametersBase:
    provider = ""
    step_type = "infra"
    step = "step1"
    default_params_path = "duplocli/terraform/json_import_tf_parameters_default.json"
    is_tenant_id_needed = False
    def __init__(self, attr_names):
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

    def get_parser(self):
        self.parser = TfArgsHelper(self)
        return self.parser.get_parser()

    def parsed_args(self, parsed_args):
        self.parser.parsed_args(parsed_args)

    def validate(self):
        self.parser.validate_and_update_modules()

    def modules(self):
        return list(self.tf_modules.keys())

    def get_tf_module(self, tenant_name):
        return  self.tf_modules[tenant_name]

####################### AwsImportParameters #############################################################
class AwsImportParameters(ImportParametersBase):
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
        super(AwsImportParameters, self).__init__(parameters)
        self.provider = "aws"

    def validate(self):
        super().validate()
        # validate params
        if self.import_module in ["infra", "all"]:
            required_fields = ["aws_region"]
        else:
            required_fields = ["tenant_name", "aws_region"]
        self._check_required_fields(required_fields)

####################### AzureImportParameters #############################################################
class AzureImportParameters(ImportParametersBase):
    provider = "azure"

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
        super.__init__(AzureImportParameters, parameters)
        self.provider = "azure"

####################### GoogleImportParameters #############################################################
class GoogleImportParameters(ImportParametersBase):
    provider = "google"

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
        super.__init__(GoogleImportParameters, parameters)
        self.provider = "google"

####################### KubernetesImportParameters #############################################################
class KubernetesImportParameters(ImportParametersBase):
    provider = "kubernetes"

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
        super.__init__(KubernetesImportParameters, parameters)
        self.provider = "kubernetes"

####################### HelmImportParameters #############################################################
class HelmImportParameters(ImportParametersBase):
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
        super.__init__(HelmImportParameters, parameters)
        self.provider = "helm"


####################### params #############################################################
####################### params #############################################################
####################### params #############################################################

def get_help(params):
    attr_names = params.attr_names
    provider = params.provider

    help_str = []
    help_str.append("Terraform provider: " + provider)
    help_str.append("")
    help_str.append("Terraform import parameters help")
    help_str.append("")
    help_str.append("")
    help_str.append("Sequence of parameters evaluation is: default -> ENV -> JSON_FILE -> arguments")
    help_str.append("   parameters in argument ")
    help_str.append("       ->  override  parameters in terraform_import_json")
    help_str.append("   AND parameters in terraform_import_json ")
    help_str.append("        ->   override  parameters in ENV variables")
    help_str.append("   AND parameters in ENV variables")
    help_str.append("       ->   override default values (json_import_tf_parameters_default.json)")
    help_str.append("")
    help_str.append("")
    help_str.append("parameters in argument")
    help_str.append("")
    for attr_name in attr_names:
        attr = arg_params[attr_name]
        str = "   [-{0} / --{1} {2}]         -- {3}".format(attr['short_name'], attr_name, attr_name.upper(),
                                                            attr["disc"])
        help_str.append(str)
    help_str.append("")
    help_str.append("")
    help_str.append(" OR alternately ")
    help_str.append(" pass the above parameters in single json file")
    help_str.append("")
    help_str.append(" [-j/--params_json_file_path PARAMSJSONFILE] = FOLDER/terraform_import_json.json")
    help_str.append("{")
    for attr_name in attr_names:
        attr = arg_params[attr_name]
        str = "   \"{0}\": \"xxxxxx\"  ".format(attr_name)
        help_str.append(str)
    help_str.append("}")

    help_str.append("")
    help_str.append("")
    help_str.append(" OR alternately ")
    help_str.append(" pass the above parameters in ENV variables")
    help_str.append("")
    for attr_name in attr_names:
        attr = arg_params[attr_name]
        str = "   export \"{0}\"=\"xxxxxx\"  ".format(attr_name)
        help_str.append(str)
    help_str.append(" ")
    help_str.append(" ")

    return "\n".join(help_str)

####################### TfModule #############################################################
class TfModule:
    def __init__(self, is_tenant, is_key_download, name, tenant_id, tenant_token):
        self.is_tenant = is_tenant
        self.is_key_download = is_key_download
        self.name = name
        self.tenant_id = tenant_id
        self.tenant_token = tenant_token

####################### TfArgsHelper #############################################################
####################### TfArgsHelper #############################################################
####################### TfArgsHelper #############################################################

class TfArgsHelper:

    def __init__(self, params):
        self.params = params

    ############  validate   ############
    def validate_and_update_modules(self):
        # is tenant_id, api_token, url  are needed?
        if self.params.import_module  in ["tenant", "tenant_list"] and self.params.download_aws_keys == "yes" :
            self.params.is_tenant_id_needed = True
        # validate
        self._validate_download_keys()
        self._validate_tenants()
        # update params with tenants and tenant_ids
        self.params.tf_modules = self._update_modules()

    ### module and tenant scope
    def _validate_download_keys(self):
        if self.params.is_tenant_id_needed:
            required_fields = ["url", "tenant_id", "api_token"]
            self._check_required_fields(required_fields)

    def _validate_tenants(self):
        params = self.params
        if params.import_module in ["infra", "all"]:
            return
        elif params.import_module in ["tenant", None, ""]:
            params.import_module = "tenant"
            if "," in params.tenant_name or "," in params.tenant_id:
                self._raise_error("Exception: import_module=tenant - more thann one tenant is provided.")
        elif params.import_module == "tenant_list":
            if self.params.is_tenant_id_needed:
                tenants_arr, tenant_ids_arr = self._parse_tenants()
                if len(tenants_arr) != len(tenant_ids_arr):
                    self._raise_error(
                        "Exception: import_module=tenant_list - count not matching for tenant_names and tenant_ids, should be equal.")

    def _parse_tenants(self):
        tenants = []
        tenant_ids = []
        params = self.params
        if params.import_module in ["infra", "all"]:
            tenants.append(params.import_module)
            tenant_ids.append("")
        elif params.import_module in ["tenant", None, ""]:
            tenants.append(params.tenant_name)
            tenant_ids.append(params.tenant_id)
        elif params.import_module == "tenant_list":
            tenants.append("infra")
            tenant_ids.append("infra")
            tenants_arr = params.tenant_name.split(",")
            for tenant in tenants_arr:
                tenant = tenant.strip()
                if tenant != "":
                    tenants.append(tenant)
            tenant_ids_arr = params.tenant_id.split(",")
            for tenant_id in tenant_ids_arr:
                tenant_id = tenant_id.strip()
                if tenant_id != "":
                    tenant_ids.append(tenant_id)
        return tenants, tenant_ids

    def _update_modules(self):
        tf_modules = {}
        is_key_download = self.params.is_tenant_id_needed
        api_token = self.params.api_token
        # def __init__(self, is_tenant, is_key_download, name, tenant_id, tenant_token):
        tenants, tenant_ids = self._parse_tenants()
        for index in range(len(tenants)):
            tenant_name = tenants[index]
            tenant_id = ""
            is_tenant = True
            if tenant_name in ["infra", "all"]:
                is_tenant = False
            if is_key_download:
                tenant_id = tenant_ids[index]
            tf_module = TfModule(is_tenant, is_key_download, tenant_name, tenant_id, api_token)
            tf_modules[tenant_name] = tf_module
        return tf_modules

    def _raise_error(self, message):
        print("============== ERROR ============== ")
        print(message)
        print("============== USAGE ============== ")
        print(get_help(self.params))
        print("============== Exception ============== ")
        raise Exception(message)

    def _check_required_fields(self, required_fields):
        parameters = vars(self)
        for required_field in required_fields:
            if required_field not in parameters or parameters[required_field] is None or parameters[required_field] == "":
                fields = ",".join(required_fields)
                print("Missing required_fields = " + " ".join(parameters))
                self._raise_error("Exception: Missing required_fields = " + fields)

    ######## ####  parser   ######## ####
    def get_parser(self, ):
        help = get_help(self.params)
        parser = argparse.ArgumentParser(description="Download Terraform state files.", usage=help)
        for attr_name in self.params.attr_names:
            parser.add_argument('-' + arg_params[attr_name]['short_name'],
                                '--' + attr_name, action='store', dest=attr_name)
        return parser

    def parsed_args(self, parsed_args):
        self.file_utils = TfFileUtils(self)
        parameters = self.file_utils.load_json_file(self.params.default_params_path)
        #
        print("########## default parameters ########## ")
        for key in parameters:
            print(" default parameter values", key, parameters[key])
        #
        print("########## passed as environ variables  ########## ")
        for key in parameters:
            if key in os.environ:
                print(" override parameter by passed as environ variable ", key, os.environ[key])
                val = os.environ[key]
                parameters[key] = val
        #
        print("########## params_json_file_path parameters ########## ")
        if parsed_args.params_json_file_path is not None:
            print("params_json_file_path ", parsed_args.params_json_file_path)
            parameters_json = self.file_utils.load_json_file(parsed_args.params_json_file_path)
            for key in parameters_json:
                print(" params_json_file_path parameter values", key, parameters_json[key])
                parameters[key] = parameters_json[key]
        #
        print("########## passed as arguments parameters ########## ")
        for key, val in vars(parsed_args).items():
            if val is not None:
                print(" override parameter by passed in arguments ", key, val)
                parameters[key] = val

        # set as attributes
        self._set_attributes(parameters)
        self._create_work_file_paths()
        # set defaults
        if self.params.tenant_id is None:
            self.params.tenant_id = ""

        if self.params.import_module in ["tenant", None, ""]:
            self.params.import_module = "tenant"
        print("########## final parameters ########## ")
        parameters_cur = vars(self.params)
        for key in parameters_cur:
            print("final", key, getattr(self.params, key))
        #
        return parameters

    def _set_attributes(self, parameters):
        key_list = list(parameters.keys())
        att_name_list = self.params.attr_names + key_list
        for att_name in att_name_list:
            value = self._from_dict(parameters, att_name)
            setattr(self.params, att_name, value)

    def _from_dict(self, parameters, key):
        if key in parameters:
            return parameters[key]
        return None

    def _create_work_file_paths(self):
        params = self.params
        if params.import_name is None:
            now = datetime.datetime.now()
            now_str = now.strftime("%m-%d-%Y--%H-%M-%S")
            params.import_name = now_str
        params.parameters_default = self.file_utils.load_json_file(params.default_params_path)
        if params.parameters_default["temp_folder"] == params.temp_folder:
            params.temp_folder = os.path.join(params.temp_folder, params.tenant_name, params.import_name)
            params.zip_folder = os.path.join(params.temp_folder, "zip")
        if params.zip_file_path is None:
            params.zip_file_path = os.path.join(params.zip_folder, params.import_name)
        params.temp_folder_path = params.temp_folder
        params.zip_folder_path = params.zip_folder



