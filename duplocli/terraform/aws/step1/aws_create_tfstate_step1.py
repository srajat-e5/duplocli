
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.schema.aws_tf_schema import AwsTfSchema
import os
import requests

class AwsCreateTfstateStep1 :
    #output folder  output/step1
    step = "step1"

    # aws_tf_schema
    aws_tf_schema_file = "data/aws_tf_schema.json"
    aws_tf_schema = {}

    # mapping_aws_to_tf_state
    mapping_aws_keys_to_tf_keys_file = "data/mapping_aws_keys_to_tf_keys.json"
    mapping_aws_keys_to_tf_keys = []

    # main.tf.json
    main_tf_json_file_name = "main.tf.json"
    main_tf_json_dict = {"resource":{}}
    resources_dict = main_tf_json_dict["resource"]

    #tf_import_script.sh
    tf_import_script_file_name = "tf_import_script.sh"
    tf_import_sh_list = []

    # tf_import_script.sh
    tf_run_script_file_name = "run.sh"

    def __init__(self, aws_az):
        self.aws_az = aws_az;
        self.utils = TfUtils()
        ## script files
        self.tf_output_path = self.utils.get_tf_output_path(self.step)
        self.tf_json_file = self.utils.get_save_to_output_path(self.step, self.main_tf_json_file_name)
        self.tf_import_script_file = self.utils.get_save_to_output_path(self.step, self.tf_import_script_file_name)
        self.tf_run_script_file = self.utils.get_save_to_output_path(self.step, self.tf_run_script_file_name)
        #
        self._load_schema()

    def execute_step(self,  aws_obj_list=[]):
        self._aws_provider()
        self._empty_output()
        self._aws_resources(aws_obj_list)
        self._create_state()
        return self.tf_json_file

    def download_key(self,  aws_obj_list=[], duplo_api_json_file=None):
        if duplo_api_json_file is None:
            raise  Exception("duplo_api_json file is required")
        self.utils.create_output_folder("keys")
        for aws_key_pair_instance in  aws_obj_list:
            #aws_obj = {"name":name, "key_name":key_name, "instanceId":instanceId}
            key_name = aws_key_pair_instance['key_name']
            instanceId = aws_key_pair_instance['instanceId']
            # self.utils.print_json(aws_key_pair_instance)
            duplo_api_json = self.utils.load_json_file(duplo_api_json_file)
            endpoint = "{0}/subscriptions/{1}/getKeyPair/{2}".format(duplo_api_json['url']
                                                                , duplo_api_json['tenant_id']
                                                                , instanceId)
            headers = {"Authorization": "Bearer {0}".format(duplo_api_json['api_token'] )}
            response = requests.get(endpoint,   headers=headers)
            output_keys_folder = self.utils.get_tf_output_path("keys")
            output_key_file_path = "{0}/{1}".format(output_keys_folder, key_name)
            self.utils.save_key_file(output_key_file_path, response.content )
            print("**** aws import step1 : save_key_file ", output_key_file_path, instanceId)
        return self.tf_json_file

    ############ aws tf resources ##########

    def _aws_resources(self, aws_obj_list):
        for aws_obj in aws_obj_list:
            self._aws_resource(aws_obj)

    def _aws_resource(self, aws_obj):
        #[
        # {
        #     "tf_import_id": "duploservices-bigdata01",
        #     "tf_resource_type": "aws_iam_role",
        #     "tf_variable_id": "AROARKHYLTX2Z5RQWNRSM"
        # },
        #]
        tf_resource_type=aws_obj['tf_resource_type']
        resource_obj = self._init_aws_resource(aws_obj)
        #hack: insert required fields: we are adding dummy data
        schema = self.aws_tf_schema.get_tf_resource(tf_resource_type)
        for required_name in schema.required:
            # keep an eye --- we are neglecting datas type !
            resource_obj[required_name] = "aa"
        return resource_obj

    def _init_aws_resource(self, aws_obj):

        tf_resource_type = aws_obj['tf_resource_type']
        tf_resource_var_name= aws_obj['tf_variable_id']
        tf_resource_type_sync_id = aws_obj['tf_import_id']

        ### create entry main.tf.json: resource "TF_RESOURCE_TYPE" "TF_RESOURCE_VAR_NAME"
        tf_resource_type_root = self._get_or_create_tf_resource_type_root(tf_resource_type)
        resource_obj = {}
        tf_resource_type_root[tf_resource_var_name] = resource_obj

        ### create entry run.sh: terraform import "TF_RESOURCE_TYPE.TF_RESOURCE_VAR_NAME" "tf_resource_type_sync_id"
        self.tf_import_sh_list.append(
            'terraform import "' + tf_resource_type + '.' + tf_resource_var_name + '"  "' + tf_resource_type_sync_id + '"')
        ### return:  resource_obj
        return resource_obj

    def _get_or_create_tf_resource_type_root(self, tf_resource_type):
        #get parent for this resource
        if tf_resource_type not in self.resources_dict:
            self.resources_dict[tf_resource_type] = {}
        return self.resources_dict[tf_resource_type]

    def _load_schema(self):
        self.aws_tf_schema = AwsTfSchema(self.aws_tf_schema_file)
        #self.utils.load_json_file(self.aws_tf_schema_file)
    ############ aws_provider ##########
    def _aws_provider(self):
        tf_resource_type = "provider"
        tf_resource_var_name = "aws"
        resource_obj = self._base_provider(tf_resource_type, tf_resource_var_name)
        resource_obj["version"] = "~> 2.0"
        resource_obj["region"] = self.aws_az
        self.tf_import_sh_list.append('terraform init ')
        return resource_obj

    def _base_provider(self, tf_resource_type, tf_resource_var_name):
        resource_obj = {}
        resource_obj[tf_resource_var_name] = {}
        self.main_tf_json_dict[tf_resource_type] = resource_obj
        return resource_obj[tf_resource_var_name]


    ############ main.tf.json + script + generate state ##########

    def _empty_output(self):
        self.utils.empty_output_folder(self.step)

    def _create_state(self):
        self._plan()
        self._save_tf_files()
        self.utils.create_state(self.tf_run_script_file, self.step)

    def _save_tf_files(self):
        self.utils.save_to_json(self.tf_json_file, self.main_tf_json_dict)
        self.utils.save_run_script(self.tf_import_script_file, self.tf_import_sh_list)
        run_sh_list=[]
        run_sh_list.append("cd {0}".format(self.tf_output_path))
        run_sh_list.append("chmod 777 *.sh")
        run_sh_list.append("./{0}  ".format(self.tf_import_script_file_name))
        self.utils.save_run_script(self.tf_run_script_file, run_sh_list)
        # add plan to script

    def _plan(self):
        ### create: terraform plan ...
        # bug in tf -> creates extra aws_security_group_rule... remove aws_security_group_rule first.
        self.tf_import_sh_list.append(
            'terraform state list | grep aws_security_group_rule | xargs terraform state rm; terraform plan')

    ############ main.tf.json + script + generate state ##########
