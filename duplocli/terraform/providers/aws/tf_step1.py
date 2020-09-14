from duplocli.terraform.providers.aws.base_tf_step import AwsBaseTfImportStep
import requests

# aws_resources
# [
# {
#     "tf_import_id": "duploservices-bigdata01",
#     "tf_resource_type": "aws_iam_role",
#     "tf_variable_id": "AROARKHYLTX2Z5RQWNRSM"
# },
# ]
dummy_values = {
    "cidr_block":"0.0.0.0/0",
    "ipv6_cidr_block":"0.0.0.0/0"
}

class AwsTfImportStep1(AwsBaseTfImportStep):

    def __init__(self,  params):
       super(AwsTfImportStep1, self).__init__(params)

    ############ execute_step public resources ##########
    def execute(self,  aws_obj_list=[]):
        self.file_utils.save_to_json(self.file_utils.tf_resources_file(), aws_obj_list)
        self.file_utils.save_to_json(self.file_utils.tf_resources_file_for_step("step2"), aws_obj_list)
        self._tf_resources(aws_obj_list)
        self._create_tf_state()
        return self.file_utils.tf_main_file()

    ############ main.tf.json + script + generate state ##########
    def _create_tf_state(self):
        super()._create_tf_state()
        self.file_utils.create_state(self.file_utils.tf_run_script())
        self.rm_aws_security_group_rule_tf_bug()

    ############ aws tf resources ##########
    def _tf_resources(self, aws_obj_list):
        for aws_obj in aws_obj_list:
            self._tf_resource(aws_obj)

    def _tf_resource(self, aws_obj):
        tf_resource_type=aws_obj['tf_resource_type']
        resource_obj = self._init_tf_resource(aws_obj)
        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
        for required_name in schema.required:
            if required_name in dummy_values:
                resource_obj[required_name] = dummy_values[required_name]
            else:
                # keep an eye --- we are neglecting data types ! until we get error ?
                resource_obj[required_name] = "xxxx"
        return resource_obj

    def _init_tf_resource(self, aws_obj):
        tf_resource_type = aws_obj['tf_resource_type']
        tf_resource_var_name= aws_obj['tf_variable_id']
        tf_resource_type_sync_id = aws_obj['tf_import_id']
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        tf_resource_type_root[tf_resource_var_name] = resource_obj
        self.tf_import_sh_list.append(
            'terraform import "' + tf_resource_type + '.' + tf_resource_var_name + '"  "' + tf_resource_type_sync_id + '"')
        return resource_obj




