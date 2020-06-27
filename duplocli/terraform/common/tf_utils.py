import json
import datetime
from collections import defaultdict
import os
import psutil

class TfUtils:

    def __init__(self, params):
        self.params = params

    #######
    def get_tenant_id(self, tenant_name):
        tenant_name_prafix="duploservices"
        tenant_id= "{0}-{1}".format(tenant_name_prafix,tenant_name)
        return tenant_id

    ####### rea from dict json
    def getVal(self, inst, key):
        try:
            return inst[key]
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

    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    def def_value(self):
        return ""



# def getValChildArray(self, inst, key, keychild):
    #     try:
    #         for instance in inst[key]:
    #             val = self.getVal(instance, keychild)
    #             if val != "":
    #                 return val
    #     except:
    #         return ""
    # def getValCild(self, inst, key, keych9ild):
    #     try:
    #         return inst[key][keych9ild]
    #     except:
    #         return ""
    #
    # def getValJson(self, inst, key):
    #     try:
    #         return json.dumps(inst[key], sort_keys=True,
    #               indent=1,
    #               default=self.default)
    #     except:
    #         return ""
    #
    # def getValChild(self, inst, key, keychild):
    #     try:
    #         return inst[key][keychild]
    #     except:
    #         return ""
