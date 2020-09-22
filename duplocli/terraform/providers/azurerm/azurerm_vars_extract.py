from duplocli.terraform.providers.azurerm.base_tf_step import AzureBaseTfImportStep

class AzurermTfVarsExtract(AzureBaseTfImportStep):

    is_allow_none = True
    state_dict = {}

    def __init__(self, params):
        super(AzurermTfVarsExtract, self).__init__(params)


    def execute(self):
        self._tf_resources()
        self._create_tf_state()
        return self.file_utils.tf_main_file()
    
    ##### manage files and state ##############
    def _create_tf_state(self):
        self.file_utils.save_state_file(self.state_dict)
        super()._create_tf_state()

    #############
    def _load_state_into_dict(self):
        ## state
        self.state_read_from_file = self.file_utils.tf_state_file_srep2()
        self.state_dict = self.file_utils.load_json_file(self.state_read_from_file)
        if "resources" in self.state_dict:
            resources = self.state_dict['resources']
        else:
            resources = self.state_dict['resource']
        return resources

    def _load_main_json(self):
        self.src_main_tf_json_file = self.file_utils.tf_main_file_srep2()
        self.src_main_tf_json_dict = self.file_utils.load_json_file(self.src_main_tf_json_file)
        self.src_resources_dict = self.src_main_tf_json_dict["resource"]

    ######  TfImportStep3 ################################################
    def _tf_resources(self):

        ### duplo resources
        self.tf_resources_file = self.file_utils.load_json_file(self.file_utils.tf_resources_file())
        ## state
        self.state_resources = self._load_state_into_dict()
        self._load_main_json()

        self.value_count = {}
        self.value_keys = {}
        self.value_details = {}
        self.value_computed = {}

        self.vars_tf = {}
        self.vars_state_tf = {}

        ###
        for resource_type in self.src_resources_dict:
            try:
                self.vars_tf[resource_type] =  self._tf_resource_type(resource_type, self.src_resources_dict[resource_type])
            except Exception as e:
                print("ERROR:Step2:","_tf_resources", e)

        ###
        self._tf_resource_state_type()

        ###
        for resource in self.state_resources:
            try:
                self._tf_resource(resource)
            except Exception as e:
                print("ERROR:Step2:","_tf_resources", e)

        print(self.value_count)
        d = self.value_count
        sort_orders = sorted(d.items(), key=lambda x: x[1], reverse=True)
        print(sort_orders)
        print(self.value_keys)
        print(self.value_computed)

        print(self.vars_tf)
        print(self.vars_state_tf)
        return self.main_tf_json_dict

    ######  TfImportStep3 ################################################
    def _tf_resource_type(self, resource_type, array_resources):
        obj_resources_arr_vars=[]
        for resource_name in  array_resources:
            try:
                obj_resources_tf = array_resources[resource_name]
                obj_resources_tf['duplo_tf_name'] =resource_name
                obj_resources_arr_vars.append(obj_resources_tf)
            except Exception as e:
                print("ERROR:Step2:","_tf_resource_type", e)
        return obj_resources_arr_vars


    def _tf_resource_state_type(self):
        obj_resources_arr_vars = []
        for resource in self.state_resources:
            try:
                tf_resource_type = resource["type"]
                tf_resource_var_name = resource["name"]
                attributes = resource['instances'][0]['attributes']
                attributes["type"] = tf_resource_type
                attributes["name"] = tf_resource_var_name
                if not tf_resource_type in self.vars_state_tf:
                    self.vars_state_tf[tf_resource_type] = []
                self.vars_state_tf[tf_resource_type].append(attributes)
            except Exception as e:
                print("ERROR:Step2:", "_tf_resource_state_type", e)
    ######  TfImportStep3 ################################################

    def set_value_cout(self, nested_count, is_computed,  parents, tf_resource_type, tf_resource_var_name, attribute, attribute_name):
        parents_str = ".".join(parents)
        if attribute is not None and attribute != "":
            if attribute in self.value_count:
                self.value_count[attribute] = self.value_count[attribute] + 1
            else:
                self.value_count[attribute] = 1
            if attribute in self.value_keys:
                self.value_keys[attribute].add(parents_str)
            else:
                self.value_keys[attribute] = {parents_str}

            if is_computed:
                if attribute in self.value_computed:
                    self.value_computed[attribute].add(parents_str)
                else:
                    self.value_computed[attribute] = {parents_str}

    ######  TfImportStep3 ################################################

    def _tf_resource(self, resource):
        nested_count = 1
        tf_resource_type = resource["type"]
        tf_resource_var_name = resource["name"]
        print(self.file_utils.stage_prefix(), nested_count, tf_resource_type,  tf_resource_var_name, "=", tf_resource_var_name)
        attributes = resource['instances'][0]['attributes']
        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)

        for attribute_name, attribute  in attributes.items():
            try:
                is_nested = attribute_name  in schema.nested
                is_computed = attribute_name  in schema.computed
                is_optional = attribute_name  in schema.optional
                parent_set = [tf_resource_type,  tf_resource_var_name, attribute_name]
                if is_nested:
                    self._process_nested(nested_count, parent_set, tf_resource_type,  tf_resource_var_name, attribute_name, attribute,  schema)
                elif isinstance(attribute, dict):
                    self._process_dict(nested_count, parent_set,  tf_resource_type,  tf_resource_var_name,  attribute_name, attribute, None)
                elif isinstance(attribute, list):
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._process_dict(nested_count, parent_set,  tf_resource_type,  tf_resource_var_name,   attribute_name, nested_item, None)
                        elif isinstance(nested_item, list):
                            print(self.file_utils.stage_prefix(), "_process_nested  is list list nested list ???? ", nested_count, tf_resource_type,  tf_resource_var_name, attribute_name)
                            #pass
                        else:
                            # self.set_value_cout(nested_count, is_computed, parent_set, tf_resource_type,
                            #                     tf_resource_var_name, nested_item, attribute_name)
                            # resource_obj_dict.append(nested_item)
                            pass
            except Exception as e:
                print("ERROR:Step2:","_tf_resource", e)



    def _process_dict(self, nested_count_parent, root_parent_set, tf_resource_type,  tf_resource_var_name,  nested_atr_name, nested_atr, schema):
        nested_count = nested_count_parent + 1
        for attribute_name, attribute in nested_atr.items():
            try:
                parent_set =  list(root_parent_set)
                parent_set.append(attribute_name)
                is_computed = schema is not None and attribute_name in schema.computed
                if self.processIfNested(nested_count, parent_set, tf_resource_type,  tf_resource_var_name, attribute_name, attribute,  schema):
                    return
                if isinstance(attribute, list):
                    for nested_item in attribute:
                        if isinstance(nested_item, dict):
                            self._process_dict(nested_count, parent_set, tf_resource_type, tf_resource_var_name,
                                                 nested_atr_name, nested_item, schema)
                        elif isinstance(nested_item, list):
                            print("WARN:", self.file_utils.stage_prefix(),
                                  " _process_nested  is list list nested list ???? ", nested_count, tf_resource_type,
                                  tf_resource_var_name, nested_atr_name)
                        else:
                            self.set_value_cout(nested_count, is_computed, parent_set, tf_resource_type,
                                                tf_resource_var_name, nested_item, nested_atr_name)
                else:
                    self.set_value_cout(nested_count, is_computed, parent_set, tf_resource_type, tf_resource_var_name, attribute, attribute_name)

            except Exception as e:
                print("ERROR:Step2:","_process_dict", e)



    def _process_nested(self, nested_count_parent, parent_set,  tf_resource_type,  tf_resource_var_name, nested_atr_name, nested_atr,   schema_nested):
        try:
            nested_count = nested_count_parent + 1
            schema = schema_nested.nested_block[nested_atr_name]
            if isinstance(nested_atr, dict):
                self._process_dict(nested_count, parent_set, tf_resource_type,  tf_resource_var_name,  nested_atr_name, nested_atr, schema)
            elif isinstance(nested_atr, list):
                for nested_item in nested_atr:
                    if isinstance(nested_item, dict):
                        self._process_dict(nested_count, parent_set, tf_resource_type,  tf_resource_var_name,  nested_atr_name,  nested_item,  schema)
                    elif isinstance(nested_item, list):
                        print("WARN:", self.file_utils.stage_prefix(), " _process_nested  is list list nested list ???? ", nested_count, tf_resource_type,  tf_resource_var_name,  nested_atr_name)
                    else:
                        is_computed = schema is not None and nested_atr_name in schema.computed
                        self.set_value_cout(nested_count, is_computed, parent_set, tf_resource_type, tf_resource_var_name, nested_item, nested_atr_name)
            else:
                pass
                # print("Warn: Nested non dict/list?")
        except Exception as e:
            print("ERROR:Step2:", "_process_nested", e)

    def processIfNested(self, nested_count_parent, parent_set, tf_resource_type,  tf_resource_var_name,  attribute_name, attribute, schema):
        if schema is not None:
            is_nested = attribute_name in schema.nested
            if is_nested:
                self._process_nested(nested_count_parent, parent_set, tf_resource_type, tf_resource_var_name, attribute_name, attribute,
                                     schema)
                return True
        return False


