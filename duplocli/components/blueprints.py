import os
import sys
import datetime
import json
import click
import requests
from common import CheckEmptyParam
from common import CheckAndGetConnection
from common import getNameWithPrefix
from common import printSuccess
from common import processStatusCode
import common
from common import printSuccess
import shutil

@click.group()
@click.pass_context
def blueprints(ctx):
    pass

@blueprints.command('export-tenant')
@click.pass_obj
def blueprints_export_tenant(ctx):
    tenant, token, url, tenantId = CheckAndGetConnection()
    jsondata = { "IncludeAwsHosts" : "true" }
    export_tenant(token,url, tenantId, jsondata)

@blueprints.command('import-tenant')
@click.option('--svd', '-s', default='', help='SVD file JSON path')
@click.pass_obj
def blueprints_import_tenant(ctx, svd):
    tenant, token, url, tenantId = CheckAndGetConnection()
    import_tenant(token,url, tenantId, svd)

def export_tenant(token, url, tenantId, funcObject):
    newFuncUrl = url + "/subscriptions/" + tenantId + "/ExportTenant"
    headerVal = "Bearer " + token
    headers = { 'Authorization' : headerVal, 'content-type': 'application/json' }
    data = json.dumps(funcObject)
    r = requests.post(newFuncUrl, data=data, headers=headers)
    processStatusCode(r)
    data = json.loads(r.text)
    data = common.remove_empty_from_dict(data)
    formattedData = json.dumps(data, indent=4, sort_keys=True)
    print(formattedData)

def import_tenant(token, url, tenantId, svdFilePath):
    headerVal = "Bearer " + token
    headers = { 'Authorization' : headerVal }

    if not (svdFilePath and os.path.isfile(svdFilePath)):
        print("svd file path is empty or file specified is doesnt exists")
        return

    content = ""
    with open(svdFilePath, 'r') as content_file:
        content = content_file.read()

    if content:
        serviceDescription = json.loads(content)
        instanceIdByName = {}

        if serviceDescription and "NativeHosts" in serviceDescription and len(serviceDescription["NativeHosts"]):
            host_add_url = url + "/subscriptions/" + tenantId + "/CreateNativeHost"
            for service in serviceDescription["NativeHosts"]:
                post_response = requests.post(host_add_url, headers=headers, json = service)
                if post_response.status_code == 200:
                    instanceIdByName[service["FriendlyName"]] = post_response.json()
                print "EC2 Instance name - " +  service["FriendlyName"] + " , create requests server return code - " + str(post_response.status_code) + str(post_response.json())

        if serviceDescription and "NativeHostCustomData" in serviceDescription and len(serviceDescription["NativeHostCustomData"]):
            custom_data_update_url = url + "/subscriptions/" + tenantId + "/UpdateCustomData"
            for service in serviceDescription["NativeHostCustomData"]:
                tempCompId = service["ComponentId"]
                if tempCompId in instanceIdByName:
                    service["ComponentId"] = instanceIdByName[tempCompId]
                    post_response = requests.post(custom_data_update_url, headers=headers, json = service)
                    print "CustomData for component - " +  tempCompId + " , create requests server return code - " + str(post_response.status_code) + " "  + str(post_response.json())

        if serviceDescription and "RDSInstances" in serviceDescription and len(serviceDescription["RDSInstances"]):
            rds_add_url = url + "/subscriptions/" + tenantId + "/RDSInstanceUpdate"
            for service in serviceDescription["RDSInstances"]:
                post_response = requests.post(rds_add_url, headers=headers, json = service)
                print "RDS name - " +  service["Identifier"] + " , create requests server return code - " + str(post_response.status_code) + " "  + str(post_response.json())
