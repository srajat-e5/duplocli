from duplocli.terraform.providers.aws.base_tf_step import AwsBaseTfImportStep


class AwsTfImportStep2(AwsBaseTfImportStep):
    is_allow_none = True
    state_dict = {}

    def __init__(self, params):
        super(AwsTfImportStep2, self).__init__(params)

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
        resources = self.state_dict['resources']
        for resource in resources:
            self._tf_resource(resource)
        return self.main_tf_json_dict

    #############
    def _tf_resource(self, resource):
        nested_count = 1
        tf_resource_type = resource["type"]
        tf_resource_var_name = resource["name"]
        print(self.file_utils.stage_prefix(), nested_count, tf_resource_type, "=", tf_resource_var_name)
        attributes = resource['instances'][0]['attributes']
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        tf_resource_type_root[tf_resource_var_name] = resource_obj
        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
        for attribute_name, attribute in attributes.items():
            is_nested = attribute_name in schema.nested
            is_computed = attribute_name in schema.computed
            is_optional = attribute_name in schema.optional
            if is_nested:
                self._process_nested(nested_count, tf_resource_type, tf_resource_var_name, attribute_name, attribute,
                                     resource_obj, schema)
            elif isinstance(attribute, dict):
                resource_obj_dict = {}
                resource_obj[attribute_name] = resource_obj_dict
                self._process_dict(nested_count, tf_resource_type, tf_resource_var_name, resource_obj_dict,
                                   attribute_name, attribute, None)
            elif isinstance(attribute, list):
                resource_obj_dict = []
                resource_obj[attribute_name] = resource_obj_dict
                for nested_item in attribute:
                    if isinstance(nested_item, dict):
                        resource_obj_list = {}
                        resource_obj_dict.append(resource_obj_list)
                        self._process_dict(nested_count, tf_resource_type, tf_resource_var_name, resource_obj_list,
                                           attribute_name, nested_item, None)
                    else:
                        resource_obj_dict.append(nested_item)
            elif is_optional or not is_computed:
                if attribute_name in ["user_data", "replicas", "availability_zone_id", "arn"]:
                    resource_obj["lifecycle"] = {"ignore_changes": [attribute_name]}
                elif tf_resource_type == "aws_elasticache_cluster" and attribute_name in ["replication_group_id",
                                                                                          "cache_nodes"]:
                    resource_obj["lifecycle"] = {"ignore_changes": ["replication_group_id", "cache_nodes"]}
                elif tf_resource_type == "aws_s3_bucket" and attribute_name in ["acl", "force_destroy",
                                                                                "acceleration_status"]:
                    resource_obj["lifecycle"] = {"ignore_changes": ["acl", "force_destroy", "acceleration_status"]}
                elif tf_resource_type == "aws_iam_instance_profile" and attribute_name in ["roles", "role"]:
                    resource_obj["lifecycle"] = {"ignore_changes": ["roles"]}
                elif tf_resource_type == "aws_instance" and attribute_name in ["cpu_core_count",
                                                                               "cpu_threads_per_core"]:
                    pass
                elif attribute_name == "id":
                    pass
                elif attribute is not None or self.is_allow_none:  # or  (isinstance(object, list) and len(list) > 0)
                    resource_obj[attribute_name] = attribute
            else:
                pass

    def _process_dict(self, nested_count_parent, tf_resource_type, tf_resource_var_name, resource_obj, nested_atr_name,
                      nested_atr, schema):
        nested_count = nested_count_parent + 1
        for attribute_name, attribute in nested_atr.items():
            if self.processIfNested(nested_count, tf_resource_type, tf_resource_var_name, attribute_name, attribute,
                                    resource_obj, schema):
                pass
            if schema is None or not attribute_name in schema.computed:
                if nested_atr_name in ["ingress", "egress"] and attribute_name == "description":
                    resource_obj[attribute_name] = attribute or ""
                elif attribute_name in ["arn"]:
                    pass  # skip
                elif attribute_name == "ipv6_cidr_block":
                    resource_obj[attribute_name] = None
                elif attribute_name == "user_data":
                    resource_obj[attribute_name] = attribute
                elif attribute is not None or self.is_allow_none:
                    resource_obj[attribute_name] = attribute
                else:
                    pass

    def _process_nested(self, nested_count_parent, tf_resource_type, tf_resource_var_name, nested_atr_name, nested_atr,
                        resource_obj_parent, schema_nested):
        nested_count = nested_count_parent + 1
        schema = schema_nested.nested_block[nested_atr_name]
        if isinstance(nested_atr, dict):
            resource_obj = {}
            resource_obj_parent[nested_atr_name] = resource_obj
            self._process_dict(nested_count, tf_resource_type, tf_resource_var_name, resource_obj, nested_atr_name,
                               nested_atr, schema)
        elif isinstance(nested_atr, list):
            resource_obj = []
            resource_obj_parent[nested_atr_name] = resource_obj
            for nested_item in nested_atr:
                if isinstance(nested_item, dict):
                    resource_obj_list = {}
                    resource_obj.append(resource_obj_list)
                    self._process_dict(nested_count, tf_resource_type, tf_resource_var_name, resource_obj_list,
                                       nested_atr_name, nested_item, schema)
                elif isinstance(nested_item, list):
                    print(self.file_utils.stage_prefix(), "_process_nested  is list list nested list ???? ",
                          nested_count, tf_resource_type, tf_resource_var_name, nested_atr_name)
                    pass
                else:
                    resource_obj.append(nested_item)

    def processIfNested(self, nested_count_parent, tf_resource_type, tf_resource_var_name, resource_obj, attribute_name,
                        attribute, schema):
        if schema is not None:
            is_nested = attribute_name in schema.nested
            if is_nested:
                self._process_nested(nested_count_parent, tf_resource_type, tf_resource_var_name, attribute_name,
                                     attribute,
                                     resource_obj, schema)
                return True
        return False
