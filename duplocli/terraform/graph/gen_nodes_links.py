import json
import datetime
from collections import defaultdict
import os
import psutil
import shutil

from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.tf_import_parameters import AwsImportParameters

class GraphData:
    tf_resources = {}
    tf_resources_var_to_ids = {}
    tf_resources_links = {}
    tf_resources_parent_links = {}
    tf_tree_ids = {}
    tf_tree = {}
    tf_graph = {}
    tf_tree_children = []
    def __init__(self, module):
        self.module = module
        self.tf_tree_children = []
        self.tf_tree = {
            "name":module,
            "data":{},
            "children": self.tf_tree_children
        }




class GenNodesLinks:
    graphData_all = GraphData("duplo")
    tf_modules = {}
    tf_module_counter = 1

    def __init__(self, params):
        self.params = params
        self.file_utils = TfFileUtils(params, step=self.params.step, step_type=self.params.step_type)

    def merge_dict(self, dict1, dict2):
        res = {**dict1, **dict2}
        return res

    def create_icons(self, main_file):
        #select random images and name them to aws_resouce.png
        state_dict = self.file_utils.load_json_file(main_file)
        resources = state_dict['resource']
        resources_names = list(resources.keys())
        src = '/Users/brighu/__pg/d3pg/duplo/icons'
        dest = '/Users/brighu/__pg/d3pg/duplo/icons2'
        src_icons = set(os.listdir(src))
        for resources_name in resources_names:
            dest_icon = os.path.join(dest, resources_name+".png")
            src_icon =  os.path.join(src, src_icons.pop())
            os.rename(src_icon, dest_icon)

    def process_dir(self, graph_root_folder):
        self.graph_root_folder = graph_root_folder
        graph_folders = set(os.listdir(graph_root_folder))
        for graph_folder_name in graph_folders:
            graph_folder =  os.path.join(graph_root_folder, graph_folder_name)
            if os.path.isdir(graph_folder):
                tf_state_file =  os.path.join(graph_folder, "terraform.tfstate")
                self.process_tfstate(tf_state_file, graph_folder_name)

        #generate  one more time for cumulative 
        self.create_nodes_and_links( self.graphData_all)
        self.create_parent_child(self.graphData_all)

        ##
        self.save_graph_data(graph_root_folder, self.graphData_all)



    def save_graph_data(self, graph_folder, graphData):
        ##
        tf_resources_file = os.path.join(graph_folder, "tf_resources_file.json")
        tf_resources_to_id_file = os.path.join(graph_folder, "tf_resources_to_id.json")
        tf_resources_links_file = os.path.join(graph_folder, "tf_resources_links.json")
        tf_resources_parent_links_file = os.path.join(graph_folder, "tf_resources_parent_links_file.json")
        tf_tree_file = os.path.join(graph_folder, "duplo_tree.json")
        tf_graph_file = os.path.join(graph_folder, "duplo_graph.json")
        tf_tree_ids_file = os.path.join(graph_folder, "tf_tree_ids_file.json")
        ##
        self.file_utils.save_to_json(tf_resources_file, graphData.tf_resources)
        self.file_utils.save_to_json(tf_resources_to_id_file, graphData.tf_resources_var_to_ids)
        self.file_utils.save_to_json(tf_resources_links_file, graphData.tf_resources_links)
        self.file_utils.save_to_json(tf_resources_parent_links_file, graphData.tf_resources_parent_links)
        self.file_utils.save_to_json(tf_tree_file, graphData.tf_tree)
        self.file_utils.save_to_json(tf_tree_ids_file, graphData.tf_tree_ids)
        self.file_utils.save_to_json(tf_graph_file, graphData.tf_graph)

    def process_tfstate(self, tf_state_file, graph_folder_name):
        print("")
        print("START ****** process tf_module: " , graph_folder_name, tf_state_file)
        state_dict = self.file_utils.load_json_file(tf_state_file)
        resources = state_dict['resources']

        # tf_resources={}
        # tf_resources_var_to_ids = {}
        # tf_resources_links = {}
        # tf_graph = {}
        graphData = GraphData(graph_folder_name)

        self.tf_modules[graph_folder_name] = self.tf_module_counter
        self.tf_module_counter = self.tf_module_counter + 1
        for resource in resources:
            tf_resource = {}
            tf_resource['type']=resource['type']
            tf_resource['name'] = resource['name']
            tf_resource['provider'] = resource['provider']
            tf_resource['module'] = graph_folder_name
            tf_resource['group'] = self.tf_modules[graph_folder_name]
            #
            attributes = resource['instances'][0]['attributes']
            tf_resource['attributes'] = attributes
            #
            var_name = "{0}.{1}".format(resource['type'], resource['name'])
            id = attributes['id']
            tf_resource['aws_id'] = id
            tf_resource['id'] = var_name
            tf_resource['var_name'] = var_name
            tf_resource['svd_id'] = var_name
            #
            graphData.tf_resources[var_name] = tf_resource
            if id not in graphData.tf_resources_var_to_ids:
                graphData.tf_resources_var_to_ids[id] = []
            graphData.tf_resources_var_to_ids[id].append(var_name)
            print("resource",var_name, id, graphData.tf_resources_var_to_ids[id])

        # links
        self.find_links(graphData)
        self.create_parent_child(graphData)

        ##
        graph_folder = os.path.dirname(tf_state_file)
        self.save_graph_data(graph_folder, graphData)

        # merge to global
        self.graphData_all.tf_resources = self.merge_dict( self.graphData_all.tf_resources, graphData.tf_resources)
        self.graphData_all.tf_resources_var_to_ids = self.merge_dict(self.graphData_all.tf_resources_var_to_ids, graphData.tf_resources_var_to_ids)
        self.graphData_all.tf_resources_links = self.merge_dict(self.graphData_all.tf_resources_links, graphData.tf_resources_links)
        self.graphData_all.tf_resources_parent_links = self.merge_dict(self.graphData_all.tf_resources_parent_links, graphData.tf_resources_parent_links)
        self.graphData_all.tf_graph= self.merge_dict(self.graphData_all.tf_graph, graphData.tf_graph)

        print("DONE ****** process tf_module: ", graph_folder_name, tf_state_file)
        print("")

    def find_links(self, graphData):
        tf_resource_var_names = list(graphData.tf_resources.keys())
        for tf_resource_var_name in tf_resource_var_names:
            self.find_link(tf_resource_var_name, graphData)
        self.create_nodes_and_links(graphData)


    def find_link(self, tf_resource_var_name_src, graphData):
        tf_resource_var_names = list(graphData.tf_resources.keys())
        for tf_resource_var_name in tf_resource_var_names:
            if tf_resource_var_name_src == tf_resource_var_name:
                continue #skip this one

            #skip if id is duplicate object?
            tf_resource_src = graphData.tf_resources[tf_resource_var_name_src]
            tf_resource_var_names_src = graphData.tf_resources_var_to_ids[tf_resource_src['aws_id']]
            if tf_resource_var_name in tf_resource_var_names_src:
                continue  # skip this one
            # check if id in this ojbect
            tf_resource_dest = graphData.tf_resources[tf_resource_var_name]
            dest_str = json.dumps(tf_resource_dest)
            src_id = tf_resource_src['aws_id']
            if "\"{0}\"".format(src_id)  in dest_str:
                #parent holds childs
                if tf_resource_var_name_src not in graphData.tf_resources_links:
                    graphData.tf_resources_links[tf_resource_var_name_src] = []
                graphData.tf_resources_links[tf_resource_var_name_src].append(tf_resource_var_name)
                #rever realtionship -- child holds parent
                if tf_resource_var_name not in graphData.tf_resources_parent_links:
                    graphData.tf_resources_parent_links[tf_resource_var_name] = []
                graphData.tf_resources_parent_links[tf_resource_var_name].append(tf_resource_var_name_src)

    def create_nodes_and_links(self, graphData):
        nodes =  list(graphData.tf_resources.values())
        src_svd_ids = list(graphData.tf_resources_links.keys())
        conuter_svd_id = 1
        links = []
        for src_svd_id in src_svd_ids:
            # need some config as it could nd parent or child
            dest_svd_ids = graphData.tf_resources_links[src_svd_id]
            value = len(dest_svd_ids)
            for dest_svd_id in dest_svd_ids:
                #{"source": "Napoleon", "target": "Myriel", "value": 1},
                src_tf_resource =  graphData.tf_resources[src_svd_id]
                module = src_tf_resource['module']
                id = "svd_link_id_{0}".format(conuter_svd_id)
                conuter_svd_id = conuter_svd_id + 1
                group = self.tf_modules[module]
                link = {"source": src_svd_id, "target": dest_svd_id, "value":value
                    , "svd_link_id": id, "group":group, "module": module}
                links.append(link)
        graphData.tf_graph["nodes"] = nodes
        graphData.tf_graph["links"] = links


    def create_parent_child(self, graphData):
        parent_svd_ids = list(graphData.tf_resources_links.keys())
        processed_ids=[]
        processed_item_ids = []
        for parent_svd_id in parent_svd_ids:
            # self._create_parent_child_tree_ids(parent_svd_id, graphData.tf_tree_ids, processed_ids, graphData)
            self._create_parent_child_tree(parent_svd_id, graphData.tf_tree_children, processed_item_ids, graphData)

        # self.file_utils.print_json(graphData.tf_tree)

    def _create_parent_child_tree(self, parent_svd_id, parent_tf_tree_children, processed_ids, graphData):
        if parent_svd_id in processed_ids:
            print("parent_svd_id already processed ", parent_svd_id)
            return
        processed_ids.append(parent_svd_id)
        if parent_svd_id not in graphData.tf_resources_links:
            print("parent_svd_id no children ", parent_svd_id)
            return

        svd_ids = graphData.tf_resources_links[parent_svd_id]
        print(len(svd_ids), "_create_parent_child", parent_svd_id, ",".join(svd_ids))
        tree_graph_children=[]
        tree_graph = {
            "name": parent_svd_id,
            "data": graphData.tf_resources[parent_svd_id],
            "children": tree_graph_children
        }
        parent_tf_tree_children.append(tree_graph)
        for svd_id in svd_ids:
            self._create_parent_child_tree(svd_id, tree_graph_children, processed_ids, graphData)

    def _create_parent_child_tree_ids(self, parent_svd_id, parent_tree_graph, processed_ids, graphData):
        if parent_svd_id  in processed_ids:
            print("parent_svd_id already processed ", parent_svd_id)
            return
        processed_ids.append(parent_svd_id)
        if parent_svd_id not in graphData.tf_resources_links:
            print("parent_svd_id no children ", parent_svd_id)
            return

        svd_ids = graphData.tf_resources_links[parent_svd_id]
        print( len(svd_ids), "_create_parent_child", parent_svd_id, ",".join(svd_ids))
        tree_graph = {}
        parent_tree_graph[parent_svd_id] = tree_graph
        for svd_id in svd_ids:
            self._create_parent_child_tree_ids(svd_id, tree_graph, processed_ids,  graphData)



if __name__ == '__main__':
    params = AwsImportParameters()
    params.step_type = "graph"
    params.module = "graph"
    graph_utils = GenNodesLinks(params)
    graph_utils.process_dir("/Users/brighu/_duplo_code/duplocli/work/graph")
    # graph_utils.create_icons("/Users/brighu/_duplo_code/duplocli/work/graph/infra/main.tf.json")


    # graph_utils.process_tfstate("/Users/brighu/_duplo_code/duplocli/work/graph/infra/terraform.tfstate")


    print("")


