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
        print("is WINDOWS ", psutil.WINDOWS)

    ######## ####
    def resolve_parameters(self, parsed_args):
        parameters = self.app_defaults(parsed_args)
        params = ImportParameters(parameters)
        return params


    ######## ####
    def get_default_params(self):
        file_utils = TfFileUtils(None, step="step1")
        parameters = file_utils.load_json_file("default_parameters.json")
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
        [-z / --zip_folder ZIPFOLDER]          -- folder to save imported terrorform files in zip format
        [-o / --zip_file_path ZIPFILEPATH]         -- zip file path to save imported terrorform files in zip format        
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
              "zip_file_path":"/tmp/NAMe.zip"
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
        export zip_file_path="/tmp/NAMe.zip"
        

        Sequence of parameters evaluation is: default -> ENV -> JSON_FILE -> arguments
        parameters in argument 
         ->  override  parameters in terraform_import_json
        AND parameters in terraform_import_json
         ->   override  parameters in ENV variables
        AND parameters in ENV variables
         ->   override default values (default_parameters.json)
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
        parser.add_argument('-o', '--zip_file_path', action='store', dest='zip_file_path')
        parser.add_argument('-j', '--params_json_file_path', action='store', dest='params_json_file_path')
        # parser.add_argument('-h', '--help', action='help' , help=" params usage")
        return parser



    ######## ####

    def app_defaults(self, parsed_args):
        parameters = self.file_utils.load_json_file("default_parameters.json")
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



