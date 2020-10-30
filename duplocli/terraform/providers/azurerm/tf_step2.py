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
        if not self.file_utils.file_exists(self.state_read_from_file):
            raise Exception("Error: Aborting import. Step1 failed to import terraform. Please check cred/permissions.")

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

    ############

    def _set_val(self, resource_obj, attribute_name, attribute):
        if attribute_name  not in resource_obj.keys():
            resource_obj[attribute_name] = attribute
    def _set_val_array(self, resource_obj, attribute_name, attribute):
        if attribute_name  not in resource_obj.keys():
            if resource_obj[attribute_name] in None:
                resource_obj[attribute_name] = []
            if isinstance(attribute_name, list):
                pass
    def _del_key(self, final_dict, attrName):
        try:
            del final_dict[attrName]
        except KeyError as ex:
            print("No such key: '%s'" % ex.message)

    def _processIfNested(self, nested_count_parent, tf_resource_type, tf_resource_var_name, resource_obj, attribute_name, attribute, schema):
        if schema is not None:
            is_nested = attribute_name in schema.nested
            if is_nested:
                self._process_nested(nested_count_parent, tf_resource_type, tf_resource_var_name, attribute_name, attribute,
                                     resource_obj, schema)
                return True
        return False

    #############
    def _tf_resource(self, resource):
        nested_count = 1
        tf_resource_type = resource["type"]
        tf_resource_var_name = resource["name"]
        print(self.file_utils.stage_prefix(), nested_count, tf_resource_type,  tf_resource_var_name, "=", tf_resource_var_name)
        attributes = resource['instances'][0]['attributes']
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        # tf_resource_type_root[tf_resource_var_name] = resource_obj
        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
        if tf_resource_type == "azurerm_container_group":
            pass
        for attribute_name, attribute  in attributes.items():
            try:
                is_nested = attribute_name  in schema.nested
                is_computed = attribute_name  in schema.computed
                is_optional = attribute_name  in schema.optional
                if is_nested:
                    self._process_nested(nested_count, tf_resource_type,  tf_resource_var_name, attribute_name, attribute, resource_obj, schema)
                elif isinstance(attribute, dict):
                    # if is_computed:
                    #     pass
                    # else:
                    resource_obj_dict = {}
                    resource_obj[attribute_name] = resource_obj_dict
                    self._process_dict(nested_count, tf_resource_type,  tf_resource_var_name, resource_obj_dict, attribute_name, attribute, None)
                elif isinstance(attribute, list):
                    # if is_computed:
                    #     pass
                    # el
                    if tf_resource_type == 'azurerm_route_table' and attribute_name == 'subnets':
                        pass
                    elif tf_resource_type == 'azurerm_network_interface' and attribute_name in ['private_ip_address', 'private_ip_addresses']:
                        pass
                    else:
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
                        # if is_computed:
                        #     pass
                        #else:
                        resource_obj[attribute_name] = resource_obj_dict
                elif is_optional or not is_computed :
                    if attribute_name == "id":
                        pass
                    elif tf_resource_type == 'azurerm_network_interface' and attribute_name in ['private_ip_address', 'private_ip_addresses']:
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
        if tf_resource_type in ['Aazurerm_virtual_machine', 'azurerm_monitor_metric_alert']:
            pass #resource_obj = resource_obj  # resource_obj2
        else:
            resource_obj = resource_obj2
        if tf_resource_type in ['azurerm_route_table'] and "subnets" in resource_obj:
            self._del_key(resource_obj, "subnets")
        if tf_resource_type in ['azurerm_monitor_metric_alert']  and ( not "name" in resource_obj or resource_obj["name"] ==""):
            resource_obj["name"] = resource_obj["resource_group_name"]

        #set
        resource_obj = self._post_tf_resource(resource, tf_resource_type_root, tf_resource_var_name, resource_obj)


    def _post_tf_resource(self, resource, tf_resource_type_root,  tf_resource_var_name, resource_obj):
        try:
            tf_resource_type = resource["type"]
            #tf_resource_var_name = resource["name"]
            if tf_resource_type in ['azurerm_storage_account']:
                import random
                number = random.randit(1111, 9999)
                resource_obj["name"] = "{0}-{1}".format(self.params.tenant_name.lower(), number)
                self._del_key(resource_obj, "queue_properties")
        except Exception as e:
            print("ERROR:Step2:", "_tf_resource", e)
        tf_resource_type_root[tf_resource_var_name] = resource_obj
        return resource_obj

    def _process_dict(self, nested_count_parent, tf_resource_type,  tf_resource_var_name, resource_obj, nested_atr_name, nested_atr, schema):
        nested_count = nested_count_parent + 1
        #https://registry.terraform.io/modules/innovationnorway/sql-server/azurerm/latest
        for attribute_name, attribute in nested_atr.items():
            try:
                # if tf_resource_type == "azurerm_container_group":
                #     pass
                if self._processIfNested(nested_count, tf_resource_type, tf_resource_var_name, attribute_name, attribute, resource_obj, schema):
                    return
                if schema is None or not attribute_name in schema.computed:
                    if isinstance(attribute, bool):
                        resource_obj[attribute_name] = attribute
                    elif tf_resource_type == "azurerm_container_group" and nested_atr_name == 'container' and attribute_name in ["volume"]:
                        pass  # skip
                    elif attribute == 0:
                        pass
                    # if tf_resource_type == 'azurerm_route_table' and nested_atr_name == 'route' and attribute_name == 'next_hop_in_ip_address':
                    #     pass
                    elif attribute is not None and attribute != "":  # attribute is not None or self.is_allow_none:
                        resource_obj[attribute_name] = attribute
                    else:
                        pass
            except Exception as e:
                print("ERROR:Step2:","_process_dict", e)
        if tf_resource_type == 'azurerm_application_gateway' and nested_atr_name == 'backend_address_pool':
            if 'fqdns' in resource_obj and len(resource_obj['fqdns']) ==0:
                del resource_obj['fqdns']
        if tf_resource_type == 'azurerm_route_table' and nested_atr_name == 'route':
            self._set_val(resource_obj, "next_hop_in_ip_address", "")
        elif tf_resource_type == 'azurerm_network_security_group' and  nested_atr_name == 'security_rule':
            self._set_val(resource_obj, "description",  "")
            self._set_val(resource_obj, "source_application_security_group_ids", "")
            #destination_address
            self._set_val(resource_obj, "destination_address_prefix", [])
            self._set_val(resource_obj, "destination_address_prefixes", [])
            self._set_val(resource_obj, "destination_port_ranges", [])
            #source_address
            self._set_val(resource_obj, "source_address_prefix", "")
            self._set_val(resource_obj, "source_address_prefixes", [])
            self._set_val(resource_obj, "source_port_ranges", [])
            # self._set_val(resource_obj, "source_port_range", "")
        # if tf_resource_type == 'azurerm_virtual_machine' and nested_atr_name == 'identity':
        #     self._set_val(resource_obj, "identity_ids", [{
        #         "identity_ids": [] }])
        if tf_resource_type == 'azurerm_virtual_machine' and nested_atr_name == 'boot_diagnostics':
            self._set_val(resource_obj, "enabled",  False)
            self._set_val(resource_obj, "storage_uri", "")

    def _process_nested(self, nested_count_parent, tf_resource_type,  tf_resource_var_name, nested_atr_name, nested_atr, resource_obj_parent, schema_nested):
        try:
            nested_count = nested_count_parent + 1
            schema = schema_nested.nested_block[nested_atr_name]
            if isinstance(nested_atr, dict):
                if nested_atr_name in schema.computed:
                    pass
                else:
                    resource_obj = {}
                    resource_obj_parent[nested_atr_name] = resource_obj
                    self._process_dict(nested_count  , tf_resource_type,  tf_resource_var_name, resource_obj, nested_atr_name, nested_atr, schema)
            elif isinstance(nested_atr, list): #aa
                if nested_atr_name in schema.computed:
                    pass
                else:
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


    def remove_empty(self, tf_resource_type, tf_resource_var_name, json_dict):
        final_dict = {}
        for attrName, attrValue in json_dict.items():
            try:
                if isinstance(attrValue , bool):
                    final_dict[attrName] = attrValue
                else:
                    if tf_resource_type == 'azurerm_network_security_group' and attrName == 'security_rule':
                        pass
                    # elif tf_resource_type == 'azurerm_virtual_machine' and attrName in ['identity',  'boot_diagnostics', 'identity_ids']:
                    #     pass
                    elif tf_resource_type == 'azurerm_route_table' and attrName in ['route']:
                        pass
                    elif tf_resource_type == 'azurerm_monitor_metric_alert' and attrName in ['name', 'scopes']:
                        pass
                    elif tf_resource_type == 'azurerm_app_service' and attrName in ['site_credential','source_control']:
                        self._del_key(final_dict, attrName)
                    elif tf_resource_type == 'azurerm_app_service_certificate' and attrName in ['host_names']:
                        self._del_key(final_dict, attrName)
                    elif isinstance(attrValue, dict):
                        final_dict[attrName] = self.remove_empty( tf_resource_type, tf_resource_var_name, attrValue)
                    elif isinstance(attrValue, list):
                        if len(attrValue) > 0:
                            resource_obj = []
                            for nested_item in attrValue:
                                if isinstance(nested_item, dict):
                                    nested_item_value = self.remove_empty( tf_resource_type, tf_resource_var_name, nested_item)
                                    if nested_item_value and len(nested_item_value) > 0:
                                        resource_obj.append(nested_item_value)
                                else:
                                    if tf_resource_type == 'azurerm_route_table' and attrName == 'route':
                                        pass
                                    else:
                                        resource_obj.append(nested_item)
                            if len(resource_obj)>0:
                                final_dict[attrName] = resource_obj

                    elif tf_resource_type == 'azurerm_storage_account' and attrName in ['retention_policy_days']:
                        if "".format("{}",attrValue) == "0" or (isinstance(attrValue, int) and attrValue ==0):
                            final_dict[attrName] = 1
                    else:
                        final_dict[attrName] = attrValue
                    #print("empty??",  attrName, attrValue )
            except Exception as e:
                print("ERROR:Step2:","remove_empty", e)
        return final_dict