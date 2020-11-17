from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import random
import os
import json
from datetime import datetime


class AzurermTfStep4NewStack(AzureBaseTfImportStep):
    # dict
    states_dict = {}
    resources_dict = {}

    # dict with ids
    resources_by_id_dict = {}
    states_by_id_dict = {}
    states_tf_var_by_id_dict = {}

    # main
    main_tf_text = ""
    main_tf_dict = {}

    # track variables to be created
    variable_list_dict = {}
    # variable index
    index = 0
    # existing res_groups
    res_groups = {}

    # to avoid duplicates
    unique_resource_groups_dict = {}
    unique_dep_ids_dict = {}

    # tenant_names
    tenant_names_dict = {}
    # duploservices-azdemo1

    tf_import_sh_list = []

    def __init__(self, params):
        super(AzurermTfStep4NewStack, self).__init__(params)
        random.seed(datetime.now())
        self.tf_import_sh_list = []
        self.tf_import_sh_list.append("")

    def execute(self):
        self._load_files()
        # self._gen_interpolation_ids_for_res()
        # self._states_by_id_dict()
        # self._tf_resources()
        self._create_tf_state()
        return self.file_utils.tf_main_file()

    def _create_tf_state(self):
        self._plan()
        self._save_files("")
        self.file_utils.save_tf_import_script(self.tf_import_sh_list)
        self.file_utils.save_tf_run_script()
        self.file_utils.create_state(self.file_utils.tf_run_script())

    def _plan(self):
        self.tf_import_sh_list.append('terraform init ')
        self.tf_import_sh_list.append('terraform refresh ')
        self.tf_import_sh_list.append('terraform plan -var-file=terraform.tfvars.json')


    ######  TfImportStep3 ################################################
    def _tf_resources(self):
        try:
            self._parameterize()
            print("DONE")
        except Exception as e:
            print("ERROR:AzurermTfStep3NewStack:", "_tf_resources", e)

    def _parameterize(self):
        self._res_group_vars()
        resource_types = self.main_tf_dict["resource"]
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                try:
                    resource = resources[resource_key]
                    try:
                        pass
                       # self._parameterize_for_res(resource_type, resource)
                    except Exception as e:
                        print("ERROR:AzurermTfStep3NewStack:1", "_parameterize", e)


                except Exception as e:
                    print("ERROR:AzurermTfStep3NewStack:3", "_parameterize", e)

    ##### helper load and save files ##############
    def _parameterize_for_res(self, resource_type, resource):

        if resource_type in ['azurerm_mysql_server', 'azurerm_postgresql_server']:
            if "administrator_login" in resource:
                name = resource["administrator_login"]
                self.index = self.index + 1
                var_name = "{0}_{1}_administrator_login".format(resource_type, self.index)
                resource["administrator_login"] = "${var." + var_name + "}"
                self.variable_list_dict[var_name] = name

        if resource_type in ["azurerm_virtual_machine"]:
            if "os_profile" in resource:
                resource_profiles = resource["os_profile"]
                for resource in resource_profiles:
                    # user_name
                    if "admin_username" in resource:
                        name = resource["admin_username"]
                    else:
                        name = "admin_username"
                    self.index = self.index + 1
                    var_name = "{0}_{1}_admin_username".format(resource_type, self.index)
                    resource["admin_username"] = "${var." + var_name + "}"
                    self.variable_list_dict[var_name] = name
    ##### helper load and save files ##############

    def _load_files(self):
        # verify import worked
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()
        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception("Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")

        # paths
        self.main_tf_read_from_file = self.file_utils.tf_main_file_for_step("step3")
        self.resources_read_from_file = self.file_utils.tf_resources_file_for_step("step3")
        self.terraform_tfvars_json_file = self.file_utils.file_in_step("step3", "terraform.tfvars.json")
        self.variables_tf_json_file = self.file_utils.file_in_step("step3", "variables.tf.json")

        # load
        self.states_dict = self.file_utils.load_json_file(self.state_read_from_file)

        #
        self.resources_dict = self.file_utils.load_json_file(self.resources_read_from_file)
        self.main_tf_dict = self.file_utils.load_json_file(self.main_tf_read_from_file)
        #
        self.variable_list_dict =  self.file_utils.load_json_file(self.terraform_tfvars_json_file)
        self.variables_tf_dict  =  self.file_utils.load_json_file(self.variables_tf_json_file)
        self.index = len(self.variable_list_dict.keys())


    def _save_files(self, folder):
        self.file_utils.save_to_json(self.file_utils.tf_resources_file(), self.resources_dict)
        self.file_utils.save_to_json(self.file_utils.tf_state_file(), self.states_dict)
        self.file_utils.save_to_json(self.file_utils.tf_main_file(), self.main_tf_dict)

        self._copy_text_file("replace.py")
        self._copy_text_file("parameterization.md")
        self.file_utils.save_json_to_work_folder("terraform.tfvars.json", self.variable_list_dict)

        ## save variables.tf.json
        self.variables_tf_dict = {}
        variables_tf_root = {}
        self.variables_tf_dict["variable"] = variables_tf_root
        for variable_name in self.variable_list_dict:
            variables_tf_root[variable_name] = {
                "description": "value e.g." + self.variable_list_dict[variable_name]
            }
        self.file_utils.save_json_to_work_folder("variables.tf.json", self.variables_tf_dict)

    def _copy_text_file(self, filename):
        try:
            src_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            dest_file = self.file_utils._file_inwork_folder(filename)
            replace_py = self.file_utils.file_read_as_text(src_file)
            self.file_utils.file_save_as_text(dest_file, replace_py)
        except Exception as e:
            print("ERROR:AzurermTfStep3NewStack:", "_states_by_id_dict", e)
