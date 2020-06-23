import sys
import json
import datetime
import os
from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.schema.tf_resource_schema import TfResourceSchema

class TfSchema:
    tfschema={}
    tf_resource_list = {}
    tf_resource_list_inited = False
    debug = False
    def __init__(self,  params ):
        self.params = params
        self.utils = TfUtils(self.params)
        json_file  = self.get_schema_file()
        with open(json_file) as f:
            self.tfschema = json.load(f)

    def get_schema_file(self):
        # json_file_prefix="json_aws_tf_schema.json"
        json_file = "json_{0}_tf_schema.json".format(self.params.provider)
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), json_file)
        if not os.path.exists(json_path):
            raise Exception("schema {0} not found".format(json_path))
        return json_path

    ######## debug  ########
    def get_tf_resource_names_list(self):
        return list(self.get_tf_resource_list().keys())

    def data_dict_tf_resource_list(self):
        data={}
        list = self.get_tf_resource_list()
        for key, tf_resource in list.items():
            data[key] = tf_resource.data_dict()
        return data
     ######## debug ########


    def get_schema_raw(self, tf_obj_name):
        return self.tfschema['provider_schemas'][self.params.provider]['resource_schemas'][tf_obj_name]

    def get_tf_resource_list(self):
        if not self.tf_resource_list_inited:
            #load once and catch
            for tf_obj_name, tf_object in self.tfschema['provider_schemas'][self.params.provider]['resource_schemas'].items():
                self.get_tf_resource(tf_obj_name)
            self.tf_resource_list_inited = True
        return self.tf_resource_list

    def get_tf_resource(self, tf_obj_name):
        try:
            if tf_obj_name  in self.tf_resource_list.keys():
                pass
                # print("**** SCHEMA: get_tf_resource ******* ",tf_obj_name," exist in catch")
            else:
                # print("**** SCHEMA:  get_tf_resource ******* ", tf_obj_name, self.tf_resource_list.keys(), "*********** START")
                tf_resource_root = self._process_root(tf_obj_name)
                tf_resource_root.update_nested()
                self._catch_resource(tf_obj_name, tf_resource_root)
                # print("**** SCHEMA: get_tf_resource ******* ", tf_resource_root.tf_obj_name, str(tf_resource_root),
                #   "*********** DONE")
            return self.tf_resource_list[tf_obj_name]
        except KeyboardInterrupt:
         quit()
        except Exception as e:
            print("**** SCHEMA: get_tf_resource Failed to generate " + tf_obj_name)
            print('**** SCHEMA: get_tf_resource Error: {}'.format(sys.exc_info()[0]))
            return None

    ######
    def _catch_resource(self, tf_obj_name, tf_resource):
        # print("**** SCHEMA: _catch_resource",tf_obj_name, tf_resource )
        self.tf_resource_list[tf_obj_name] = tf_resource.copy()

    def _process_root(self, tf_obj_name):
        tf_object = self.get_schema_raw(tf_obj_name)
        tf_resource = TfResourceSchema(tf_obj_name, tf_object)
        self._process_attributes(tf_resource)
        if 'block_types' in  tf_resource.tf_object['block']:
            self._process_blocks_nested(tf_resource)
        return tf_resource.copy()

    ######
    def _process_attributes(self, tf_resource):
        try:
            if 'attributes' in tf_resource.tf_object['block']:
                for attrname, attr in  tf_resource.tf_object['block']['attributes'].items():
                    computed = False
                    sensitive = False
                    optional = False
                    required = False
                    opts=[]
                    type=None
                    tf_resource.all_attributes.append(attrname)
                    for key1, val1 in attr.items():
                        if key1 != 'type':
                            opts.append(computed)
                        if key1 == 'computed':
                            computed = val1
                        elif key1 == 'optional':
                            optional = val1
                        elif key1 == 'sensitive':
                            sensitive = val1
                        elif key1 == 'required':
                            required = val1
                            # tf_resource.required.append(attrname)
                        elif key1 == 'type':
                            type = val1
                            tf_resource.data_type[attrname]= str(val1)

                    if sensitive:
                        tf_resource.sensitive.append(attrname)
                    if required:
                        tf_resource.required.append(attrname)
                    if optional:
                        tf_resource.optional.append(attrname)

                    if computed :
                        #TF has bugs ?... needs some additional work based on bugs
                        # todo check if its set, list, dict,tupple etc
                        # tf_resource.computed.append(attrname)
                        # if not "optional" in opts:
                        #     tf_resource.computed.append(attrname)
                        # el
                        if  not self.utils.is_native_type(type) :
                            tf_resource.non_computed.append(attrname)
                        else:
                            tf_resource.computed.append(attrname)
                    else:
                        tf_resource.non_computed.append(attrname)
        except KeyboardInterrupt:
            quit()
        except Exception as e:
            print("**** SCHEMA: _process_attributes Failed to generate " +  tf_resource.tf_obj_name)
            print('**** SCHEMA: _process_attributes Error: {}'.format(sys.exc_info()[0]))
        # print("**** SCHEMA: _process_attributes******* ", tf_resource.tf_obj_name, "*********** END")

    def _process_blocks_nested(self, tf_resource):
        try:
            if 'block_types' not in tf_resource.tf_object['block']:
                return
            block_types = tf_resource.tf_object['block']['block_types']
            for tf_obj_name_nested, tf_object_nested in block_types.items():
                # print("**** SCHEMA: _process_blocks_nested******* ", tf_obj_name_nested, "*********** start")
                tf_resource_child = TfResourceSchema(tf_obj_name_nested, tf_object_nested)
                self._process_attributes(tf_resource_child)
                self._process_spec_for_nested(tf_resource_child, tf_object_nested)
                tf_resource.nested_block[tf_obj_name_nested] = tf_resource_child
                # print("**** SCHEMA: _process_blocks_nested******* ", tf_obj_name_nested ,  tf_resource.data_dict(), "*********** END")
        except Exception as e:
            print("**** SCHEMA: _process_blocks_nested Failed to generate " + tf_resource.tf_obj_name)
            print('**** SCHEMA: _process_blocks_nested Error: {}'.format(sys.exc_info()[0]))

    def _process_spec_for_nested(self, tf_resource, block_type):
        for spec_key, spec_val in block_type.items():
            if spec_key == 'block' or spec_key == 'block_types':
                pass
            else:
                tf_resource.spec[spec_key]=spec_val

    ## use from common utils
    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    def save_json(self, response, file_name):
        resp_json = json.dumps(response, sort_keys=True,
                               indent=1,
                               default=self.default)
        f = open(file_name, "w")
        f.write(resp_json)
        f.close()


#
# # ##### test ##########
# from duplocli.terraform.import_parameters import AwsImportParameters
# def main1():
#     params = AwsImportParameters()
#     params.provider="azurerm"
#     awsParseSchema = TfSchema(params)
#     data_dict_tf_resource_list = awsParseSchema.data_dict_tf_resource_list()
#     awsParseSchema.save_json(data_dict_tf_resource_list, "../data/duplo_{0}_tf_schema.json".format(params.provider))
#     print(json.dumps(data_dict_tf_resource_list))
#
#     tf_resource_names_list = awsParseSchema.get_tf_resource_names_list()
#     print(json.dumps(tf_resource_names_list))
#     awsParseSchema.save_json(tf_resource_names_list, "../data/{0}_resources.json".format(params.provider))
#
# if __name__ == '__main__':
#     main1()
#