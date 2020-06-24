from duplocli.terraform.tf_import_parameters import KubernetesImportParameters

from duplocli.terraform.steps.tf_steps import TfSteps

######## ####
def main(params):
    tenant = TfSteps(params)
    tenant.execute()

if __name__ == '__main__':
    params_resovler = KubernetesImportParameters()
    parsed_args = params_resovler.get_parser().parse_args()
    params_resovler.parsed_args(parsed_args)
    params_resovler.validate()
    main(params_resovler)
