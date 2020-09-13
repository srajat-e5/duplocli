from duplocli.terraform.tf_import_parameters import GoogleImportParameters

from duplocli.terraform.steps.google.tf_steps import GoogleTfSteps

######## ####
def main(params):
    tenant = GoogleTfSteps(params)
    tenant.execute()

if __name__ == '__main__':
    params_resovler = GoogleImportParameters()
    parsed_args = params_resovler.get_parser().parse_args()
    params_resovler.parsed_args(parsed_args)
    params_resovler.validate()
    main(params_resovler)
