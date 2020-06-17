import json
import os
import datetime
import argparse
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.step1.aws_create_tfstate_step1 import AwsCreateTfstateStep1
from duplocli.terraform.aws.step1.get_aws_object_list import GetAwsObjectList
from duplocli.terraform.aws.step2.aws_tf_import_step2 import AwsTfImportStep2
from duplocli.terraform.aws.common.tf_file_utils import TfFileUtils
import psutil


class ImportParameters:
    tenant_name = None

    def __init__(self, parameters):

        self.tenant_name = self.get_key(parameters, 'tenant_name')
        self.aws_region = self.get_key(parameters, 'aws_region')
        self.zip_folder = self.get_key(parameters, 'zip_folder')
        self.zip_file_path = self.get_key(parameters, 'zip_file_path')
        self.import_name = self.get_key(parameters, 'import_name')


        self.download_aws_keys = self.get_key(parameters, 'download_aws_keys')
        self.url = self.get_key(parameters, 'url')
        self.tenant_id = self.get_key(parameters, 'tenant_id')
        self.api_token = self.get_key(parameters, 'api_token')

        self.params_json_file_path = self.get_key(parameters, 'params_json_file_path')
        self.temp_folder = self.get_key(parameters, 'temp_folder')
        self.tenant_with_prefix = self.get_key(parameters, 'tenant_with_prefix')
        self.state_file = self.get_key(parameters, 'state_file')


    def get_key(self, parameters, key):
        if key in parameters:
            return parameters[key]
        return None

class AwsParseParams:

    def __init__(self):
        self.file_utils = TfFileUtils(self.get_default_params(), step="step1")

    ######## ####
    def check_required_fields(self,parameters,  required_fields):
        for required_field in required_fields:
            if parameters[required_field] is None:
                fields=",".join(required_fields)
                print("missing required_fields = " + parameters)
                print(self.get_help())
                raise Exception("missing required_fields = " +fields)

    def resolve_parameters(self, parsed_args):
        parameters = self.app_defaults(parsed_args)
        # validate params
        required_fields = ["tenant_name",  "aws_region"]
        self.check_required_fields(parameters, required_fields)
        if parameters["download_aws_keys"] == "yes":
            required_fields=["url","tenant_id","api_token"]
            self.check_required_fields(parameters, required_fields)
        params = ImportParameters(parameters)
        if params.zip_file_path is None:
            if params.import_name is None:
                now = datetime.datetime.now()
                now_str = now.strftime("%m-%d-%Y--%H-%M-%S")
                params.import_name = now_str
            #append import_name to zip_file_path, zip_folder, temp_folder
            params.temp_folder = os.path.join(params.temp_folder, params.tenant_name, params.import_name)
            params.zip_folder = os.path.join(params.temp_folder, "zip")
            params.zip_file_path = os.path.join(params.zip_folder, params.import_name)
            print("zip_file_path  ***** ", os.path.abspath(params.zip_file_path+".zip") )

        return params


    ######## ####
    def get_default_params(self):
        file_utils = TfFileUtils(None, step=None, set_temp_and_zip_folders=False)
        parameters = file_utils.load_json_file("import_tf_parameters_default.json")
        params = ImportParameters(parameters)
        return params


    def get_help(self):
        return """

        argument to python file

        [-t / --tenant_id TENANTID]           -- TenantId e.g. 97a833a4-2662-4e9c-9867-222565ec5cb6
        [-n / --tenant_name TENANTNAME]         -- TenantName e.g. webdev
        [-r / --aws_region AWSREGION]          -- AWSREGION  e.g. us-west2
        [-a / --api_token APITOKEN]           -- Duplo API Token
        [-u / --url URL]                -- Duplo URL  e.g. https://msp.duplocloud.net
        [-k / --download_aws_keys DOWNLOADKEYS]       -- Aws keypair=yes/no, private key used for ssh into EC2 servers
        [-z / --zip_folder ZIPFOLDER]          -- folder to save imported  files in zip format
                self.import_name = self.get_key(parameters, 'import_name')
        [-i / --import_name IMPORTNAME]            -- import name and zip file path are mutually exclusive.  import name will create sub folders and zip file with same name.    
        [-o / --zip_file_path ZIPFILEPATH]         -- zip file path to save imported terraform files in zip format        
        [-j / --params_json_file_path PARAMSJSONFILE]     -- All params passed in single JSON file
        [-h / --help HELP]               -- help



        OR alternately 

        pass the above parameters in single json file

       [-j/--params_json_file_path PARAMSJSONFILE] = FOLDER/terraform_import_json.json
            terraform_import_json.json
            {
              "tenant_name": "xxxxxx",
              "aws_region": "xxxxxx",
              "zip_folder": "zip",
              "download_aws_keys": "yes",
              "url": "https://xxx.duplocloud.net",
              "tenant_id": "xxx-2662-4e9c-9867-9a4565ec5cb6",
              "api_token": "xxxxxx",
              "import_name":"UNIQUE_NAME"
            }

        OR alternately 
        pass the above parameters in ENV variables
        export tenant_name="xxxxxx"
        export aws_region="xxxxxx"
        export zip_folder="zip",
        export download_aws_keys="yes",
        export url="https://xxx.duplocloud.net",
        export tenant_id="xxx-2662-4e9c-9867-9a4565ec5cb6",
        export api_token="xxxxxx"
        export zip_file_path="/tmp/NAMe.zip" or export import_name="UNIQUE_NAME"
        

        Sequence of parameters evaluation is: default -> ENV -> JSON_FILE -> arguments
        parameters in argument 
         ->  override  parameters in terraform_import_json
        AND parameters in terraform_import_json
         ->   override  parameters in ENV variables
        AND parameters in ENV variables
         ->   override default values (import_tf_parameters_default.json)
        """

    ######## ####

    def get_parser(self):
        help_str = self.get_help()
        # parser = argparse.ArgumentParser(prog='AwsTfImport',add_help=False)
        # parser = argparse.ArgumentParser(description="Download Terraform state files.", argument_default=argparse.SUPPRESS,
        #                         allow_abbrev=False, add_help=False)
        parser = argparse.ArgumentParser(description="Download Terraform state files.", usage=self.get_help())

        parser.add_argument('-t', '--tenant_id', action='store', dest='tenant_id')
        parser.add_argument('-n', '--tenant_name', action='store', dest='tenant_name')
        parser.add_argument('-r', '--aws_region', action='store', dest='aws_region')
        parser.add_argument('-a', '--api_token', action='store', dest='api_token')
        parser.add_argument('-u', '--url', action='store', dest='url')
        parser.add_argument('-k', '--download_aws_keys', action='store', dest='download_keys')
        parser.add_argument('-z', '--zip_folder', action='store', dest='zip_folder')
        parser.add_argument('-i', '--import_name', action='store', dest='import_name')
        parser.add_argument('-o', '--zip_file_path', action='store', dest='zip_file_path')
        parser.add_argument('-j', '--params_json_file_path', action='store', dest='params_json_file_path')
        # parser.add_argument('-h', '--help', action='help' , help=" params usage")
        return parser



    ######## ####

    def app_defaults(self, parsed_args):
        parameters = self.file_utils.load_json_file("import_tf_parameters_default.json")
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

        print("########## final parameters ########## ")
        for key in parameters:
            print("final", key, parameters[key])

        return parameters



