from duplocli.terraform.tf_import_parameters import HelmImportParameters

from duplocli.terraform.providers.helm.tf_steps import HelmTfSteps

######## ####
def main(params):
    tenant = HelmTfSteps(params)
    tenant.execute()

if __name__ == '__main__':
    params_resovler = HelmImportParameters()
    parsed_args = params_resovler.get_parser().parse_args()
    params_resovler.parsed_args(parsed_args)
    params_resovler.validate()
    main(params_resovler)
