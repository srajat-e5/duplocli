from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import random
import os
from datetime import datetime


class AzurermTfStep3NewStack(AzureBaseTfImportStep):
    is_allow_none = True
    states_dict = {}

    def __init__(self, params):
        super(AzurermTfStep3NewStack, self).__init__(params)
        random.seed(datetime.now())

    def _load_files(self):
        self.main_tf_read_from_file = self.file_utils.tf_main_file_for_step("step2")
        self.resources_read_from_file = self.file_utils.tf_resources_file_for_step("step1")
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()

        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception("Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")
        self.states_dict = self.file_utils.load_json_file(self.state_read_from_file)
        self.main_tf_dict = self.file_utils.load_json_file(self.main_tf_read_from_file)
        self.resources_dict = self.file_utils.load_json_file(self.resources_read_from_file)
        self.main_tf_text = self.file_utils.file_read_as_text(self.main_tf_read_from_file)

    def _save_files(self, folder):
        self.file_utils.save_to_json( self.file_utils.tf_resources_file(), self.resources_dict )
        self.file_utils.save_to_json(self.file_utils.tf_state_file(), self.states_dict)
        self.file_utils.file_save_as_text(self.file_utils.tf_main_file(), self.main_tf_text)

    def execute(self):
        # copy step2 main file
        # copy resources file
        # add new fields- new name, replace id with json interpolation
        #
        self._load_files()
        self._tf_resources()
        self._save_files("")
        return self.file_utils.tf_main_file()

    ##### manage files and state ##############
    def _resources_by_id_dict(self):
        self.resources_by_id_dict = {}
        for duplo_resource in self.resources_dict:
            self.resources_by_id_dict[duplo_resource["tf_import_id"]] = duplo_resource
        return self.resources_by_id_dict
    def _states_by_id_dict(self):
        self.states_by_id_dict = {}
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

    def _update_resource_for_id(self,resources_id):
        # {
        #     "tf_resource_type": "azurerm_managed_disk",
        #     "tf_variable_id": "duploservices-azdemo1-host1-dohpx",
        #     "tf_import_id": "/subscriptions/29474c73-cd93-48f0-80ee-9577a54e2227/resourceGroups/DUPLOSERVICES-AZDEMO1/providers/Microsoft.Compute/disks/duploservices-azdemo1-host1-dohpx",
        #     "module": "azdemo1"
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
        interpolation_id = "${"+tf_resource_type+"."+tf_variable_id_new+"}"


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
        ######  TfImportStep3 ################################################
    def _tf_resources(self):
        try:
            self._resources_by_id_dict()
            self._states_by_id_dict()

            # create unique names for storage
            # create dependency heirarchy -- a simple cheat to trraform framework by replacing actual id with referenced/dependent's id
            # ie. simple json interpolation  referenced-id replacement in main tf
            # also create resource, and simple json interpolation location and resource-id replacement in main tf

            keys =  self.resources_by_id_dict.keys()
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
                    print("ERROR:AzurermTfStep3NewStack:text", "_tf_resources",resources_id, e)
            print("DONE")
        except Exception as e:
            print("ERROR:AzurermTfStep3NewStack:", "_tf_resources", e)
        #save resources and tf
        #todo: different folders for exisitng ,new non-duplo, new duplo tenant/infra
        # self._save_files()

