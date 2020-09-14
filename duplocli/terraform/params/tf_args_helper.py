import psutil
import os
import datetime
import argparse
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.params.params_config import get_help, arg_params
from duplocli.terraform.params.tf_module import TfModule


class TfArgsHelper:

    def __init__(self):
        print(self.provider)

    ############  validate   ############
    def validate_and_update_modules(self):
        # is tenant_id, api_token, url  are needed?
        if self.import_module in ["tenant", "tenant_list"] and self.download_aws_keys == "yes":
            self.is_tenant_id_needed = True
        # validate
        self._validate_download_keys()
        self._validate_tenants()
        # update params with tenants and tenant_ids
        self.tf_modules = self._update_modules()

    ### module and tenant scope
    def _validate_download_keys(self):
        if self.is_tenant_id_needed:
            required_fields = ["url", "tenant_id", "api_token"]
            self._check_required_fields(required_fields)

    def _validate_tenants(self):
        params = self
        if self.import_module in ["infra", "all"]:
            return
        elif self.import_module in ["tenant", None, ""]:
            self.import_module = "tenant"
            if "," in self.tenant_name or "," in self.tenant_id:
                self._raise_error("Exception: import_module=tenant - more thann one tenant is provided.")
        elif self.import_module == "tenant_list":
            if self.is_tenant_id_needed:
                tenants_arr, tenant_ids_arr = self._parse_tenants()
                if len(tenants_arr) != len(tenant_ids_arr):
                    self._raise_error(
                        "Exception: import_module=tenant_list - count not matching for tenant_names and tenant_ids, should be equal.")

    def _parse_tenants(self):
        tenants = []
        tenant_ids = []
        params = self
        if self.import_module in ["infra", "all"]:
            tenants.append(self.import_module)
            tenant_ids.append("")
        elif self.import_module in ["tenant", None, ""]:
            tenants.append(self.tenant_name)
            tenant_ids.append(self.tenant_id)
        elif self.import_module == "tenant_list":
            tenants.append("infra")
            tenant_ids.append("infra")
            tenants_arr = self.tenant_name.split(",")
            for tenant in tenants_arr:
                tenant = tenant.strip()
                if tenant != "":
                    tenants.append(tenant)
            tenant_ids_arr = self.tenant_id.split(",")
            for tenant_id in tenant_ids_arr:
                tenant_id = tenant_id.strip()
                if tenant_id != "":
                    tenant_ids.append(tenant_id)
        return tenants, tenant_ids

    def _update_modules(self):
        tf_modules = {}
        is_key_download = self.is_tenant_id_needed
        api_token = self.api_token
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
        print(get_help(self))
        print("============== Exception ============== ")
        raise Exception(message)

    def _check_required_fields(self, required_fields):
        parameters = vars(self)
        for required_field in required_fields:
            if required_field not in parameters or parameters[required_field] is None or parameters[
                required_field] == "":
                fields = ",".join(required_fields)
                print("Missing required_fields = " + " ".join(parameters))
                self._raise_error("Exception: Missing required_fields = " + fields)

    ######## ####  parser   ######## ####
    def get_parser(self, ):
        help = get_help(self)
        parser = argparse.ArgumentParser(description="Download Terraform state files.", usage=help)
        for attr_name in self.attr_names:
            parser.add_argument('-' + arg_params[attr_name]['short_name'],
                                '--' + attr_name, action='store', dest=attr_name)
        return parser

    def parsed_args(self, parsed_args):
        self.file_utils = TfFileUtils(self)
        parameters = self.file_utils.load_json_file(self.default_params_path)
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
        if self.tenant_id is None:
            self.tenant_id = ""
        if self.import_module in ["tenant", None, ""]:
            self.import_module = "tenant"

        print("########## final parameters ########## ")
        parameters_cur = vars(self)
        for key in parameters_cur:
            print("final", key, getattr(self, key))
        #
        return parameters

    def _set_attributes(self, parameters):
        key_list = list(parameters.keys())
        att_name_list = self.attr_names + key_list
        for att_name in att_name_list:
            value = self._from_dict(parameters, att_name)
            setattr(self, att_name, value)

    def _from_dict(self, parameters, key):
        if key in parameters:
            return parameters[key]
        return None

    def _create_work_file_paths(self):
        params = self
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
        self.temp_folder_path = self.temp_folder
        self.zip_folder_path = self.zip_folder



