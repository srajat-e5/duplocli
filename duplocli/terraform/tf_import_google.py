import sys

sys.path.insert(0, '..')
sys.path.insert(0, '../..')

from duplocli.terraform.providers.google.google_params import GoogleParams
from duplocli.terraform.providers.google.tf_steps import GoogleTfSteps


######## ####
def main(params):
    tenant = AwsTfSteps(params)
    tenant.execute()


if __name__ == '__main__':
    params_resovler = AwsParams()
    parsed_args = params_resovler.get_parser().parse_args()
    params_resovler.parsed_args(parsed_args)
    params_resovler.validate()
    main(params_resovler)
