import json
import datetime
from collections import defaultdict
import os
import psutil
import shutil

from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.tf_import_parameters import AwsImportParameters


class GenNodesLinks:
    tf_resources_merged = {}
    tf_resources_to_id_merged = {}
    tf_resources_links_merged = {}
    tf_graph_merged = {}

    def __init__(self, params):
        self.params = params
        self.file_utils = TfFileUtils(params, step=self.params.step, step_type=self.params.step_type)

    def merge_dict(self, dict1, dict2):
        res = {**dict1, **dict2}
        return res



    def process_dir(self, graph_root_folder):
        self.graph_root_folder = graph_root_folder
        graph_folders = set(os.listdir(graph_root_folder))
        for graph_folder_name in graph_folders:
            graph_folder =  os.path.join(graph_root_folder, graph_folder_name)
            if os.path.isdir(graph_folder):
                tf_state_file =  os.path.join(graph_folder, "terraform.tfstate")
                self.process_tfstate(tf_state_file)


        ##
        tf_resources_file = os.path.join(graph_root_folder, "tf_resources_file.json")
        tf_resources_to_id_file = os.path.join(graph_root_folder, "tf_resources_to_id.json")
        tf_resources_links_file = os.path.join(graph_root_folder, "tf_resources_links.json")
        tf_graph_file = os.path.join(graph_root_folder, "duplo_graph.json")
        ##
        self.file_utils.save_to_json(tf_resources_file, self.tf_resources_merged)
        self.file_utils.save_to_json(tf_resources_to_id_file, self.tf_resources_to_id_merged)
        self.file_utils.save_to_json(tf_resources_links_file, self.tf_resources_links_merged)
        self.file_utils.save_to_json(tf_graph_file, self.tf_graph_merged)

    def process_tfstate(self, tf_state_file):
        state_dict = self.file_utils.load_json_file(tf_state_file)
        resources = state_dict['resources']

        tf_resources={}
        tf_resources_var_to_ids = {}
        tf_resources_links = {}
        tf_graph = {}

        for resource in resources:
            tf_resource = {}
            tf_resource['type']=resource['type']
            tf_resource['name'] = resource['name']
            tf_resource['provider'] = resource['provider']
            #
            attributes = resource['instances'][0]['attributes']
            tf_resource['attributes'] = attributes
            #
            var_name = "{0}.{1}".format(resource['type'], resource['name'])
            id = attributes['id']
            tf_resource['id'] = id
            tf_resource['var_name'] = var_name
            tf_resource['svd_id'] = var_name
            #
            tf_resources[var_name] = tf_resource
            if id not in tf_resources_var_to_ids:
                tf_resources_var_to_ids[id] = []
            tf_resources_var_to_ids[id].append(var_name)
            print("resource",var_name, id, tf_resources_var_to_ids[id])

        # links
        self.find_links(tf_resources, tf_resources_var_to_ids, tf_resources_links, tf_graph)
        ##
        graph_folder = os.path.dirname(tf_state_file)
        tf_resources_file = os.path.join(graph_folder, "tf_resources_file.json")
        tf_resources_to_id_file = os.path.join(graph_folder, "tf_resources_to_id.json")
        tf_resources_links_file = os.path.join(graph_folder, "tf_resources_links.json")
        tf_graph_file = os.path.join(graph_folder, "duplo_graph.json")

        ##
        self.file_utils.save_to_json(tf_resources_file, tf_resources)
        self.file_utils.save_to_json(tf_resources_to_id_file, tf_resources_var_to_ids)
        self.file_utils.save_to_json(tf_resources_links_file, tf_resources_links)
        self.file_utils.save_to_json(tf_graph_file, tf_graph)

        # merge to global
        self.tf_resources_merged = self.merge_dict( self.tf_resources_merged, tf_resources)
        self.tf_resources_to_id_merged = self.merge_dict(self.tf_resources_to_id_merged, tf_resources_var_to_ids)
        self.tf_resources_links_merged = self.merge_dict(self.tf_resources_links_merged, tf_resources_links)
        self.tf_graph_merged = self.merge_dict(self.tf_graph_merged, tf_graph)


        print("")


    def find_links(self, tf_resources, tf_resources_var_to_ids, tf_resources_links, tf_graph):
        tf_resource_var_names = list(tf_resources.keys())
        for tf_resource_var_name in tf_resource_var_names:
            self.find_link(tf_resource_var_name, tf_resources, tf_resources_var_to_ids, tf_resources_links, tf_graph)
        self.create_nodes_and_links(tf_resources, tf_resources_var_to_ids, tf_resources_links, tf_graph)

    def find_link(self, tf_resource_var_name_src, tf_resources, tf_resources_var_to_ids, tf_resources_links, tf_graph):
        tf_resource_var_names = list(tf_resources.keys())
        for tf_resource_var_name in tf_resource_var_names:
            if tf_resource_var_name_src == tf_resource_var_name:
                continue #skip this one

            #skip if id is duplicate object?
            tf_resource_src = tf_resources[tf_resource_var_name_src]
            tf_resource_var_names_src = tf_resources_var_to_ids[tf_resource_src['id']]
            if tf_resource_var_name in tf_resource_var_names_src:
                continue  # skip this one
            # check if id in this ojbect
            tf_resource_dest = tf_resources[tf_resource_var_name]
            dest_str = json.dumps(tf_resource_dest)
            src_id = tf_resource_src['id']
            if "\"{0}\"".format(src_id)  in dest_str:
                if tf_resource_var_name_src not in tf_resources_links:
                    tf_resources_links[tf_resource_var_name_src] = []
                tf_resources_links[tf_resource_var_name_src].append(tf_resource_var_name)

    def create_nodes_and_links(self, tf_resources, tf_resources_var_to_ids, tf_resources_links, tf_graph):
        nodes =  list(tf_resources.values())
        src_svd_ids = list(tf_resources_links.keys())
        conuter_svd_id = 1
        links = []
        for src_svd_id in src_svd_ids:
            # need some config as it could nd parent or child
            dest_svd_ids = tf_resources_links[src_svd_id]
            for dest_svd_id in dest_svd_ids:
                #{"source": "Napoleon", "target": "Myriel", "value": 1},
                id = "svd_link_id_{0}".format(conuter_svd_id)
                conuter_svd_id = conuter_svd_id + 1
                link = {"source": src_svd_id, "target": dest_svd_id, "svd_link_id": id}
                links.append(link)
        tf_graph["nodes"] = nodes
        tf_graph["links"] = links



if __name__ == '__main__':
    params = AwsImportParameters()
    params.step_type = "graph"
    params.module = "graph"
    graph_utils = GenNodesLinks(params)
    graph_utils.process_dir("/Users/brighu/_duplo_code/duplocli/work/graph")
    # graph_utils.process_tfstate("/Users/brighu/_duplo_code/duplocli/work/graph/infra/terraform.tfstate")


    print("")


