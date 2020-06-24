import psutil
import os
import datetime
import argparse
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.common.tf_utils import TfUtils

#app params for all providers = aws/azure
arg_params = {
        "tenant_name":{"short_name":"n", "disc":"Tenant Name e.g. webdev"},
        "import_name": {"short_name":"i", "disc":"zip file path to save imported terraform files in zip format "},
        "zip_file_path": {"short_name":"o", "disc":"zip file path to save imported terraform files in zip format"},
        "params_json_file_path": {"short_name":"j", "disc":"All params passed in single JSON file"},
        "download_aws_keys":{"short_name":"k", "disc":"Aws keypair=yes/no, private key used for ssh into EC2 servers"},
        "tenant_id": {"short_name":"t", "disc":"TenantId e.g. 97a833a4-2662-4e9c-9867-222565ec5cb6"},
        "api_token": {"short_name":"a", "disc":"Duplo API Token"},
        "url": {"short_name":"u", "disc":"Duplo URL  e.g. https://msp.duplocloud.net"},
        "import_module": {"short_name": "m", "disc": "import_module=infra or tenant. default is tenant,"},
        "aws_region": {"short_name":"r", "disc":"AWSREGION  e.g. us-west2"}
    }


def get_help(attr_names, provider):
    help_str = []
    help_str.append("Terraform provider: "+ provider)
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
        attr =  arg_params[attr_name]
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



class ImportParametersBase:
    step_type = "infra"
    step = "step1"
    default_params_path = "duplocli/terraform/json_import_tf_parameters_default.json"

    def __init__(self, attr_names):
        self.attr_names=attr_names
        if psutil.WINDOWS:
            self.default_params_path = self.default_params_path.replace("/", "\\")
    def set_step_type(self, step_type):
        self.step_type = step_type

    def set_step(self, step):
        self.step = step

    def modules(self):
        #here we can easily support multiple self.tenant_name list ... e.g. use comma separated self.tenant_name.
        if self.import_module == "infra":
            return ["infra"]
        else:
            return [self.tenant_name]

    ######## ####  from parsed args ######## ####
    def get_parser(self):
        help = get_help(self.attr_names, self.provider)
        parser = argparse.ArgumentParser(description="Download Terraform state files.", usage=help)
        for attr_name in self.attr_names:
            parser.add_argument('-'+ arg_params[attr_name]['short_name'],
                                '--'+attr_name, action='store', dest=attr_name)
        return parser

    def parsed_args(self, parsed_args):
        self.file_utils = TfFileUtils(self)
        parameters = self.file_utils.load_json_file(self.default_params_path)
        print("########## default parameters ########## ")
        for key in parameters:
            print(" default parameter values", key, parameters[key])

        print("########## passed as environ variables  ########## ")
        for key in parameters:
            if key in os.environ:
                print(" override parameter by passed as environ variable ", key, os.environ[key])
                val = os.environ[key]
                parameters[key] = val

        print("########## params_json_file_path parameters ########## ")

        if parsed_args.params_json_file_path is not None:
            print("params_json_file_path ", parsed_args.params_json_file_path)
            parameters_json = self.file_utils.load_json_file(parsed_args.params_json_file_path)
            for key in parameters_json:
                print(" params_json_file_path parameter values", key, parameters_json[key])
                parameters[key] = parameters_json[key]

        print("########## passed as arguments parameters ########## ")
        for key, val in vars(parsed_args).items():
            if val is not None:
                print(" override parameter by passed in arguments ", key, val)
                parameters[key] = val

        # set as attributes
        self.set_attributes(parameters)
        self.create_work_file_paths()

        print("########## final parameters ########## ")
        parameters_cur = vars(self)
        for key in parameters_cur:
            print("final", key, getattr(self, key) )


        return parameters

    def set_attributes(self, parameters):
        key_list = list(parameters.keys())
        att_name_list = self.attr_names + key_list
        for att_name in att_name_list:
            value = self._from_dict(parameters, att_name)
            setattr(self, att_name, value)

    def _from_dict(self, parameters, key):
        if key in parameters:
            return parameters[key]
        return None

    ######## #### validate   ######## ####
    def validate(self):
        pass
    def _check_required_fields(self,  required_fields):
        parameters = vars(self)
        for required_field in required_fields:
            if parameters[required_field] is None:
                fields=",".join(required_fields)
                print("missing required_fields = " + parameters)
                print(get_help(self.attr_names, self.provider))
                raise Exception("missing required_fields = " +fields)

    # mostly static
    def fix_os(self):
       pass

    def create_work_file_paths(self):
        if self.import_name is None:
            now = datetime.datetime.now()
            now_str = now.strftime("%m-%d-%Y--%H-%M-%S")
            self.import_name = now_str

        self.parameters_default = self.file_utils.load_json_file(self.default_params_path)
        if self.parameters_default["temp_folder"] == self.temp_folder:
            self.temp_folder = os.path.join(self.temp_folder, self.tenant_name, self.import_name)
            self.zip_folder = os.path.join(self.temp_folder, "zip")

        if self.zip_file_path is None:
            self.zip_file_path = os.path.join(self.zip_folder, self.import_name)

        self.temp_folder_path = self.temp_folder #?
        self.zip_folder_path = self.zip_folder #?
        # if psutil.WINDOWS:
        #     self.zip_folder_path = self.zip_folder_path.replace("/", "\\")
        #     self.temp_folder_path = self.temp_folder_path.replace("/", "\\")
        #     self.zip_folder_local_path = self.zip_folder_local_path.replace("/", "\\")
        # else:
        #     self.zip_folder_path = self.zip_folder_path.replace("\\", "/")
        #     self.temp_folder_path = self.temp_folder_path.replace("\\", "/")
        #     self.zip_folder_local_path = self.zip_folder_local_path.replace("/", "\\")



