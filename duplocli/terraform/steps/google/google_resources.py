import boto3
import json
import datetime
from collections import defaultdict
from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils
from duplocli.terraform.resources.base_resources import BaseResources

class GoogleResources(BaseResources):
    debug_print_out = False
    debug_json = True
    create_key_pair = False
    #
    vpc_list = {}

    def __init__(self, params):
        super(GoogleResources, self).__init__(params)
        self.tenant_prefix = self.utils.get_tenant_id(params.tenant_name )

    def get_tenant_resources(self):
        return  self.tf_cloud_obj_list

    def get_infra_resources(self):
        return self.tf_cloud_obj_list

