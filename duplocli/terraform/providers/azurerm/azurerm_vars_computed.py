from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import json

class AzurermTfVarsComputed():

    def __init__(self, parent):
        self.parent = parent

    def _resource_array_by_type_computed(self, resource, resource_object):
        nested_count = 1
        tf_resource_type = resource["tf_type"]
        tf_resource_var_name = resource["tf_var_name"]
        attributes = resource
        nested_count = 1
        schema = self.parent.aws_tf_schema.get_tf_resource(tf_resource_type)
        for attribute_name, attribute in attributes.items():
            try:
                is_nested = attribute_name in schema.nested
                is_computed = attribute_name in schema.computed
                is_optional = attribute_name in schema.optional
                parent_set = [tf_resource_type, tf_resource_var_name, attribute_name]
                if is_computed:
                    if  is_nested:
                        self._process_nested_computed(nested_count, parent_set, tf_resource_type, tf_resource_var_name,
                                                 attribute_name, attribute, schema, resource_object)
                    else:
                        resource_object[attribute_name] = attribute
            except Exception as e:
                print("ERROR:Step3:", "_resource_array_by_type_computed", e)


    def _process_nested_computed(self, nested_count_parent, parent_set,  tf_resource_type,  tf_resource_var_name, nested_atr_name, nested_atr,   schema_nested, resource_object_parent):
        try:
            nested_count = nested_count_parent + 1
            schema = schema_nested.nested_block[nested_atr_name]
            if isinstance(nested_atr, dict):
                resource_object = {}
                resource_object_parent[nested_atr_name] = resource_object
                self._process_dict_computed(nested_count, parent_set, tf_resource_type,  tf_resource_var_name,  nested_atr_name, nested_atr, schema, resource_object_parent)
            elif isinstance(nested_atr, list):
                resource_object = {}
                for nested_item in nested_atr:
                    if isinstance(nested_item, dict):
                        self._process_dict_computed(nested_count, parent_set, tf_resource_type,  tf_resource_var_name,  nested_atr_name,  nested_item,  schema)
                    else:
                        is_computed = schema is not None and nested_atr_name in schema.computed
                        self.set_value_cout(nested_count, is_computed, parent_set, tf_resource_type, tf_resource_var_name, nested_item, nested_atr_name)
            else:
                resource_object_parent[nested_atr_name] = nested_atr
                print("Warn: _process_nested_computed Nested non dict/list?")
        except Exception as e:
            print("ERROR:Step3:", "_process_nested_computed", e)

    def _process_dict_computed(self, nested_count_parent, root_parent_set, tf_resource_type,  tf_resource_var_name,  nested_atr_name, nested_atr, schema):
        nested_count = nested_count_parent + 1
        for attribute_name, attribute in nested_atr.items():
            try:
                parent_set =  list(root_parent_set)
                parent_set.append(attribute_name)
                is_computed = attribute_name in schema.computed
                if self.processIfNested(nested_count, parent_set, tf_resource_type,  tf_resource_var_name, attribute_name, attribute,  schema):
                    return
                if isinstance(attribute, list):
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._process_dict(nested_count, parent_set, tf_resource_type, tf_resource_var_name,
                                                 nested_atr_name, nested_item, schema)
                        elif isinstance(nested_item, list):
                            print("WARN:", self.parent.file_utils.stage_prefix(),
                                  " _process_nested  is list list nested list ???? ", nested_count, tf_resource_type,
                                  tf_resource_var_name, nested_atr_name)
                        else:
                            self.set_value_cout(nested_count, is_computed, parent_set, tf_resource_type,
                                                tf_resource_var_name, nested_item, nested_atr_name)
                else:

                    self.set_value_cout(nested_count, is_computed, parent_set, tf_resource_type, tf_resource_var_name, attribute, attribute_name)

            except Exception as e:
                print("ERROR:Step2:","_process_dict", e)


    def processIfNested(self, nested_count_parent, parent_set, tf_resource_type,  tf_resource_var_name,  attribute_name, attribute, schema):
        if schema is not None:
            is_nested = attribute_name in schema.nested
            if is_nested:
                self._process_nested(nested_count_parent, parent_set, tf_resource_type, tf_resource_var_name, attribute_name, attribute,
                                     schema)
                return True
        return False

    def set_value_cout(self, nested_count, is_computed,  parents, tf_resource_type, tf_resource_var_name, attribute, attribute_name):
        parents_str = ".".join(parents)
        if attribute is not None and attribute != "":
            if attribute in self.parent.value_count:
                self.parent.value_count[attribute] = self.parent.value_count[attribute] + 1
            else:
                self.parent.value_count[attribute] = 1
            if attribute in self.parent.value_keys:
                self.parent.value_keys[attribute].add(parents_str)
            else:
                self.parent.value_keys[attribute] = {parents_str}

            if is_computed:
                if attribute in self.parent.value_computed:
                    self.parent.value_computed[attribute].add(parents_str)
                else:
                    self.parent.value_computed[attribute] = {parents_str}