import psutil
import os
import datetime
import argparse
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.params.config import get_help, arg_params


class TfModule:
    def __init__(self, is_tenant, is_key_download, name, tenant_id, tenant_token):
        self.is_tenant = is_tenant
        self.is_key_download = is_key_download
        self.name = name
        self.tenant_id = tenant_id
        self.tenant_token = tenant_token


class ArgParse:

    def __init__(self, provider, args_param_list, default_params):
        self.provider = provider
        self.args_param_list = args_param_list
        self.default_params = default_params


    ######## ####  parser   ######## ####
    def get_parser(self):
        help = get_help(self.args_param_list, self.provider)
        parser = argparse.ArgumentParser(description="Download Terraform state files.", usage=help)
        for attr_name in self.args_param_list:
            parser.add_argument('-' + arg_params[attr_name]['short_name'],
                                '--' + attr_name, action='store', dest=attr_name)
        return parser

    def infer_import_module(self, default_import_module="all"):
        self.import_module = None  # for now neglect and derive
        if self.import_module is None:
            if self.tenant_name is None:
                self.import_module = default_import_module
            else:
                if self.tenant_name in ["all", "infra"]:
                    self.import_module = self.tenant_name
                elif "," in self.tenant_name:
                    self.import_module = "tenantlist"
                else:
                    self.import_module = default_import_module

    def parsed_args(self, parsed_args):
        self.parsed_args_params = parsed_args
        params = self.default_params

        file_utils = TfFileUtils(params)
        # parameters = self.file_utils.load_json_file(self.default_params_path)
        #
        print("########## default parameters ########## ")
        for key in params:
            print(" default parameter values", key, params[key])
        #
        print("########## passed as environ variables  ########## ")
        for key in params:
            if key in os.environ:
                print(" override parameter by passed as environ variable ", key, os.environ[key])
                val = os.environ[key]
                params[key] = val
        #
        print("########## params_json_file_path parameters ########## ")
        if parsed_args.params_json_file_path is not None:
            print("params_json_file_path ", parsed_args.params_json_file_path)
            parameters_json = file_utils.load_json_file(parsed_args.params_json_file_path)
            for key in parameters_json:
                print(" params_json_file_path parameter values", key, parameters_json[key])
                params[key] = parameters_json[key]
        #
        print("########## passed as arguments parameters ########## ")
        for key, val in vars(parsed_args).items():
            if val is not None:
                print(" override parameter by passed in arguments ", key, val)
                params[key] = val

        print("########## after merge all parameters ########## ")
        for key in params:
            print(" after merge all parameters ", key, params[key])
        return params

    def getTfModules(self, params):
        params = self._set_defaults(params)
        tenants = []
        tenant_ids = []
        tenant_name = params['tenant_name']
        tenant_id = params['tenant_id']

        import_module = params['import_module']
        if  import_module in ["tenant", None, ""]:
            import_module = "tenant"
            params['import_module']= "tenant"

        if  tenant_id is None:
            params['tenant_id'] = ""
            tenant_id = ""

        if  tenant_id is None:
            params['tenant_id'] = ""
            tenant_id = ""

        if import_module in ["tenant", "tenant_list"] and params['download_aws_keys'] == "yes":
            params['is_tenant_id_needed'] = True
            required_fields = ["url", "tenant_id", "api_token"]
            self._check_required_fields( required_fields)


        if import_module in ["infra", "all"]:
            tenants.append(import_module)
            tenant_ids.append("")
        elif import_module  == "tenant":
            if "," in tenant_name or "," in tenant_id:
                self._raise_error(self.parsed_args_params, "Exception: import_module=tenant - more thann one tenant is provided.")
            tenants.append(tenant_name)
            tenant_ids.append(tenant_id)
        elif import_module == "tenant_list":
            tenants.append("infra")
            tenant_ids.append("infra")
            tenants_arr = tenant_name.split(",")
            for tenant in tenants_arr:
                tenant = tenant.strip()
                if tenant != "":
                    tenants.append(tenant)
            tenant_ids_arr = tenant_id.split(",")
            for tenant_id in tenant_ids_arr:
                tenant_id = tenant_id.strip()
                if tenant_id != "":
                    tenant_ids.append(tenant_id)
            if len(tenants_arr) != len(tenant_ids_arr):
                self._raise_error(self.parsed_args_params, "Exception: import_module=tenant_list - count not matching for tenant_names and tenant_ids, should be equal.")

        tf_modules = {}
        is_tenant_id_needed = params['is_tenant_id_needed']
        api_token = params['api_token']
        is_key_download =  is_tenant_id_needed
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

    ############ helpers ########################
    def _raise_error(self, params, message):
        print("============== ERROR ============== ")
        print(message)
        print("============== USAGE ============== ")
        print(get_help(params, self.provider))
        print("============== Exception ============== ")
        raise Exception(message)

    def _check_required_fields(self, required_fields):
        parameters = vars(self.parsed_args_params,)
        self.validate_required_fields(parameters, required_fields)

    def validate_required_fields(self, parameters, required_fields):
        # parameters = vars(self.parsed_args_params,)
        for required_field in required_fields:
            if required_field not in parameters or parameters[required_field] is None or parameters[
                required_field] == "":
                fields = ",".join(required_fields)
                print("Missing required_fields = " + " ".join(parameters))
                self._raise_error(parameters, "Exception: Missing required_fields = " + fields)

    def _set_defaults(self, params):
        if params['import_module'] in ["tenant", None, ""]:
            params['import_module'] = "tenant"

        if params['tenant_id'] is None:
            params['tenant_id'] = ""

        if params['tenant_name'] is None:
            params['tenant_name'] = ""

        return params