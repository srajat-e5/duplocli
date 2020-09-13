from duplocli.terraform.common.tf_utils import TfUtils
from duplocli.terraform.common.tf_file_utils import TfFileUtils
 

import os
class KubernetesTfSteps:
    only_step2 = False
    only_step1 = False
    def __init__(self, params):
        self.utils = TfUtils(params)
        self.file_utils = TfFileUtils(params)
        self.params = params

    ######### modules == tenant, infra or all customer objects ######
    def execute(self):
        return None
