import json
import datetime
from collections import defaultdict
import os
import psutil
import shutil

from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.tf_import_parameters import AwsImportParameters


class GenNodesLinks:

    def __init__(self, params):
        self.params = params
        self.file_utils = TfFileUtils(params, step=self.params.step, step_type=self.params.step_type)

    def process_dir(self, folder):
        pass

    def process_tfstate(self, tf_state_file):
        state_dict = self.file_utils.load_json_file(tf_state_file)
        resources = state_dict['resources']
        tf_resources={}
        tf_resources_to_id = {}
        for resource in resources:
            tf_resource = {}
            tf_resource['type']=resource['type']
            tf_resource['name'] = resource['name']
            tf_resource['provider'] = resource['provider']
            tf_resource['var_name'] = "{0}.{1}".format(resource['type'], resource['name'])
            attributes = resource['instances'][0]['attributes']
            tf_resource['attributes'] = attributes
            tf_resource['id'] = attributes['id']
            tf_resources[tf_resource['id']] = tf_resource
            tf_resources_to_id[tf_resource['var_name']] = tf_resource['id']
            print("resource",tf_resource['var_name'], tf_resource['id'] )

        ##
        graph_folder = os.path.dirname(tf_state_file)
        ##
        tf_resources_file = os.path.join(graph_folder, "tf_resources_file.json")
        tf_resources_to_id_file = os.path.join(graph_folder, "tf_resources_to_id.json")
        ##
        self.file_utils.save_to_json(tf_resources_file, tf_resources)
        self.file_utils.save_to_json(tf_resources_to_id_file, tf_resources_to_id)
        # tf_resources = {}
        # tf_resources_to_id = {}

        print("")

    def find_links(self, ):

if __name__ == '__main__':
    params = AwsImportParameters()
    params.step_type = "graph"
    params.module = "graph"
    graph_utils = GenNodesLinks(params)
    graph_utils.process_tfstate("/Users/brighu/_duplo_code/duplocli/work/graph/infra/terraform.tfstate")
    print("")


