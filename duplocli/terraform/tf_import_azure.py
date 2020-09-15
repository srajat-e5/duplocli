import sys
sys.path.insert(0,'..')
sys.path.insert(0,'../..')

from duplocli.terraform.providers.azurerm.azurerm_params import AzurermParams

from duplocli.terraform.providers.azurerm.tf_steps import AzurermTfSteps

######## ####
def main(params):
    tenant = AzurermTfSteps(params)
    tenant.execute()

if __name__ == '__main__':
    params_resovler = AzurermParams()
    parsed_args = params_resovler.get_parser().parse_args()
    params_resovler.parsed_args(parsed_args)
    params_resovler.validate()
    main(params_resovler)
