from duplocli.terraform.tf_import_parameters import AzurermImportParameters

from duplocli.terraform.steps.azurerm.tf_steps import AzurermTfSteps

######## ####
def main(params):
    tenant = AzurermTfSteps(params)
    tenant.execute()

if __name__ == '__main__':
    params_resovler = AzurermImportParameters()
    parsed_args = params_resovler.get_parser().parse_args()
    params_resovler.parsed_args(parsed_args)
    params_resovler.validate()
    main(params_resovler)
