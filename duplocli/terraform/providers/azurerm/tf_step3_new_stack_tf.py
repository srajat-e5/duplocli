from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import random
from datetime import datetime

class AzurermTfStep3NewStack(AzureBaseTfImportStep):

    is_allow_none = True
    states_dict = {}

    def __init__(self, params):
        super(AzurermTfStep3NewStack, self).__init__(params)
        random.seed(datetime.now())

    def _load_files(self):
        self.main_tf_read_from_file = self.file_utils.tf_resources_file_for_step("step2")
        self.resources_read_from_file = self.file_utils.tf_resources_file_for_step("step1")
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()

        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception("Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")
        self.states_dict = self.file_utils.load_json_file(self.state_read_from_file)
        self.main_tf_dict = self.file_utils.load_json_file(self.main_tf_read_from_file)
        self.resources_dict = self.file_utils.load_json_file(self.resources_read_from_file)
        self.main_tf_text = self.file_utils.file_read_as_text(self.main_tf_read_from_file)

    def execute(self):
        #copy step2 main file
        #copy resources file
        #add new fields- new name, replace id with json interpolation
        #
        self._tf_resources()
        return self.file_utils.tf_main_file()

    ##### manage files and state ##############
    def _resources_by_id_dict(self):
        self.resources_by_id_dict = {}
        for duplo_resource in self.resources_dict:
            self.resources_by_id_dict[duplo_resource["tf_import_id"]] = duplo_resource

    def _states_by_id_dict(self):
        self.states_by_id_dict = {}
        if "resources" in  self.states_dict:
            resources = self.states_dict['resources']
        else:
            resources = self.states_dict['resource']
        for resource in resources:
            try:
                attributes = resource['instances'][0]['attributes']
                attributes["tf_resource_type"]= resource["type"]
                attributes["tf_resource_var_name"] = resource["name"]
                self.states_by_id_dict[attributes["id"]] = attributes
            except Exception as e:
                print("ERROR:Step2:","_tf_resources", e)

        return self.states_by_id_dict
    ######  TfImportStep3 ################################################
    def _tf_resources(self):
        self.resources_by_id_dict = self._resources_by_id_dict()
        self.states_by_id_dict = self._states_by_id_dict()
        # create unique names for storage
        # create dependency heirarchy -- a simple cheat to trraform framework by replacing actual id with referenced/dependent's id
        # ie. simple json interpolation  referenced-id replacement in main tf
        #also create resource, and simple json interpolation location and resource-id replacement in main tf

