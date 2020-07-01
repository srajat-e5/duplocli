#!/usr/bin/env python
import os
import sys
import json
import requests

def update_lambda():

    s3_file = 'apigateway-zappa-demo.zip'
    S3_BUCKET_LAMBDA = os.getenv('S3_BUCKET_LAMBDA')
    TENANTID = os.getenv('TENANTID')
    use_duplo = False
    DUPLO_URL = os.getenv('DISCOVERY_EP')
    if DUPLO_URL is None:
        use_duplo =True
    if use_duplo :
        DUPLO_URL = os.getenv('DUPLO_URL')
        API_TOKEN = os.getenv('DUPLO_API_TOKEN')


    function_name = os.getenv('LAMBDA_NAME')
    if function_name is None:
        function_name = "duploservices-dev01-helloworld-128329325849"
    if use_duplo:
        headers = { "Authorization": "Bearer {0}".format( API_TOKEN ),
                 'Content-Type': 'application/json'
                 }
    else:
        headers = { 'Content-Type': 'application/json' }
    data = {
        "FunctionName": function_name,
        "Timeout": 20,
        "MemorySize":128,
        "Handler":"handler.lambda_handler",
        "Description":"api gateway demo",
        "Runtime":"python3.7"
    }

    data = json.dumps(data)
    print("UpdateLambdaFunctionConfiguration start ", data)
    endpoint = "{0}/subscriptions/{1}/UpdateLambdaFunctionConfiguration".format(DUPLO_URL, TENANTID)
    response = requests.post(endpoint, headers=headers , data=data)
    print("UpdateLambdaFunctionConfiguration response ", endpoint, response)

    #UpdateLambdaFunction
    data = {
     "FunctionName":function_name,
     "S3Bucket":S3_BUCKET_LAMBDA,
     "S3Key":s3_file
    }
    data = json.dumps(data)
    print("UpdateLambdaFunction start ", data)
    endpoint = "{0}/subscriptions/{1}/UpdateLambdaFunction".format(DUPLO_URL, TENANTID)
    response = requests.post(endpoint, headers=headers , data=data)
    print("UpdateLambdaFunction response ", endpoint, response)

if __name__ == "__main__":
    update_lambda()
