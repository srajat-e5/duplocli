import json


class AwsTfResourceSchema :
    def __init__(self,  tf_obj_name, tf_object):
        self.tf_obj_name=tf_obj_name
        self.tf_object=tf_object
        #attributes
        self.non_computed = []
        self.computed = []
        self.optional = []
        self.required = []
        self.sensitive = []
        #?
        self.all_attributes = []
        self.data_type = {}
        # nested hash-table
        self.nested_block  = {}
        self.spec= {"nesting_mode": ""}
        self.nested = []

    def __str__(self):
        return json.dumps(self.data_dict())

    def copy(self):
        # only copy useful things, neglect debug list/maps
        tf = AwsTfResourceSchema(self.tf_obj_name, self.tf_object)
        tf.non_computed = self.non_computed
        tf.computed = self.computed
        tf.optional = self.optional
        tf.all_attributes = self.all_attributes
        tf.sensitive = self.sensitive
        tf.required = self.required
        tf.data_type = self.data_type
        tf.nested_block = self.nested_block
        tf.spec = self.spec
        tf.nested = self.nested
        tf.nested_block = self.nested_block
        return  tf

    def update_nested(self):
        self.nested = []
        for nested_block_name, nested_block in self.nested_block.items():
            self.nested.append(nested_block_name)
            self.all_attributes.append(nested_block_name)

    def data_dict(self):
        data = {}
        data['non_computed'] = self.non_computed
        data['computed'] = self.computed
        data['optional'] = self.optional
        data['all_attributes'] = self.all_attributes
        data['sensitive'] = self.sensitive
        data['required'] = self.required
        data['data_type'] = self.data_type

        # nested hash-table
        data['nested'] = self.nested
        data['nested_block'] = {}
        for nested_block_name, nested_block in self.nested_block.items():
            data['nested_block'][nested_block_name] = nested_block.data_dict()
        data['spec'] = self.spec
        return data
