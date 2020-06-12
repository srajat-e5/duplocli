
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.schema.aws_tf_schema import AwsTfSchema
import os
import requests
import psutil
from duplocli.terraform.aws.common.tf_file_utils import TfFileUtils

class AwsCreateTfstateStep1 :

    step = "step1"
    aws_tf_schema = {}
    mapping_aws_keys_to_tf_keys = []
    main_tf_json_dict = {"resource":{}}
    resources_dict = main_tf_json_dict["resource"]
    tf_import_sh_list = []

    def __init__(self,  params):
        self.params = params
        self.aws_az = params.aws_region
        self.utils = TfUtils(params, step=self.step)
        #file_utils for steps
        self.file_utils = TfFileUtils(params, step=self.step)
        self._load_schema()

    ############ execute_step public api ##########
    def execute_step(self,  aws_obj_list=[]):
        self._aws_provider()
        self._empty_output()
        self._aws_resources(aws_obj_list)
        self._create_tf_state()
        return self.file_utils.tf_main_file()

    ############ download_key public api ##########
    def download_key(self,  aws_obj_list=[] ):
        # download_aws_keys = self.params.download_aws_keys
        url = self.params.url
        tenant_id = self.params.tenant_id
        api_token = self.params.api_token
        if  url is None or tenant_id is None  or api_token is None :
            raise  Exception("to download_keys  - url, tenant_id, api_token are required.")

        for aws_key_pair_instance in  aws_obj_list:
            #aws_obj = {"name":name, "key_name":key_name, "instanceId":instanceId}
            key_name = aws_key_pair_instance['key_name']
            instanceId = aws_key_pair_instance['instanceId']
            endpoint = "{0}/subscriptions/{1}/getKeyPair/{2}".format(url
                                                                , tenant_id
                                                                , instanceId)
            headers = {"Authorization": "Bearer {0}".format( api_token )}
            response = requests.get(endpoint,   headers=headers)
            self.file_utils.save_key_file(key_name, response.content )
            print("**** aws import step1 : save_key_file ", key_name, instanceId)
        return (self.file_utils.tf_main_file(), self.file_utils.tf_state_file(), self.file_utils.keys_folder())

    ############ aws tf resources ##########
    # aws_resources
    # [
    # {
    #     "tf_import_id": "duploservices-bigdata01",
    #     "tf_resource_type": "aws_iam_role",
    #     "tf_variable_id": "AROARKHYLTX2Z5RQWNRSM"
    # },
    # ]
    def _aws_resources(self, aws_obj_list):
        for aws_obj in aws_obj_list:
            self._aws_resource(aws_obj)

    def _aws_resource(self, aws_obj):
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
        #get parent for the resource
        if tf_resource_type not in self.resources_dict:
            self.resources_dict[tf_resource_type] = {}
        return self.resources_dict[tf_resource_type]

    def _load_schema(self):
        self.aws_tf_schema = AwsTfSchema(self.params, self.file_utils.aws_tf_schema_file())

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
        self.file_utils.empty_temp_folder()

    def _create_tf_state(self):
        # self._empty_output()
        ## save files
        self._plan()
        self.file_utils.save_main_file(self.main_tf_json_dict)
        self.file_utils.save_tf_import_script(self.tf_import_sh_list)
        self.file_utils.save_tf_run_script()
        ## execute script
        self.file_utils.create_state(self.file_utils.tf_run_script())
        self.rm_aws_security_group_rule_tf_bug()

    def _plan(self):
        ### create: terraform plan ...
        # bug in tf -> creates extra aws_security_group_rule... remove aws_security_group_rule first.
        # self.tf_import_sh_list.append(
        #     'terraform state list | grep aws_security_group_rule | xargs terraform state rm; terraform plan')

        self.tf_import_sh_list.append( "terraform plan")

    ############ main.tf.json + script + generate state ##########
    def rm_aws_security_group_rule_tf_bug(self):
        main_resources= self.main_tf_json_dict['resource']
        aws_security_group_rules=[]
        object_type_bug="aws_security_group_rule" # #aws_security_group
        if object_type_bug in main_resources:
            aws_security_group_rules = list(main_resources[object_type_bug].keys())

        state_dict = self.file_utils.load_json_file( self.file_utils.tf_state_file())
        if "resources" in  state_dict:
            resources = state_dict['resources']
        else:
            resources = state_dict['resource']

        resources_to_del = []
        for resource in resources: #list
            # print(resource)
            if object_type_bug == resource["type"]:
                name = resource["name"]
                if name not in aws_security_group_rules:
                    # resources.remove(resource)
                    resources_to_del.append(resource)
                else:
                   print("name skip ", name)
        for resource in resources_to_del:  # list
            resources.remove(resource)
        # save
        self.file_utils.save_state_file(state_dict)
        # print(state_dict)
