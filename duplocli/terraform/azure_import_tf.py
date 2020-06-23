
from duplocli.terraform.step1.azure.azure_tf_import import AzureTfImport
from duplocli.terraform.import_parameters import AzureImportParameters

######## ####
def main(params):
    tenant = AzureTfImport(params)
    tenant.execute()

if __name__ == '__main__':
    params_resovler = AzureImportParameters()
    parsed_args = params_resovler.get_parser().parse_args()
    params_resovler.parsed_args(parsed_args)
    params_resovler.validate()
    main(params_resovler)

