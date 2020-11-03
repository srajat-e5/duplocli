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
        index=0
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
                        index = index + 1
                        variable_name = "resource_group_name_{0}_{1}".format(resource_group_name, index)  # "resource_group_{0}_{1}".format( resource_group_name ,random.randint(1,99))
                        if variable_name not in self.variable_list:
                            unique_resource_group_name =    "resource_group_{1}_name_{0}".format(resource_group_name, index)
                            unique_resource_group_location = "resource_group_{1}_location_{0}".format(resource_group_name, index)
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
        resource_types = self.main_tf_dict["resource"]
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                resource = resources[resource_key]
                resource_group_name = resource["resource_group_name"]
                resource_group = self.unique_resource_groups_dict[resource_group_name]
                resource["resource_group_name"] = "${var." + resource_group["var_resource_group_name"] +"}"
                if resource["location"]  is not None:
                    resource["location"] = "${var." + resource_group["var_resource_group_location"] +"}"

    ###### resource_groups name and location parameterization #############

    ############## /subscriptions/ extract them to variables as they are missing in import dependency list #############
    # def _create_unique_tf_variable(self,):
    #     resource_types = self.main_tf_dict["resource"]
    #     for resource_type in resource_types:
    #         resources = resource_types[resource_type]
    #         for resource_key in resources:
    #             resource  = resources[resource_key]
    #             print(resource_key)

    def _create_vars(self):
        resource_types = self.main_tf_dict["resource"]
        for resource_type in resource_types:
            resources = resource_types[resource_type]
            for resource_key in resources:
                resource  = resources[resource_key]
                print(resource_key)

    def _create_var_for_dep_ids(self, resource):
        # assign variable for resource_group_name, location, add to variables dict if does not exits already
        # Find recurively all values with string /subscriptions/ extract them to variables as they are missing in import dependency list
        for attribute_name, attribute in resource.items():
            try:
                if isinstance(attribute, dict):
                    self._process_dict(resource, attribute_name, attribute)
                elif isinstance(attribute, list):
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._process_dict(resource, attribute_name, nested_item)
                        else:
                            # self.set_value_cout(nested_count, is_computed, parent_set, tf_resource_type,
                            #                     tf_resource_var_name, nested_item, attribute_name)
                            # resource_obj_dict.append(nested_item)
                            pass
            except Exception as e:
                print("ERROR:Step2:", "_create_var", e)

    def _process_dict(self, resource, nested_atr_name, nested_atr):
        for attribute_name, attribute in nested_atr.items():
            try:
                if isinstance(attribute, list):
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._process_dict(resource, nested_atr_name, nested_item)
                        elif isinstance(nested_item, list):
                            print("WARN:", self.file_utils.stage_prefix(),
                                  " _process_nested  is list list nested list ???? ", nested_atr_name)
                        else:
                            pass
                else:
                    pass
            except Exception as e:
                print("ERROR:Step2:", "_process_dict", e)


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
        index = self._has_id(tf_import_id)

        if index >0:
            print("DEP_FOUND:_replace_id_with_reference", index, tf_import_id)
            text = text.replace("\"" +tf_import_id + "\"", "\""+interpolation_id+"\"" )
            text = text.replace( tf_import_id , interpolation_id )
            self.main_tf_text = text
            index = self._has_id(tf_import_id)
            print("AFTE DEP_FOUND:_replace_id_with_reference", index, tf_import_id)
        else:
            pass #print("DEP_NOT_FOUND:_replace_id_with_reference",   tf_import_id)

    def _has_id(self, tf_import_id):
        try:
            return self.main_tf_text.index(tf_import_id)
        except Exception as e:
            pass
         #print("ERROR:AzurermTfStep3NewStack:", "_tf_resources", e)
        return -1


