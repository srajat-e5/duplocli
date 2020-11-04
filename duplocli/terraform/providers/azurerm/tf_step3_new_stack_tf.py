from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import random
import os
import json
from datetime import datetime


class AzurermTfStep3NewStack(AzureBaseTfImportStep):
    is_allow_none = True

    states_dict = {}
    resources_dict = {}

    main_tf_text = ""
    main_tf_dict = {}

    resources_by_id_dict = {}
    states_by_id_dict = {}
    variable_list = {}

    variables_dict = {}
    unique_resource_groups_dict={}
    unique_dep_ids_dict={}

    #variable index
    index = 0
    def __init__(self, params):
        super(AzurermTfStep3NewStack, self).__init__(params)
        random.seed(datetime.now())


    def execute(self):
        # simple json manipulation to extract variables and dependency id replacement
        self._load_files()
        self._tf_resources()
        self._save_files("")
        return self.file_utils.tf_main_file()

    ######  TfImportStep3 ################################################

    def _tf_resources(self):
        try:
            self._resources_by_id_dict()
            self._states_by_id_dict()
            self._unique_resource_groups_dict()

            # create unique names for storage
            # create dependency heirarchy -- a simple cheat to trraform framework by replacing actual id with referenced/dependent's id
            # ie. simple json interpolation  referenced-id replacement in main tf
            # also create resource, and simple json interpolation location and resource-id replacement in main tf

            keys = self.resources_by_id_dict.keys()
            for resources_id in keys:
                try:
                    self._update_resource_for_id(resources_id)
                except Exception as e:
                    print("ERROR:AzurermTfStep3NewStack:res", "_tf_resources", resources_id, e)

            for resources_id in self.resources_by_id_dict:
                try:
                    resource = self.resources_by_id_dict[resources_id]
                    self._replace_id_with_reference(resource)
                except Exception as e:
                    print("ERROR:AzurermTfStep3NewStack:text", "_tf_resources", resources_id, e)

            ### extract resource group into vars
            self.main_tf_dict = json.loads(self.main_tf_text)
            self._replace_resource_group_with_variable()
            ### extract missing infra or object ids into vars
            self._create_vars()

            print("DONE")
        except Exception as e:
            print("ERROR:AzurermTfStep3NewStack:", "_tf_resources", e)
        # save resources and tf
        # todo: different folders for exisitng ,new non-duplo, new duplo tenant/infra
        # self._save_files()

    ##### helper load and save files ##############
    def _load_files(self):
        self.main_tf_read_from_file = self.file_utils.tf_main_file_for_step("step2")
        self.resources_read_from_file = self.file_utils.tf_resources_file_for_step("step1")
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()

        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception("Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")
        self.states_dict = self.file_utils.load_json_file(self.state_read_from_file)
        # self.main_tf_dict = self.file_utils.load_json_file(self.main_tf_read_from_file)
        self.resources_dict = self.file_utils.load_json_file(self.resources_read_from_file)
        self.main_tf_text = self.file_utils.file_read_as_text(self.main_tf_read_from_file)

    def _save_files(self, folder):
        self.file_utils.save_to_json( self.file_utils.tf_resources_file(), self.resources_dict )
        self.file_utils.save_to_json(self.file_utils.tf_state_file(), self.states_dict)
        self.file_utils.save_to_json(self.file_utils.tf_main_file(), self.main_tf_dict)
        # self.file_utils.file_save_as_text(self.file_utils.tf_main_file(), self.main_tf_text)
        self.file_utils.save_json_to_work_folder("terraform.tfvars.json", self.variable_list)

    ##### helper for parameterization resources and state dict ##############
    def _resources_by_id_dict(self):
        # self.resources_by_id_dict = {}
        for duplo_resource in self.resources_dict:
            self.resources_by_id_dict[duplo_resource["tf_import_id"]] = duplo_resource
        return self.resources_by_id_dict

    def _states_by_id_dict(self):
        # self.states_by_id_dict = {}
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
            except Exception as e:
                print("ERROR:AzurermTfStep3NewStack:", "_states_by_id_dict", e)

        return self.states_by_id_dict

    ###### resource_groups name and location parameterization #############
    # def _unique_resource_groups_variable_name(self, resource_type, field_name, value):
    #     while(True):
    #         variable_name = "{0}_{1}_{2}".format( resource_type, field_name ,random.randint(1,99)) #"resource_group_{0}_{1}".format( resource_group_name ,random.randint(1,99))
    #         if variable_name not in self.unique_variable_name_list:
    #             self.unique_variable_name_list[variable_name] = value
    #             return variable_name

    def _unique_resource_groups_dict(self):
        # self.unique_resource_groups_dict={}
        for resource_key in self.states_by_id_dict:
            try:
                resource = self.states_by_id_dict[resource_key]
                if "resource_group_name" not in resource:
                    continue
                location = None
                if "location"   in resource:
                    location = resource["location"]
                resource_group_name = resource["resource_group_name"]
                if resource_group_name not in self.unique_resource_groups_dict:
                    while (True):
                        self.index = self.index + 1
                        variable_name = "resource_group_name_{0}_{1}".format(resource_group_name, self.index)  # "resource_group_{0}_{1}".format( resource_group_name ,random.randint(1,99))
                        if variable_name not in self.variable_list:
                            unique_resource_group_name =    "resource_group_{1}_name_{0}".format(resource_group_name, self.index)
                            unique_resource_group_location = "resource_group_{1}_location_{0}".format(resource_group_name, self.index)
                            resouce_vars={"location":location, "resource_group_name":resource_group_name,
                                           "var_resource_group_name":unique_resource_group_name,
                                          "var_resource_group_location": unique_resource_group_location
                                         }
                            self.unique_resource_groups_dict[resource_group_name] = resouce_vars
                            self.variable_list[unique_resource_group_name] = resource_group_name
                            self.variable_list[unique_resource_group_location] = location

                            break
            except Exception as e:
                print("ERROR:AzurermTfStep3NewStack:", "_unique_resource_groups_dict", e)
        return self.unique_resource_groups_dict

    def _replace_resource_group_with_variable(self):
        #TODO: re-define after including resouece in main.tf file
        resource_types = self.main_tf_dict["resource"]
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                resource = resources[resource_key]
                if resource["resource_group_name"] is not None:
                    return  #TODO:
                resource_group_name = resource["resource_group_name"]
                resource_group = self.unique_resource_groups_dict[resource_group_name]
                resource["resource_group_name"] = "${var." + resource_group["var_resource_group_name"] +"}"
                if resource["location"]  is not None:
                    resource["location"] = "${var." + resource_group["var_resource_group_location"] +"}"

    ###### resource_groups name and location parameterization #############

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############


    def _create_vars(self):
        resource_types = self.main_tf_dict["resource"]
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                resource  = resources[resource_key]
                self._process_resource_for_dep_ids(resource)

    def _process_resource_for_dep_ids(self, resource):
        # assign variable for resource_group_name, location, add to variables dict if does not exits already
        # Find recurively all values with string /subscriptions/ extract them to variables as they are missing in import dependency list
        resource_obj_parent = resource
        for attribute_name, attribute in resource.items():
            try:
                if isinstance(attribute, dict):
                    self._process_resource_dict_for_dep_ids(resource_obj_parent, attribute_name, attribute)
                elif isinstance(attribute, list):
                    is_string=False
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._process_resource_dict_for_dep_ids(attribute, attribute_name, nested_item)
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

    def _process_resource_dict_for_dep_ids(self, resource_obj_parent, nested_atr_name, nested_atr):
        for attribute_name, attribute in nested_atr.items():
            try:
                if isinstance(attribute, list):
                    is_string = False
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._process_resource_dict_for_dep_ids(attribute, nested_atr_name, nested_item)
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
        if is_list and isinstance(value, list) and nested_atr_name in attribute:
            values = []
            for value_item in value:
                if value_item is not None and "{0}".format(value_item).startswith("/subscriptions/"):
                    # print(is_list, "@@@@found ", nested_atr_name, value)
                    variable_id = self._get_variable_id_for_dep_id(value_item)
                    values.append(variable_id)
            attribute[nested_atr_name] = values
            return values
        else:
            if value is not None and "{0}".format(value).startswith("/subscriptions/"):
                if nested_atr_name in attribute:
                    # print(is_list, "@@@@found ",nested_atr_name, value )
                    variable_id = self._get_variable_id_for_dep_id(value)
                    attribute[nested_atr_name] = variable_id
                    return variable_id
                else:
                    print(is_list, "@@@@NOT found ",nested_atr_name, value, attribute)
                #print( nested_atr_name, value)
                pass
        return value

    def _get_variable_id_for_dep_id(self, id):
        if id in self.unique_dep_ids_dict:
            var_name_repl = self.unique_dep_ids_dict[id]
        else:
            id_arr = id.split("/")
            len_arr= len(id_arr)
            name = id_arr[len_arr-1]
            self.index = self.index + 1
            var_name = "variable_{0}_{1}".format(self.index, name)
            var_name_repl = "${var." + var_name + "}"
            self.variable_list[var_name] = id
            self.unique_dep_ids_dict[id] = var_name_repl
        return var_name_repl
    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############

    ############

    def _update_resource_for_id(self,resources_id):
        # {
        #     "tf_resource_type": "azurerm_app_service",
        #     "tf_variable_id": "duplotestfileshare",
        #     "tf_import_id": "/subscriptions/29474c73-cd93-48f0-80ee-9577a54e2227/resourceGroups/duploservices-azdemo1/providers/Microsoft.Web/sites/duplotestfileshare",
        #     "module": "azdemo1",
        #     "tf_variable_id_new": "duplotestfileshare",
        #     "interpolation_id": "${azurerm_app_service.duplotestfileshare.id}"
        # },
        resource = self.resources_by_id_dict[resources_id]
        tf_resource_type = resource["tf_resource_type"]
        tf_variable_id = resource["tf_variable_id"]
        tf_import_id = resource["tf_import_id"]

        # must be unique for new terraform for global's like s3 or azure storage?
        if "tf_variable_id_new" not in resource:
            resource["tf_variable_id_new"] = tf_variable_id
        else:
            resource["tf_variable_id_new"] = tf_variable_id # "tf_variable_id_new"
        #TODO: for new we have to change id for existing keep old id?
        tf_variable_id_new = resource["tf_variable_id_new"]
        #interpolation_id= "${azurerm_resource_group.tfduplosvs-aztf7.name}"
        #TODO:  if id contains '$' or '}' ?
        interpolation_id = "${"+tf_resource_type+"."+tf_variable_id_new+".id}"
        resource["interpolation_id"] = interpolation_id
        # self.resources_by_id_dict[tf_import_id]=resource
        return resource

    def _replace_id_with_reference(self, resource):
        tf_import_id = resource["tf_import_id"]
        interpolation_id = resource["interpolation_id"]
        text = self.main_tf_text
        self.index = self._has_id(tf_import_id)

        if self.index >0:
            print("DEP_FOUND:_replace_id_with_reference", self.index, tf_import_id)
            text = text.replace("\"" +tf_import_id + "\"", "\""+interpolation_id+"\"" )
            #text = text.replace( tf_import_id , interpolation_id )
            self.main_tf_text = text
            self.index = self._has_id(tf_import_id)
            print("AFTE DEP_FOUND:_replace_id_with_reference", self.index, tf_import_id)
        else:
            pass #print("DEP_NOT_FOUND:_replace_id_with_reference",   tf_import_id)

    def _has_id(self, tf_import_id):
        try:
            return self.main_tf_text.self.index(tf_import_id+"\"")
        except Exception as e:
            pass
         #print("ERROR:AzurermTfStep3NewStack:", "_tf_resources", e)
        return -1


