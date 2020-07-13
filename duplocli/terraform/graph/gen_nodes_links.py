import json
import datetime
from collections import defaultdict
import os
import psutil
import shutil

from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.tf_import_parameters import AwsImportParameters


class GenNodesLinks:
    tf_resources_all = {}
    tf_resources_to_id_all = {}

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

        tf_resources_links = {}
        self.find_links(tf_resources, tf_resources_to_id, tf_resources_links)
        ##
        graph_folder = os.path.dirname(tf_state_file)
        ##
        tf_resources_file = os.path.join(graph_folder, "tf_resources_file.json")
        tf_resources_to_id_file = os.path.join(graph_folder, "tf_resources_to_id.json")
        tf_resources_links_file = os.path.join(graph_folder, "tf_resources_links.json")
        ##
        self.file_utils.save_to_json(tf_resources_file, tf_resources)
        self.file_utils.save_to_json(tf_resources_to_id_file, tf_resources_to_id)
        self.file_utils.save_to_json(tf_resources_links_file, tf_resources_links)

        print("")

    def find_links(self, tf_resources, tf_resources_to_id, tf_resources_links):
        tf_resource_ids = list(tf_resources.keys())
        for tf_resource_id in tf_resource_ids:
            self.find_link(tf_resource_id, tf_resources, tf_resources_to_id, tf_resources_links)

    def find_link(self, tf_resource_id_src, tf_resources, tf_resources_to_id, tf_resources_links):
        tf_resource_ids = list(tf_resources.keys())
        for tf_resource_id in tf_resource_ids:
            if tf_resource_id_src != tf_resource_id:
                tf_resources_dest = tf_resources[tf_resource_id]
                str_dest = json.dumps(tf_resources_dest)
                if "\"{0}\"".format(tf_resource_id_src)  in str_dest:
                    if tf_resource_id_src not in tf_resources_links:
                        tf_resources_links[tf_resource_id_src] = []
                    tf_resources_links[tf_resource_id_src].append(tf_resource_id)



if __name__ == '__main__':
    params = AwsImportParameters()
    params.step_type = "graph"
    params.module = "graph"
    graph_utils = GenNodesLinks(params)
    graph_utils.process_tfstate("/Users/brighu/_duplo_code/duplocli/work/graph/infra/terraform.tfstate")
    print("")


