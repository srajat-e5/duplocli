from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import random
import os
import json
from datetime import datetime
import psutil

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
        self.tf_import_sh_list.append("")

    def execute(self):
        self._load_files()
        # self._gen_interpolation_ids_for_res()
        # self._states_by_id_dict()
        self._tf_resources()
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
            print("DONE new stack")
        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:Step4: _tf_resources {0}".format(e))
            print("ERROR:Step4:", "_tf_resources", e)

    def _skip_remove_resources(self, resource_types):
        if "azurerm_managed_disk" in resource_types:
            self._del_key(resource_types , "azurerm_managed_disk")
        if "azurerm_virtual_machine_extension" in resource_types:
            self._del_key(resource_types , "azurerm_virtual_machine_extension")

    def _parameterize(self):
        #
        resource_types = self.main_tf_dict["resource"]
        # azure auto creates them?
        self._skip_remove_resources(resource_types)
        #
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                try:
                    resource = resources[resource_key]
                    try:
                       self._parameterize_for_res(resource_type, resource)
                    except Exception as e:
                        self.file_utils._save_errors(e,"ERROR:Step4: _parameterize {0}".format(e))
                        print("ERROR:Step4:1", "_parameterize", e)


                except Exception as e:
                    self.file_utils._save_errors(e,"ERROR:Step4: _parameterize {0}".format(e))
                    print("ERROR:Step4:3", "_parameterize", e)

    ##### helper load and save files ##############
    def _parameterize_for_res(self, resource_type, resource):
        "azurerm_network_interface ip_configuration public_ip_address_id"
        if resource_type in ["azurerm_network_interface"]:
            if "ip_configuration" in resource:
                ip_configurations = resource["ip_configuration"]
                for ip_configuration in ip_configurations:
                    if "public_ip_address_id" in ip_configuration:
                        #not sure what is side effect of this... enable public ip afterwords?
                        self._del_key(ip_configuration, "public_ip_address_id")
        # azurerm_managed_disk disk_iops_read_write and disk_mbps_read_write
        #.azurerm_managed_disk disk_iops_read_write
        if resource_type in ['azurerm_managed_disk' ]:
            self._del_key(resource, "disk_iops_read_write")
            self._del_key(resource, "disk_mbps_read_write")
        # print(resource_type)
        if resource_type in ['azurerm_mysql_server', 'azurerm_postgresql_server', 'azurerm_sql_server']:
            if "administrator_login_password" not in resource:
                # administrator_login_password = resource["administrator_login"]
                if "administrator_login" in self.variable_list_dict:
                    var_name = self.variable_list_dict["administrator_login"].replace("administrator_login", "administrator_login_password")
                else:
                    self.index = self.index + 1
                    var_name = "{0}_{1}_administrator_login_password".format(resource_type, self.index)
                resource["administrator_login_password"] = "${var." + var_name + "}"
                self.variable_list_dict[var_name] = self.password_const

        if resource_type in ["azurerm_virtual_machine"]:
            if "os_profile" in resource:
                resource_profiles = resource["os_profile"]
                for resource in resource_profiles:
                    if "admin_password" in self.variable_list_dict:
                        var_name = self.variable_list_dict["admin_password"].replace("admin_password",
                                                                                          "admin_password")
                    else:
                        self.index = self.index + 1
                        var_name = "{0}_{1}_admin_password".format(resource_type, self.index)
                    resource["admin_password"] = "${var." + var_name + "}"
                    self.variable_list_dict[var_name]  = self.password_const
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
        #self.file_utils.save_to_json(self.file_utils.tf_state_file(), self.states_dict)
        self.file_utils.save_to_json(self.file_utils.tf_main_file(), self.main_tf_dict)

        self._copy_text_file("replace.py")
        self._copy_text_file("parameterization.md")
        self._copy_text_file("replace_azdemo1.sh")

        self.file_utils.save_json_to_work_folder("terraform.tfvars.json", self.variable_list_dict)

        ## save variables.tf.json
        self.variables_tf_dict = {}
        variables_tf_root = {}
        self.variables_tf_dict["variable"] = variables_tf_root
        for variable_name in self.variable_list_dict:
            variables_tf_root[variable_name] = {
                # "description": "value e.g." + self.get_string(self.variable_list_dict[variable_name])
                "description": "value e.g. {0}".format(  self.variable_list_dict[variable_name])
            }
        self.file_utils.save_json_to_work_folder("variables.tf.json", self.variables_tf_dict)

    def _copy_text_file(self, filename):
        try:
            src_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            dest_file = self.file_utils._file_inwork_folder(filename)
            replace_py = self.file_utils.file_read_as_text(src_file)
            self.file_utils.file_save_as_text(dest_file, replace_py)
        except Exception as e:
            self.file_utils._save_errors(e,"ERROR:Step4: _copy_text_file {0}".format(e))
            print("ERROR:Step4:", "_states_by_id_dict", e)