class AwsImportParameters(ImportParametersBase):
    provider = "aws"
    def __init__(self):
        parameters = ["tenant_name" ,
                      "import_module",
                    "import_name" ,
                    "zip_file_path" ,
                    "params_json_file_path",
                    "download_aws_keys",
                    "tenant_id",
                    "api_token",
                    "url",
                    "aws_region"]
        super(AwsImportParameters, self).__init__(parameters)
        self.provider ="aws"


    def validate(self):
        super().validate()

        # validate params
        if self.import_module == "infra":
            pass
        else:
            required_fields = ["tenant_name", "aws_region"]
            self._check_required_fields(required_fields)

        if self.download_aws_keys == "yes":
            required_fields=["url","tenant_id","api_token"]
            self._check_required_fields(required_fields)



class AzureImportParameters(ImportParametersBase):
    provider = "azure"
    def __init__(self):
        parameters = ["tenant_name" ,
                      "import_module",
                    "import_name" ,
                    "zip_file_path" ,
                    "params_json_file_path",
                    "download_aws_keys",
                    "tenant_id",
                    "api_token",
                    "url",
                    "aws_region"]
        super.__init__( AzureImportParameters, parameters)
        self.provider = "azure"



class GcpImportParameters(ImportParametersBase):
    provider = "google"
    def __init__(self):
        parameters = ["tenant_name" ,
                      "import_module",
                    "import_name" ,
                    "zip_file_path" ,
                    "params_json_file_path",
                    "download_aws_keys",
                    "tenant_id",
                    "api_token",
                    "url",
                    "aws_region"]
        super.__init__( AzureImportParameters, parameters)
        self.provider ="google"

class KubernetesImportParameters(ImportParametersBase):
    provider = "kubernetes"
    def __init__(self):
        parameters = ["tenant_name" ,
                      "import_module",
                    "import_name" ,
                    "zip_file_path" ,
                    "params_json_file_path",
                    "download_aws_keys",
                    "tenant_id",
                    "api_token",
                    "url",
                    "aws_region"]
        super.__init__( AzureImportParameters, parameters)
        self.provider ="kubernetes"
