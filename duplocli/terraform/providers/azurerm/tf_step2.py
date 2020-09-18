from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep

class AzurermTfImportStep2(AzureBaseTfImportStep):

    is_allow_none = True
    state_dict = {}

    def __init__(self, params):
        super(AzurermTfImportStep2, self).__init__(params)

    def execute(self):
        self._tf_resources()
        self._create_tf_state()
        return self.file_utils.tf_main_file()
    
    ##### manage files and state ##############
    def _create_tf_state(self):
        self.file_utils.save_state_file(self.state_dict)
        super()._create_tf_state()

    ######  TfImportStep2 ################################################
    def _tf_resources(self):
        self.state_read_from_file = self.file_utils.tf_state_file_srep1()
        self.state_dict = self.file_utils.load_json_file(self.state_read_from_file)
        if "resources" in  self.state_dict:
            resources = self.state_dict['resources']
        else:
            resources = self.state_dict['resource']
        for resource in resources:
            try:
                self._tf_resource(resource)
            except Exception as e:
                print("ERROR:Step2:","_tf_resources", e)

        return self.main_tf_json_dict

    #############
    def _tf_resource(self, resource):
        nested_count = 1
        tf_resource_type = resource["type"]
        tf_resource_var_name = resource["name"]
        print(self.file_utils.stage_prefix(), nested_count, tf_resource_type,  tf_resource_var_name, "=", tf_resource_var_name)
        attributes = resource['instances'][0]['attributes']
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        tf_resource_type_root[tf_resource_var_name] = resource_obj
        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)

        for attribute_name, attribute  in attributes.items():
            try:
                is_nested = attribute_name  in schema.nested
                is_computed = attribute_name  in schema.computed
                is_optional = attribute_name  in schema.optional
                if is_nested:
                    self._process_nested(nested_count, tf_resource_type,  tf_resource_var_name, attribute_name, attribute, resource_obj, schema)
                elif isinstance(attribute, dict):
                    resource_obj_dict = {}
                    resource_obj[attribute_name] = resource_obj_dict
                    self._process_dict(nested_count, tf_resource_type,  tf_resource_var_name, resource_obj_dict, attribute_name, attribute, None)
                elif isinstance(attribute, list):
                    resource_obj_dict = []
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            resource_obj_list = {}
                            resource_obj_dict.append(resource_obj_list)
                            self._process_dict(nested_count, tf_resource_type,  tf_resource_var_name, resource_obj_list, attribute_name, nested_item, None)
                        elif isinstance(nested_item, list):
                            print(self.file_utils.stage_prefix(), "_process_nested  is list list nested list ???? ", nested_count, tf_resource_type,  tf_resource_var_name, attribute_name)
                            #pass
                        else:
                            resource_obj_dict.append(nested_item)
                    if len(resource_obj_dict) > 0 :
                        resource_obj[attribute_name] = resource_obj_dict
                elif is_optional or not is_computed :
                    if attribute_name == "id":
                        pass
                    elif isinstance(attribute, bool):
                        resource_obj[attribute_name] = attribute
                    elif attribute == 0:
                        pass
                    elif attribute is not None and attribute != ""  :  #attribute is not None  or self.is_allow_none : #or  (isinstance(object, list) and len(list) > 0)
                        resource_obj[attribute_name]=attribute
                else:
                    pass
            except Exception as e:
                print("ERROR:Step2:","_tf_resource", e)

        resource_obj2 = self.remove_empty(tf_resource_type, tf_resource_var_name, resource_obj)
        # print("after ",  resource_obj2)
        # if tf_resource_type == 'azurerm_image':
        #     if 'hyper_v_generation' not in resource_obj2:
        #         resource_obj2['hyper_v_generation'] = ""
        tf_resource_type_root[tf_resource_var_name] = resource_obj2

    # azurerm_network_security_group
    # Inappropriate
    # value
    # for attribute "security_rule": element
    # 0: attributes
    # "description", "destination_address_prefix", "destination_address_prefixes",
    # "destination_port_ranges", "source_address_prefixes",
    # "source_application_security_group_ids", and "source_port_ranges"
    # are
    # required.
    def _process_dict(self, nested_count_parent, tf_resource_type,  tf_resource_var_name, resource_obj, nested_atr_name, nested_atr, schema):
        nested_count = nested_count_parent + 1
        for attribute_name, attribute in nested_atr.items():
            try:
                if self.processIfNested(nested_count, tf_resource_type,  tf_resource_var_name, attribute_name, attribute, resource_obj, schema):
                    return
                if schema is None or not attribute_name in schema.computed:
                    if isinstance(attribute, bool):
                        resource_obj[attribute_name] = attribute
                    elif attribute == 0:
                        pass
                    elif attribute is not None and attribute != "":  # attribute is not None or self.is_allow_none:
                        resource_obj[attribute_name] = attribute
                    else:
                        pass
            except Exception as e:
                print("ERROR:Step2:","_process_dict", e)

        if tf_resource_type == 'azurerm_network_security_group' and  nested_atr_name == 'security_rule':
            self._set_val(resource_obj, "description",  "")
            self._set_val(resource_obj, "destination_address_prefix", [])
            self._set_val(resource_obj, "destination_address_prefixes", [])
            self._set_val(resource_obj, "destination_port_ranges", [])
            self._set_val(resource_obj, "source_port_ranges", [])
            self._set_val(resource_obj, "source_address_prefixes", [])
            self._set_val(resource_obj, "source_application_security_group_ids", "")
            self._set_val(resource_obj, "source_port_ranges", "")


    def _set_val(self, resource_obj, attribute_name, attribute):
        if attribute_name  not in resource_obj.keys():
            resource_obj[attribute_name] = attribute

    def _process_nested(self, nested_count_parent, tf_resource_type,  tf_resource_var_name, nested_atr_name, nested_atr, resource_obj_parent, schema_nested):
        try:
            nested_count = nested_count_parent + 1
            schema = schema_nested.nested_block[nested_atr_name]
            if isinstance(nested_atr, dict):
                resource_obj = {}
                resource_obj_parent[nested_atr_name] = resource_obj
                self._process_dict(nested_count  , tf_resource_type,  tf_resource_var_name, resource_obj, nested_atr_name, nested_atr, schema)
            elif isinstance(nested_atr, list): #aa
                resource_obj = []
                # resource_obj_parent[nested_atr_name] = resource_obj
                for nested_item in nested_atr:
                    if isinstance(nested_item, dict):
                        resource_obj_list = {}
                        self._process_dict(nested_count, tf_resource_type,  tf_resource_var_name, resource_obj_list,nested_atr_name,  nested_item,  schema)
                        resource_obj.append(resource_obj_list)
                    elif isinstance(nested_item, list):
                        print("WARN:", self.file_utils.stage_prefix(), " _process_nested  is list list nested list ???? ", nested_count, tf_resource_type,  tf_resource_var_name,  nested_atr_name)
                        #pass
                    else:
                        resource_obj.append(nested_item)
                if len(resource_obj) > 0:
                    resource_obj_parent[nested_atr_name] = resource_obj
            else:
                pass
                # print("Warn: Nested non dict/list?")
        except Exception as e:
            print("ERROR:Step2:", "_process_nested", e)

    def processIfNested(self, nested_count_parent, tf_resource_type,  tf_resource_var_name, resource_obj, attribute_name, attribute, schema):
        if schema is not None:
            is_nested = attribute_name in schema.nested
            if is_nested:
                self._process_nested(nested_count_parent, tf_resource_type, tf_resource_var_name, attribute_name, attribute,
                                     resource_obj, schema)
                return True
        return False

    def remove_empty(self, tf_resource_type, tf_resource_var_name, json_dict):
        final_dict = {}
        for attrName, attrValue in json_dict.items():
            try:
                if isinstance(attrValue , bool):
                    final_dict[attrName] = attrValue
                elif attrValue :
                    if isinstance(attrValue, dict):
                        if tf_resource_type == 'azurerm_network_security_group' and attrName == 'security_rule':
                            pass
                        else:
                            final_dict[attrName] = self.remove_empty(attrValue)
                    elif isinstance(attrValue, list):
                        if len(attrValue) > 0:
                            resource_obj = []
                            for nested_item in attrValue:
                                if isinstance(nested_item, dict):
                                    nested_item_value = self.remove_empty(nested_item)
                                    if nested_item_value and len(nested_item_value) > 0:
                                        resource_obj.append(nested_item_value)
                                else:
                                    resource_obj.append(nested_item)
                            if len(resource_obj)>0:
                                final_dict[attrName] = resource_obj

                    else:
                        final_dict[attrName] = attrValue
                else:
                    pass
                    #print("empty??",  attrName, attrValue )
            except Exception as e:
                print("ERROR:Step2:","remove_empty", e)
        return final_dict