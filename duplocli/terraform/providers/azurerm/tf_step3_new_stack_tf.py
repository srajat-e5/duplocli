from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import random
import os
import json
from datetime import datetime


# simple json manipulation to extract variables and dependency id replacement
# create unique names for storage
# create dependency heirarchy -- a simple cheat to trraform framework by replacing actual id with referenced/dependent's id
# ie. simple json interpolation  referenced-id replacement in main tf
# also create resource, and simple json interpolation location and resource-id replacement in main tf
# {
#     "tf_resource_type": "azurerm_app_service",
#     "tf_variable_id": "duplotestfileshare",
#     "tf_import_id": "/subscriptions/29474c73-cd93-48f0-80ee-9577a54e2227/resourceGroups/duploservices-azdemo1/providers/Microsoft.Web/sites/duplotestfileshare",
#     "module": "azdemo1",
#     "tf_variable_id_new": "duplotestfileshare",
#     "interpolation_id": "${azurerm_app_service.duplotestfileshare.id}"
# },
# assign variable for resource_group_name, location, add to variables dict if does not exits already
# Find recurively all values with string /subscriptions/ extract them to variables as they are missing in import dependency list
# interpolation_id= "${azurerm_resource_group.tfduplosvs-aztf7.name}"
# TODO:  if id contains '$' or '}' ?
# if resource group use var
# else use resource group dep id
# first list all currently being imported resource_groups by {name:locartion}
class AzurermTfStep3NewStack(AzureBaseTfImportStep):

    #dict
    states_dict = {}
    resources_dict = {}

    #dict with ids
    resources_by_id_dict = {}
    states_by_id_dict = {}
    states_tf_var_by_id_dict = {}

    #main
    main_tf_text = ""
    main_tf_dict = {}

    #track variables to be created
    variable_list_dict = {}
    # variable index
    index = 0
    #existing res_groups
    res_groups={}

    #to avoid duplicates
    unique_resource_groups_dict={}
    unique_dep_ids_dict={}


    def __init__(self, params):
        super(AzurermTfStep3NewStack, self).__init__(params)
        random.seed(datetime.now())

    def execute(self):
        self._load_files()
        self._gen_interpolation_ids_for_res()
        self._states_by_id_dict()
        self._tf_resources()
        self._save_files("")
        return self.file_utils.tf_main_file()

    ######  TfImportStep3 ################################################
    def _tf_resources(self):
        try:
            self._parameterize()
            print("DONE")
        except Exception as e:
            print("ERROR:AzurermTfStep3NewStack:", "_tf_resources", e)
        # save resources and tf
        # todo: different folders for exisitng ,new non-duplo, new duplo tenant/infra
        # self._save_files()

    def _parameterize(self):
        self._res_group_vars()
        resource_types = self.main_tf_dict["resource"]
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                try:
                    resource  = resources[resource_key]

                    try:
                        self._parameterize_for_res_grp(resource_type, resource)
                    except Exception as e:
                        print("ERROR:AzurermTfStep3NewStack:1", "_parameterize", e)

                    try:
                        self._parameterize_res_for_dep_ids(resource_type, resource)
                    except Exception as e:
                        print("ERROR:AzurermTfStep3NewStack:2", "_parameterize", e)

                except Exception as e:
                    print("ERROR:AzurermTfStep3NewStack:3", "_parameterize", e)


    ###### resource_groups name and location parameterization #############
    def _interplation_for_res_grp(self, index, resource_group_name, location, exists_in_import):
        try:
            var_res_grp_name = "resource_group_{1}_name_{0}".format(resource_group_name, index)
            var_res_grp_loc = "resource_group_{1}_location_{0}".format(resource_group_name,index)
            self.variable_list_dict[var_res_grp_name] = resource_group_name
            self.variable_list_dict[var_res_grp_loc] = var_res_grp_loc
            #not needed if exists_in_import=False
            interpolation_res_grp_id = "azurerm_resource_group.{0}.id".format(resource_group_name)
            interpolation_res_grp_loc  = "azurerm_resource_group.{0}.location".format(resource_group_name)
            resource_group_vars = {
                "location": location,
                "resource_group_name": resource_group_name,
                "index":  index,
                "var_res_grp_name": var_res_grp_name,
                "var_res_grp_loc": var_res_grp_loc,
                "interpolation_res_grp_id": interpolation_res_grp_id,
                "interpolation_res_grp_loc": interpolation_res_grp_loc,
                "exists_in_import": exists_in_import
            }
            return resource_group_vars
        except Exception as e:
            print("ERROR:AzurermTfStep3NewStack:1", "_parameterize", e)


    def _res_group_vars(self):
        resource_types = self.main_tf_dict["resource"]
        self.res_groups={}
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                resource  = resources[resource_key]
                if resource_type == "azurerm_resource_group":
                    location = resource["location"]
                    resource_group_name = resource["name"]
                    if resource_group_name not in self.res_groups:
                        self.index = self.index + 1
                        resource_group_vars = self._interplation_for_res_grp(self.index, resource_group_name, location, True)
                        self.res_groups[resource_group_name] = resource_group_vars

        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                resource  = resources[resource_key]
                if resource_type != "azurerm_resource_group":
                    if "resource_group_name"  in resource and  "location"  in resource:
                        location = resource["location"]
                        resource_group_name = resource["resource_group_name"]
                        if resource_group_name not in self.res_groups:
                            self.index = self.index + 1
                            resource_group_vars = self._interplation_for_res_grp(self.index, resource_group_name, location, False)
                            self.res_groups[resource_group_name] = resource_group_vars


    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############
    def _parameterize_for_res_grp(self, resource_type, resource):
        if resource_type == "azurerm_resource_group":
            resource_group_name = resource[ "name"]
            resource_group_vars = self.res_groups[resource_group_name]
            resource["name"]= "${"+resource_group_vars["var_res_grp_name"] +"}"
            resource["location"] = "${" + resource_group_vars["var_res_grp_loc"] + "}"
        else:
            if "resource_group_name" in resource:
                resource_group_name = resource["resource_group_name"]
                resource_group_vars = self.res_groups[resource_group_name]
                resource["resource_group_name"]= "${"+resource_group_vars["interpolation_res_grp_id"] +"}"
                if "location" in resource:
                    resource["location"]= "${"+resource_group_vars["interpolation_res_grp_loc"] +"}"

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############



    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############


    def _parameterize_res_for_dep_ids(self, resource_type, resource):
        resource_obj_parent = resource
        for attribute_name, attribute in resource.items():
            try:
                if isinstance(attribute, dict):
                    self._parameterize_util_dict_for_dep_ids(resource_obj_parent, attribute_name, attribute)
                elif isinstance(attribute, list):
                    is_string=False
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._parameterize_util_dict_for_dep_ids(attribute, attribute_name, nested_item)
                        elif isinstance(nested_item, list):
                            print("isinstance(attribute, list):", "_process_dict", attribute_name)
                        else:
                            is_string = True
                    if is_string:
                        self._get_unique_tf_variable(attribute, attribute_name, nested_item,  True)
                else:
                    self._get_unique_tf_variable(resource_obj_parent, attribute_name, attribute, False)

            except Exception as e:
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
                print("ERROR:Step2:", "_process_dict", e)

    def _get_unique_tf_variable(self, attribute, nested_atr_name, value, is_list ):
        # array or string?
        if value is None:
            return value
        #its bug
        if nested_atr_name not in attribute:
            return value

        if isinstance(value, list):
            values = [] #array of ids?
            for value_item in value:
                if value_item is not None and "{0}".format(value_item).startswith("/subscriptions/"):
                    variable_id = self._get_variable_id_for_dep_id(value_item)
                    values.append(variable_id)
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
                    print(is_list, "@@@@NOT found ",nested_atr_name, value, attribute)
                #print( nested_atr_name, value)
        return value
    def _has_id(self, tf_import_id):
        try:
            return self.main_tf_text.self.index(tf_import_id+"\"")
        except Exception as e:
            pass
         #print("ERROR:AzurermTfStep3NewStack:", "_tf_resources", e)
        return -1

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############
    def _get_variable_id_for_dep_id(self, id):
        if id in self.states_tf_var_by_id_dict:
            var_name_repl = "${" + self.states_tf_var_by_id_dict[id] + ".id}"
        elif id in self.unique_dep_ids_dict:
            var_name_repl = self.unique_dep_ids_dict[id]
        else:
            id_arr = id.split("/")
            len_arr = len(id_arr)
            name = id_arr[len_arr - 1]
            self.index = self.index + 1
            var_name = "variable_{0}_{1}".format(self.index, name)
            var_name_repl = "${var." + var_name + "}"
            self.variable_list_dict[var_name] = id
            self.unique_dep_ids_dict[id] = var_name_repl
        return var_name_repl

    ############
    def _states_by_id_dict(self):
        if "resources" in self.states_dict:
            resources = self.states_dict['resources']
        else:
            resources = self.states_dict['resource']
        for resource in resources:
            try:
                attributes = resource['instances'][0]['attributes']
                attributes["tf_resource_type"] = resource["type"]
                attributes["tf_resource_var_name"] = resource["name"]
                self.states_by_id_dict[attributes["id"]] = attributes
                var_tf = "{0}.{1}".format(attributes["tf_resource_type"], attributes["tf_resource_var_name"])
                self.states_tf_var_by_id_dict[attributes["id"]] = var_tf
            except Exception as e:
                print("ERROR:AzurermTfStep3NewStack:", "_states_by_id_dict", e)
        return self.states_by_id_dict

    def _gen_interpolation_ids_for_res(self):
        for resource in self.resources_dict:
            resource["tf_variable_id_new"] = resource["tf_variable_id"]
            resource["interpolation_id"] = "${" + resource["tf_resource_type"] + "." + resource["tf_variable_id"] + ".id}"
            self.resources_by_id_dict[resource["tf_import_id"]] = resource
    ############


    ##### helper load and save files ##############

    def _load_files(self):
        #verify import worked
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()
        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception("Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")

        #paths
        self.main_tf_read_from_file = self.file_utils.tf_main_file_for_step("step2")
        self.resources_read_from_file = self.file_utils.tf_resources_file_for_step("step1")

        #load
        self.states_dict = self.file_utils.load_json_file(self.state_read_from_file)

        #
        self.resources_dict = self.file_utils.load_json_file(self.resources_read_from_file)
        # self.main_tf_text = self.file_utils.file_read_as_text(self.main_tf_read_from_file)
        self.main_tf_dict = self.file_utils.load_json_file(self.main_tf_read_from_file) #json.loads(self.main_tf_text)

    def _save_files(self, folder):
        self.file_utils.save_to_json( self.file_utils.tf_resources_file(), self.resources_dict )
        self.file_utils.save_to_json(self.file_utils.tf_state_file(), self.states_dict)
        self.file_utils.save_to_json(self.file_utils.tf_main_file(), self.main_tf_dict)
        self.file_utils.save_json_to_work_folder("terraform.tfvars.json", self.variable_list_dict)
