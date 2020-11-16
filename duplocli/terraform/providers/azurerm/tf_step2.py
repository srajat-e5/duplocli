from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep
import random
from datetime import datetime


class AzurermTfImportStep2(AzureBaseTfImportStep):
    is_allow_none = True
    state_dict = {}

    def __init__(self, params):
        super(AzurermTfImportStep2, self).__init__(params)
        random.seed(datetime.now())

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
        resources = self.state_dict['resources']
        for resource in resources:
            try:
                self._tf_resource(resource)
            except Exception as e:
                print("ERROR:Step2:", "_tf_resources", e, resource)
        return self.main_tf_json_dict

    #############
    def _tf_resource(self, resource):
        nested_count = 1
        tf_resource_type = resource["type"]
        tf_resource_var_name = resource["name"]
        print(self.file_utils.stage_prefix(), nested_count, tf_resource_type, tf_resource_var_name, "=",
              tf_resource_var_name)
        attributes = resource['instances'][0]['attributes']
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
        for attribute_name, attribute in attributes.items():
            try:
                is_nested = attribute_name in schema.nested
                is_computed = attribute_name in schema.computed
                is_optional = attribute_name in schema.optional
                if is_nested:
                    self._process_nested(nested_count, tf_resource_type, tf_resource_var_name, attribute_name,
                                         attribute, resource_obj, schema)
                elif isinstance(attribute, dict):
                    resource_obj_dict = {}
                    resource_obj[attribute_name] = resource_obj_dict
                    self._process_dict(nested_count, tf_resource_type, tf_resource_var_name, resource_obj_dict,
                                       attribute_name, attribute, None)
                elif isinstance(attribute, list):
                    # TO_FIX_BUGS: skip list based on object  type
                    if self._skip_root_attr_list(tf_resource_type, tf_resource_var_name, attribute_name, attribute):
                        pass
                    else:
                        resource_obj_dict = []
                        for nested_item in attribute:
                            if isinstance(nested_item, dict):
                                resource_obj_list = {}
                                resource_obj_dict.append(resource_obj_list)
                                self._process_dict(nested_count, tf_resource_type, tf_resource_var_name,
                                                   resource_obj_list, attribute_name, nested_item, None)
                            else:
                                resource_obj_dict.append(nested_item)
                        if len(resource_obj_dict) > 0:
                            resource_obj[attribute_name] = resource_obj_dict
                elif is_optional or not is_computed:
                    #TO_FIX_BUGS: skip based on object type
                    if self._skip_root_attr_optional(tf_resource_type, tf_resource_var_name, attribute_name, attribute):
                        pass
                    elif isinstance(attribute, bool):
                        resource_obj[attribute_name] = attribute
                    elif attribute == 0:
                        pass
                    elif attribute is not None and attribute != "":
                        resource_obj[attribute_name] = attribute
                else:
                    pass
            except Exception as e:
                print("ERROR:Step2:", "_tf_resource", e)

        #TO_FIX_BUGS: remove empoty array,strings
        resource_obj2 = resource_obj #original vals
        resource_obj = self.remove_empty(tf_resource_type, tf_resource_var_name, resource_obj)

        #TO_FIX_BUGS: update root elements
        self._skip_root_update_attrs_resource(tf_resource_type, resource_obj, resource_obj2)
        tf_resource_type_root[tf_resource_var_name] = resource_obj

    #############
    def _process_dict(self, nested_count_parent, tf_resource_type, tf_resource_var_name, resource_obj,
                      nested_atr_name, nested_atr, schema):
        nested_count = nested_count_parent + 1
        for attribute_name, attribute in nested_atr.items():
            try:
                if self._processIfNested(nested_count, tf_resource_type, tf_resource_var_name, attribute_name,
                                         attribute, resource_obj, schema):
                    return
                if schema is None or not attribute_name in schema.computed:
                    if isinstance(attribute, bool):
                        resource_obj[attribute_name] = attribute
                    elif tf_resource_type == "azurerm_container_group" and nested_atr_name == 'container' \
                            and attribute_name in ["volume"]:
                        pass  # skip
                    elif attribute == 0:
                        pass
                    elif attribute is not None and attribute != "":  # attribute is not None or self.is_allow_none:
                        resource_obj[attribute_name] = attribute
                    else:
                        pass
            except Exception as e:
                print("ERROR:Step2:", "_process_dict", e)
        # TO_FIX_BUGS: skip based on object type
        self._skip_process_dict(nested_count_parent, tf_resource_type, tf_resource_var_name, resource_obj,
                                nested_atr_name, nested_atr, schema)

    def remove_empty(self, tf_resource_type, tf_resource_var_name, json_dict):
        if tf_resource_type not in ['Aazurerm_virtual_machine',  'azurerm_monitor_metric_alert']:
            return json_dict
        final_dict = {}
        for attrName, attrValue in json_dict.items():
            try:
                if isinstance(attrValue, bool):
                    final_dict[attrName] = attrValue
                else:
                    # TO_FIX_BUGS: skip based on object type
                    if self._skip_attr_remove_empty(tf_resource_type, tf_resource_var_name, json_dict, final_dict,
                                                    attrName, attrValue):
                        pass
                    elif isinstance(attrValue, dict):
                        final_dict[attrName] = self.remove_empty(tf_resource_type, tf_resource_var_name, attrValue)
                    elif isinstance(attrValue, list):
                        if len(attrValue) > 0:
                            resource_obj = []
                            for nested_item in attrValue:
                                if isinstance(nested_item, dict):
                                    nested_item_value = self.remove_empty(tf_resource_type, tf_resource_var_name,
                                                                          nested_item)
                                    if nested_item_value and len(nested_item_value) > 0:
                                        resource_obj.append(nested_item_value)
                                else:
                                    if tf_resource_type == 'azurerm_route_table' and attrName == 'route':
                                        pass
                                    else:
                                        resource_obj.append(nested_item)
                            if len(resource_obj) > 0:
                                final_dict[attrName] = resource_obj
                    else:
                        final_dict[attrName] = attrValue
                    # print("empty??",  attrName, attrValue )
            except Exception as e:
                print("ERROR:Step2:", "remove_empty", e)
        return final_dict

    def _process_nested(self, nested_count_parent, tf_resource_type, tf_resource_var_name, nested_atr_name,
                        nested_atr, resource_obj_parent, schema_nested):
        try:

            # TO_FIX_BUGS: skip based on object type
            if self._skip_process_nested(nested_count_parent, tf_resource_type, tf_resource_var_name,
                                         nested_atr_name,
                                         nested_atr, resource_obj_parent, schema_nested):
                return

            nested_count = nested_count_parent + 1
            schema = schema_nested.nested_block[nested_atr_name]
            if isinstance(nested_atr, dict):
                if nested_atr_name in schema.computed:
                    pass
                else:
                    resource_obj = {}
                    resource_obj_parent[nested_atr_name] = resource_obj
                    self._process_dict(nested_count, tf_resource_type, tf_resource_var_name, resource_obj,
                                       nested_atr_name, nested_atr, schema)
            elif isinstance(nested_atr, list):  # aa
                if nested_atr_name in schema.computed:
                    pass
                else:
                    resource_obj = []
                    # resource_obj_parent[nested_atr_name] = resource_obj
                    for nested_item in nested_atr:
                        if isinstance(nested_item, dict):
                            resource_obj_list = {}
                            self._process_dict(nested_count, tf_resource_type, tf_resource_var_name,
                                               resource_obj_list,
                                               nested_atr_name, nested_item, schema)
                            resource_obj.append(resource_obj_list)
                        else:
                            resource_obj.append(nested_item)
                    if len(resource_obj) > 0:
                        resource_obj_parent[nested_atr_name] = resource_obj
            else:
                pass
        except Exception as e:
            print("ERROR:Step2:", "_process_nested", e)

    #############

    def _skip_root_attr_list(self, tf_resource_type, tf_resource_var_name, attribute_name, attribute):
        if tf_resource_type == 'azurerm_route_table' and attribute_name == 'subnets':
            return True
        elif tf_resource_type == 'azurerm_network_interface' and attribute_name in ['private_ip_address',
                                                                                    'private_ip_addresses']:
            return True
        return False

    def _skip_root_attr_optional(self, tf_resource_type, tf_resource_var_name, attribute_name, attribute):
        if attribute_name == "id":
            return True
        elif tf_resource_type == 'azurerm_network_interface' and attribute_name in ['private_ip_address',
                                                                                    'private_ip_addresses']:
            return True
        return False

    def _skip_root_update_attrs_resource(self, tf_resource_type, resource_obj, resource_obj2):
        try:
            if tf_resource_type == 'azurerm_app_service':
                if "auth_settings" in resource_obj:
                    auth_settings = resource_obj["auth_settings"]
                    for auth_setting in auth_settings:
                        if "token_refresh_extension_hours" not in auth_setting:
                            auth_setting["token_refresh_extension_hours"] = 0

            if tf_resource_type in ["azurerm_mysql_server", "azurerm_postgresql_server"]:
                self._del_key(resource_obj, "storage_profile")
                self._del_key(resource_obj, "ssl_enforcement")

            if tf_resource_type in ['azurerm_route_table'] and "subnets" in resource_obj:
                self._del_key(resource_obj, "subnets")

            if tf_resource_type in ['azurerm_monitor_metric_alert'] and (
                    not "name" in resource_obj or resource_obj["name"] == ""):
                resource_obj["name"] = resource_obj["resource_group_name"]

            if tf_resource_type in ['azurerm_storage_account']:
                self._del_key(resource_obj, "queue_properties")
                if "network_rules" in resource_obj:
                    network_rules = resource_obj["network_rules"]
                    for network_rule in network_rules:
                        if "bypass" not in network_rule:
                            network_rule["bypass"] = ["AzureServices"]
                        elif len(network_rule["bypass"]) == 0:
                            network_rule["bypass"] = ["AzureServices"]

            if tf_resource_type in ['azurerm_container_group']:
                if not "ip_address_type" in resource_obj or resource_obj["ip_address_type"] is None:
                    resource_obj["ip_address_type"] = "Public"
                containers = resource_obj["container"]
                for container in containers:
                    if not "ports" in container:
                        container["ports"] = {
                            "port": 80,  # 443
                            "protocol": "TCP"
                        }
        except Exception as e:
            print("ERROR:Step2:", "_tf_resource", e)
        return resource_obj

    ########
    def _skip_process_nested(self, nested_count_parent, tf_resource_type, tf_resource_var_name, nested_atr_name,
                             nested_atr, resource_obj_parent, schema_nested):
        if tf_resource_type == "azurerm_app_service":
            # need values non empty as thery are optional + computed?
            if nested_atr_name == 'site_config':
                resource_obj_arr = []
                for attribute_item in nested_atr:
                    resource_obj = {}
                    resource_obj_arr.append(resource_obj)
                    for attribute_name, attribute in attribute_item.items():
                        try:
                            if attribute_name in ["app_command_line", "default_documents",
                                                  "auto_swap_slot_name", "health_check_path",
                                                  "windows_fx_version"]:
                                resource_obj[attribute_name] = attribute
                            elif isinstance(attribute, str):
                                if (attribute != "" and attribute is not None):
                                    resource_obj[attribute_name] = attribute
                            else:
                                resource_obj[attribute_name] = attribute
                        except Exception as e:
                            print("ERROR:Step2:", "site_config", e)
                resource_obj_parent[nested_atr_name] = resource_obj_arr
                return True

        elif tf_resource_type == "azurerm_virtual_machine":
            if nested_atr_name in ['storage_image_reference', "os_profile", "storage_os_disk"]:
                resource_obj_arr = []
                for attribute_item in nested_atr:
                    resource_obj = {}
                    resource_obj_arr.append(resource_obj)
                    for attribute_name, attribute in attribute_item.items():
                        try:
                            if isinstance(attribute, str):
                                if (attribute != "" and attribute is not None):
                                    resource_obj[attribute_name] = attribute
                            else:
                                resource_obj[attribute_name] = attribute
                        except Exception as e:
                            print("ERROR:Step2:", nested_atr_name, e)
                if resource_obj_arr is not None:
                    resource_obj_parent[nested_atr_name] = resource_obj_arr
                else:
                    print("WARN:Step2:VALUE empty", nested_atr_name)
                return True
        return False

    def _skip_process_dict(self, nested_count_parent, tf_resource_type, tf_resource_var_name, resource_obj,
                           nested_atr_name, nested_atr, schema):
        if tf_resource_type == 'azurerm_application_gateway' and nested_atr_name == 'backend_address_pool':
            if 'fqdns' in resource_obj and len(resource_obj['fqdns']) == 0:
                del resource_obj['fqdns']
        if tf_resource_type == 'azurerm_route_table' and nested_atr_name == 'route':
            self._set_val(resource_obj, "next_hop_in_ip_address", "")
        elif tf_resource_type == 'azurerm_network_security_group' and nested_atr_name == 'security_rule':
            self._set_val(resource_obj, "description", "")
            self._set_val(resource_obj, "source_application_security_group_ids", "")
            # destination_address
            self._set_val(resource_obj, "destination_address_prefix", [])
            self._set_val(resource_obj, "destination_address_prefixes", [])
            self._set_val(resource_obj, "destination_port_ranges", [])
            # source_address
            self._set_val(resource_obj, "source_address_prefix", "")
            self._set_val(resource_obj, "source_address_prefixes", [])
            self._set_val(resource_obj, "source_port_ranges", [])
        if tf_resource_type == 'azurerm_virtual_machine' and nested_atr_name == 'boot_diagnostics':
            self._set_val(resource_obj, "enabled", False)
            self._set_val(resource_obj, "storage_uri", "")

    def _skip_attr_remove_empty(self, tf_resource_type, tf_resource_var_name, json_dict, final_dict, attrName,
                                attrValue):
        if tf_resource_type == 'azurerm_network_security_group' and attrName == 'security_rule':
            return True
        elif tf_resource_type == 'azurerm_route_table' and attrName in ['route']:
            return True
        elif tf_resource_type == 'azurerm_monitor_metric_alert' and attrName in ['name', 'scopes']:
            return True
        elif tf_resource_type == 'azurerm_app_service' and attrName in ['site_credential',
                                                                        'source_control']:
            self._del_key(final_dict, attrName)
            return True
        elif tf_resource_type == 'azurerm_app_service_certificate' and attrName in ['host_names']:
            self._del_key(final_dict, attrName)
            return True
        elif tf_resource_type == 'azurerm_storage_account' and attrName in ['retention_policy_days']:
            if "".format("{}", attrValue) == "0" or (isinstance(attrValue, int) and attrValue == 0):
                final_dict[attrName] = 1
            return True
        return False

    ############

    def _set_val(self, resource_obj, attribute_name, attribute):
        if attribute_name not in resource_obj.keys():
            resource_obj[attribute_name] = attribute

    def _del_key(self, final_dict, attrName):
        try:
            del final_dict[attrName]
        except KeyError as ex:
            pass

    #############
    def _processIfNested(self, nested_count_parent, tf_resource_type, tf_resource_var_name, resource_obj,
                         attribute_name, attribute, schema):
        if schema is not None:
            is_nested = attribute_name in schema.nested
            if is_nested:
                self._process_nested(nested_count_parent, tf_resource_type, tf_resource_var_name, attribute_name,
                                     attribute,
                                     resource_obj, schema)
                return True
        return False



