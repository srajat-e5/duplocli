import json
import datetime
from collections import defaultdict

class TfUtils:

    def get_tf_output_path(self, step_name):
        output_path = "../output/{0}".format(step_name)
        return output_path

    def get_save_to_output_path(self, step_name, file_name):
        output_path = self.get_tf_output_path(step_name)
        output_file_path = "{0}/{1}".format(output_path, file_name)
        return output_file_path
    #######
    def get_tenant_id(self, tenant_name):
        tenant_name_prafix="duploservices"
        tenant_id= "{0}-{1}".format(tenant_name_prafix,tenant_name)
        return tenant_id

    ###
    def is_native_type(self, object):
        try:
            # json.dumps(object)
            type_b = isinstance(object, (list, tuple, set, dict))
            print(type_b  )
            return not type_b
        except TypeError:
            print ("Can't convert", object)
            return True

    ####### json
    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    ####### defaultdict
    def def_value(self):
        return ""

    ####### rea from dict json
    def getValCild(self, inst, key, keych9ild):
        try:
            return inst[key][keych9ild]
        except:
            return ""

    def getValJson(self, inst, key):
        try:
            return json.dumps(inst[key], sort_keys=True,
                  indent=1,
                  default=self.default)
        except:
            return ""
    def getVal(self, inst, key):
        try:
            return inst[key]
        except:
            return ""

    def getValChild(self, inst, key, keychild):
        try:
            return inst[key][keychild]
        except:
            return ""
    def getHashFromArray(self, insts):
        vals = defaultdict(self.def_value)
        try:
            for inst in insts:
                key = inst["Key"]
                val = inst["Value"]
                vals[key]=val
        except:
            return vals
        return vals

    def getValChildArray(self, inst, key, keychild):
        try:
            for instance in inst[key]:
                val = self.getVal(instance, keychild)
                if val != "":
                    return val
        except:
            return ""

    #######
    def load_json_file(self, file):
        with open(file) as f:
            data = json.load(f)
        return data


    def print_json(self, response, sort_keys=True):
        resp_json = json.dumps(response,
                               sort_keys=sort_keys,
                               indent=3,
                               default=self.default)
        print(resp_json)

    def save_run_script(self, file_name, data_dict, mode="w"):
        f = open(file_name, mode)
        f.write('\n')
        for line in data_dict:
            f.write(line + '\n')
        f.write('\n')
        f.close()

    def save_json_to_log(self, file_name, data_dict, step="step1"):
        file_path= "../log/{0}_{1}".format(step,file_name )
        self.save_to_json(file_path, data_dict)

    def save_to_json(self, file_name, data_dict):
        resp_json = json.dumps(data_dict,
                               indent=2,
                               default=self.default)
        f = open(file_name, "w")
        f.write(resp_json)
        f.close()

    #######

    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    def def_value(self):
        return ""

    def to_json_str(self, response):
        resp_json = json.dumps(response, default=self.default)
        return resp_json.replace('"', '\\"')
