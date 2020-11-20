from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import random
import os
import json
from datetime import datetime

class AzurermTfStep3ParamStack(AzureBaseTfImportStep):
    # dict
    states_dict = {}
    resources_dict = {}

    # dict with ids
    resources_by_id_dict = {}
    states_by_id_dict = {}
    states_tf_var_by_id_dict = {}
    id_by_type_and_var_name_dict = {}

    # main
    main_tf_dict = {}

    # track variables to be created
    variable_list_dict = {}
    # variable index
    index = 0
    # existing res_groups
    res_groups = {}

    # to avoid duplicates
    unique_dep_ids_dict = {}

    # tenant_names
    tenant_names_dict = {}

    tf_import_sh_list = []

    def __init__(self, params):
        super(AzurermTfStep3ParamStack, self).__init__(params)
        random.seed(datetime.now())
        self.tf_import_sh_list = []
        self.tf_import_sh_list.append("")

    def execute(self):
        self._load_files()
        self._gen_interpolation_ids_for_res()
        self._states_by_id_dict()
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
            print("step3 successful - DONE")
        except Exception as e:
            self.file_utils._save_errors("ERROR:Step3: _tf_resources {0}".format(e))
            print("ERROR:AzurermTfStep3NewStack:", "_tf_resources", e)

    def _parameterize(self):
        self._interpolation_for_res_grps()
        resource_types = self.main_tf_dict["resource"]
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                try:
                    resource = resources[resource_key]

                    try:
                        self._parameterize_for_res_grp(resource_type, resource)
                    except Exception as e:
                        self.file_utils._save_errors("ERROR:Step3:1: _parameterize {0}".format(e))
                        print("ERROR:AzurermTfStep3NewStack:1", "_parameterize", e)

                    try:
                        self._parameterize_for_res(resource_type, resource)
                    except Exception as e:
                        self.file_utils._save_errors("ERROR:Step3:2: _parameterize {0}".format(e))
                        print("ERROR:AzurermTfStep3NewStack:2", "_parameterize_for_res", e)

                    try:
                        self._parameterize_res_for_dep_ids(resource_type, resource)
                    except Exception as e:
                        self.file_utils._save_errors("ERROR:Step3:3: _parameterize {0}".format(e))
                        print("ERROR:AzurermTfStep3NewStack:3", "_parameterize", e)

                    try:
                        self._fix_vnet_and_subnet(resource_type, resource)
                    except Exception as e:
                        self.file_utils._save_errors("ERROR:Step3:2: _parameterize {0}".format(e))
                        print("ERROR:AzurermTfStep3NewStack:2", "_parameterize_for_res", e)

                except Exception as e:
                    self.file_utils._save_errors("ERROR:Step3:4: _parameterize {0}".format(e))
                    print("ERROR:AzurermTfStep3NewStack:4", "_parameterize", e)


    ############## /subscriptions/extract them to variables as they are missing in import dependency list #############

    def _parameterize_for_res(self, resource_type, resource):
        if resource_type in ["azurerm_storage_account", "azurerm_app_service", "azurerm_app_service_plan",
                             'azurerm_mysql_server', 'azurerm_postgresql_server']:
            if "name" in resource:
                name = resource["name"]
                self.index = self.index + 1
                var_name = "{0}_{1}_name".format(resource_type, self.index)
                resource["name"] = "${var." + var_name + "}"
                self.variable_list_dict[var_name] = name
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

    def _parameterize_for_res_grp(self, resource_type, resource):
        if resource_type == "azurerm_resource_group":
            resource_group_name = resource["name"].lower()
            resource_group_vars = self.res_groups[resource_group_name]
            resource["name"] = "${var." + resource_group_vars["var_res_grp_name"] + "}"
            resource["location"] = "${var." + resource_group_vars["var_res_grp_loc"] + "}"
        else:
            if "resource_group_name" in resource:
                resource_group_name = resource["resource_group_name"].lower()
                if resource_group_name  in self.res_groups:
                    resource_group_vars = self.res_groups[resource_group_name ]
                else:
                    resource_group_vars = self.res_groups[resource_group_name]
                resource["resource_group_name"] = "${" + resource_group_vars["interpolation_res_grp_id"] + "}"
                if "location" in resource:
                    resource["location"] = "${" + resource_group_vars["interpolation_res_grp_loc"] + "}"

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############

    ###### interpolation for_res_grps #############

    def _interpolation_for_res_grps(self):
        resource_types = self.main_tf_dict["resource"]
        self.res_groups = {}
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                resource = resources[resource_key]
                if resource_type == "azurerm_resource_group":
                    location = resource["location"]
                    resource_group_name = resource["name"].lower()
                    if resource_group_name not in self.res_groups:
                        self.index = self.index + 1
                        resource_group_vars = self.__interpolation_for_res_grp(self.index, resource_group_name,
                                                                               location, True, resource["name"])
                        self.res_groups[resource_group_name] = resource_group_vars

        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                resource = resources[resource_key]
                if resource_type != "azurerm_resource_group":
                    if "resource_group_name" in resource and "location" in resource:
                        location = resource["location"]
                        resource_group_name = resource["resource_group_name"].lower()
                        if resource_group_name not in self.res_groups or resource_group_name.lower() not in self.res_groups:
                            self.index = self.index + 1
                            resource_group_vars = self.__interpolation_for_res_grp(self.index, resource_group_name,
                                                                                   location, False)
                            self.res_groups[resource_group_name] = resource_group_vars


    def __interpolation_for_res_grp(self, index, resource_group_name, location, exists_in_import, resource_group_name_origin):
        try:
            var_res_grp_name = "resource_group_{0}_name".format(index)
            var_res_grp_loc = "resource_group_{0}_location".format(index)
            #
            self.variable_list_dict[var_res_grp_name] = resource_group_name_origin #resource_group_name
            self.variable_list_dict[var_res_grp_loc] = location
            #
            interpolation_res_grp_id = "azurerm_resource_group.{0}.name".format(resource_group_name)
            interpolation_res_grp_loc = "azurerm_resource_group.{0}.location".format(resource_group_name)
            resource_group_vars = {
                "location": location,
                "resource_group_name": resource_group_name,
                "index": index,
                "var_res_grp_name": var_res_grp_name,
                "var_res_grp_loc": var_res_grp_loc,
                "interpolation_res_grp_id": interpolation_res_grp_id,
                "interpolation_res_grp_loc": interpolation_res_grp_loc,
                "exists_in_import": exists_in_import
            }
            return resource_group_vars
        except Exception as e:
            self.file_utils._save_errors("ERROR:Step3:2: _interplation_for_res_grp {0}".format(e))
            print("ERROR:AzurermTfStep3NewStack:1", "_interplation_for_res_grp", e)

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############

    def _parameterize_res_for_dep_ids(self, resource_type, resource):
        resource_obj_parent = resource
        for attribute_name, attribute in resource.items():
            try:
                if isinstance(attribute, dict):
                    self._parameterize_util_dict_for_dep_ids(resource_obj_parent, attribute_name, attribute)
                elif isinstance(attribute, list):
                    is_string = False
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._parameterize_util_dict_for_dep_ids(attribute, attribute_name, nested_item)
                        elif isinstance(nested_item, list):
                            print("isinstance(attribute, list):", "_process_dict", attribute_name)
                        else:
                            is_string = True
                    if is_string:
                        self._get_unique_tf_variable(attribute, attribute_name, nested_item, True)
                else:
                    self._get_unique_tf_variable(resource_obj_parent, attribute_name, attribute, False)

            except Exception as e:
                self.file_utils._save_errors("ERROR:Step3:2: _create_var {0}".format(e))
                print("ERROR:Step2:", "_create_var", e)

    def _parameterize_util_dict_for_dep_ids(self, resource_obj_parent, nested_atr_name, nested_atr):
        for attribute_name, attribute in nested_atr.items():
            try:
                if isinstance(attribute, list):
                    is_string = False
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._parameterize_util_dict_for_dep_ids(attribute, nested_atr_name, nested_item)
                        elif isinstance(nested_item, list):
                            print("isinstance(attribute, list):", "_process_dict", nested_atr_name)
                        else:
                            is_string = True
                    if is_string:
                        self._get_unique_tf_variable(nested_atr, attribute_name, attribute, True)
                else:
                    self._get_unique_tf_variable(nested_atr, attribute_name, attribute, False)
            except Exception as e:
                self.file_utils._save_errors("ERROR:Step3:2: _process_dict {0}".format(e))
                print("ERROR:Step2:", "_process_dict", e)

    def _get_unique_tf_variable(self, attribute, nested_atr_name, value, is_list):
        # array or string?
        if value is None:
            return value
        # its bug
        if nested_atr_name not in attribute:
            return value

        if isinstance(value, list):
            found = False
            values = []  # array of ids?
            for value_item in value:
                if value_item is not None and "{0}".format(value_item).startswith("/subscriptions/"):
                    variable_id = self._get_variable_id_for_dep_id(value_item)
                    values.append(variable_id)
                    found = True
            if found:
                attribute[nested_atr_name] = values
                return values
        else:
            if "{0}".format(value).startswith("/subscriptions/"):
                if nested_atr_name in attribute:
                    # print(is_list, "@@@@found ",nested_atr_name, value )
                    variable_id = self._get_variable_id_for_dep_id(value)
                    attribute[nested_atr_name] = variable_id
                    return variable_id
                else:
                    print(is_list, "@@@@NOT found ", nested_atr_name, value, attribute)
                # print( nested_atr_name, value)
        return value

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############
    def _get_variable_id_for_dep_id(self, id):
        if "azurerm_user_assigned_identity" in id:
            pass
        if self._get_states_tf_var_by_id_dict(id) is not None:
            var_name_repl = "${" + self._get_states_tf_var_by_id_dict(id) + ".id}"
        elif id in self.unique_dep_ids_dict:
            var_name_repl = self.unique_dep_ids_dict[id]
        else:
            id_arr = id.split("/")
            len_arr = len(id_arr)
            name = id_arr[len_arr - 1]
            self.index = self.index + 1
            counter = 5
            var_prefix_name = ""
            while (True):
                counter = counter + 2
                if counter < len_arr:
                    var_prefix_name = var_prefix_name + "_" + id_arr[counter]
                else:
                    break
            var_name = "variable_{0}{1}".format(self.index, var_prefix_name)
            var_name_repl = "${var." + var_name + "}"
            self.variable_list_dict[var_name] = id
            self.unique_dep_ids_dict[id] = var_name_repl
        return var_name_repl

    ############
    ################# FIX  virtual network and subnet mess ########
    def _fix_vnet_and_subnet(self, resource_type, resource):
         if "azurerm_virtual_network" != resource_type:
             return
         # move vnet name into variable
         # move instance.name into subnet
         if "subnet" in resource:
             refer_vnet_name= "{0}.{1}.name".format(resource_type, resource["name"])
             subnets = resource["subnet"]
             for subnet in subnets:
                subnet_id = subnet["id"]
                main_subnet= self._get_main_by_var_name_dict(subnet_id)
                main_subnet['virtual_network_name']="${"+refer_vnet_name+"}"
             self._del_key(resource, "subnet")

    ################# FIX  virtual network and subnet mess ########
    def _main_by_id_dict_by_type(self, tf_resource_type):
        resource_types = self.main_tf_dict["resource"]
        if tf_resource_type in resource_types:
            return resource_types[tf_resource_type]
        return []

    def _main_by_id_dict_by_type_and_var_name(self, tf_resource_type, tf_resource_var_id):
        resource_types = self.main_tf_dict["resource"]
        if tf_resource_type in resource_types:
            res_dict = resource_types[tf_resource_type]
            if tf_resource_var_id in res_dict:
                return res_dict[tf_resource_var_id]
        return []

    ################# FIX   virtual network and subnet mess : assuming the subnet is added only one vnet########

    def _set_states_by_id_dict(self, id, attributes):
        self.states_by_id_dict[id] = attributes
        self.states_by_id_dict[id.strip().lower()] = attributes

    def _get_states_by_id_dict(self, id):
        if id in self.states_by_id_dict:
            return self.states_by_id_dict[id]
        elif id.strip().lower() in self.states_by_id_dict:
            return self.states_by_id_dict[id.strip().lower()]
        return None

    ##
    def _set_states_tf_var_by_id_dict(self, id, type_and_var_name):
        self.states_tf_var_by_id_dict[id] = type_and_var_name
        self.states_tf_var_by_id_dict[id.strip().lower()] = type_and_var_name
        self._set_id_by_type_and_var_name_dict(id, type_and_var_name)

    def _get_states_tf_var_by_id_dict(self, id):
        if id in self.states_tf_var_by_id_dict:
            return self.states_tf_var_by_id_dict[id]
        elif id.strip().lower() in self.states_tf_var_by_id_dict:
            return self.states_tf_var_by_id_dict[id.strip().lower()]
        return None

    ### main
    def _set_id_by_type_and_var_name_dict(self, id, type_and_var_name):
        self.id_by_type_and_var_name_dict[type_and_var_name] = id
        self.id_by_type_and_var_name_dict[type_and_var_name.lower().strip()] = id

    def _get_id_by_type_and_var_name_dict(self, type_and_var_name):
        if type_and_var_name in self.id_by_type_and_var_name_dict:
            return self.id_by_type_and_var_name_dict[type_and_var_name]
        if type_and_var_name.lower().strip() in self.id_by_type_and_var_name_dict:
            return self.id_by_type_and_var_name_dict[type_and_var_name.lower().strip()]
        print("ERROR:", "_get_id_by_type_and_var_name_dict: NOT FOUND", type_and_var_name)
        return None
    #
    def _get_main_by_id_dict(self, id):
        resource = self._get_states_by_id_dict(id)
        if resource:
            tf_resource_type = resource["tf_resource_type"]
            tf_resource_var_name = resource["tf_resource_var_name"]
            return self._main_by_id_dict_by_type_and_var_name(tf_resource_type, tf_resource_var_name )
        return None
    def _get_main_by_var_name_dict(self, var_str):
        if "${"  not in var_str:
            self._get_main_by_id_dict(var_str)
        if "${var"  in var_str:
            var_name = var_str.replace("${", "").replace("}", "").strip()
            id = self.variable_list_dict[var_name]
            if id:
                return self._get_main_by_id_dict(id)
            print("ERROR:", "_get_main_by_var_name_dict: NOT FOUND", var_str)
            return None
        var_name = var_str.replace("${", "").replace("}", "").strip().lower()
        var_name_arr = var_name.split(".")
        var_name_new = "{0}.{1}".format(var_name_arr[0],var_name_arr[1])
        if var_name_new in self.id_by_type_and_var_name_dict:
            id = self._get_id_by_type_and_var_name_dict(var_name_new)
            return self._get_main_by_id_dict(id)
        print("ERROR:", "_get_main_by_var_name_dict: NOT FOUND", var_str)
        return None


    ###
    def _states_by_id_dict(self):
        resources = self.states_dict['resources']
        for resource in resources:
            try:
                attributes = resource['instances'][0]['attributes']
                id = attributes["id"]
                id = id.strip().lower()
                attributes["tf_resource_type"] = resource["type"]
                attributes["tf_resource_var_name"] = resource["name"]
                self._set_states_by_id_dict(id, attributes)
                var_tf = "{0}.{1}".format(attributes["tf_resource_type"], attributes["tf_resource_var_name"])
                self._set_states_tf_var_by_id_dict(id, var_tf)
            except Exception as e:
                self.file_utils._save_errors("ERROR:Step3:2: _states_by_id_dict {0}".format(e))
                print("ERROR:AzurermTfStep3NewStack:", "_states_by_id_dict", id, e)
        return self.states_by_id_dict

    def _gen_interpolation_ids_for_res(self):
        for resource in self.resources_dict:
            resource["tf_variable_id_new"] = resource["tf_variable_id"]
            resource["interpolation_id"] = "${" + resource["tf_resource_type"] + "." + resource[
                "tf_variable_id"] + ".id}"
            self.resources_by_id_dict[resource["tf_import_id"]] = resource

    ############



    ##### helper load and save files ##############

    def _load_files(self):
        # verify import worked
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()
        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception("Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")

        # paths
        self.main_tf_read_from_file = self.file_utils.tf_main_file_for_step("step2")
        self.resources_read_from_file = self.file_utils.tf_resources_file_for_step("step2")

        # load
        self.states_dict = self.file_utils.load_json_file(self.state_read_from_file)

        #
        self.resources_dict = self.file_utils.load_json_file(self.resources_read_from_file)
        self.main_tf_dict = self.file_utils.load_json_file(self.main_tf_read_from_file)

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
            self.file_utils._save_errors("ERROR:Step3:2: _copy_text_file {0}".format(e))
            print("ERROR:AzurermTfStep3NewStack:", "_copy_text_file", e)
