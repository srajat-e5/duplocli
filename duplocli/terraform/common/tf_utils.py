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
        tenant_name_prafix = "duploservices"
        tenant_id = "{0}-{1}".format(tenant_name_prafix, tenant_name)
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
                vals[key] = val
        except:
            return vals
        return vals

    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    def def_value(self):
        return ""
