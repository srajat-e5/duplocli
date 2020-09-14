
# app params for all providers = aws/azure
arg_params = {
    "import_module": {"short_name": "m", "disc": "import_module=infra, tenant, tenant_list, all. default is tenant,"},
    "import_name": {"short_name": "i", "disc": "zip file path to save imported terraform files in zip format "},
    "zip_file_path": {"short_name": "o", "disc": "zip file path to save imported terraform files in zip format"},
    "download_aws_keys": {"short_name": "k", "disc": "Aws keypair=yes/no, private key used for ssh into EC2 servers"},
    "tenant_name": {"short_name": "n", "disc": "Tenant Name(s) comma separated e.g. webdev or  webdev,website,default"},
    "tenant_id": {"short_name": "t", "disc": "TenantId(s) comma separated e.g.  xxxxxx,yyy,97a833a4-2662-4e9c-9867-222565ec5cb6"},
    "api_token": {"short_name": "a", "disc": "Duplo API Token. API Token must be with admin rights for multi-tenant."},
    "url": {"short_name": "u", "disc": "Duplo URL  e.g. https://msp.duplocloud.net"},
    "params_json_file_path": {"short_name": "j", "disc": "All params passed as single JSON file."},
    "aws_region": {"short_name": "r", "disc": "AWSREGION  e.g. us-west2"}
}


####################### params #############################################################
####################### params #############################################################
####################### params #############################################################

def get_help(params):
    attr_names = params.attr_names
    provider = params.provider

    help_str = []
    help_str.append("Terraform provider: " + provider)
    help_str.append("")
    help_str.append("Terraform import parameters help")
    help_str.append("")
    help_str.append("")
    help_str.append("Sequence of parameters evaluation is: default -> ENV -> JSON_FILE -> arguments")
    help_str.append("   parameters in argument ")
    help_str.append("       ->  override  parameters in terraform_import_json")
    help_str.append("   AND parameters in terraform_import_json ")
    help_str.append("        ->   override  parameters in ENV variables")
    help_str.append("   AND parameters in ENV variables")
    help_str.append("       ->   override default values (json_import_tf_parameters_default.json)")
    help_str.append("")
    help_str.append("")
    help_str.append("parameters in argument")
    help_str.append("")
    for attr_name in attr_names:
        attr = arg_params[attr_name]
        str = "   [-{0} / --{1} {2}]         -- {3}".format(attr['short_name'], attr_name, attr_name.upper(),
                                                            attr["disc"])
        help_str.append(str)
    help_str.append("")
    help_str.append("")
    help_str.append(" OR alternately ")
    help_str.append(" pass the above parameters in single json file")
    help_str.append("")
    help_str.append(" [-j/--params_json_file_path PARAMSJSONFILE] = FOLDER/terraform_import_json.json")
    help_str.append("{")
    for attr_name in attr_names:
        attr = arg_params[attr_name]
        str = "   \"{0}\": \"xxxxxx\"  ".format(attr_name)
        help_str.append(str)
    help_str.append("}")

    help_str.append("")
    help_str.append("")
    help_str.append(" OR alternately ")
    help_str.append(" pass the above parameters in ENV variables")
    help_str.append("")
    for attr_name in attr_names:
        attr = arg_params[attr_name]
        str = "   export \"{0}\"=\"xxxxxx\"  ".format(attr_name)
        help_str.append(str)
    help_str.append(" ")
    help_str.append(" ")

    return "\n".join(help_str)
