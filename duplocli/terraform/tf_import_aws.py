from duplocli.terraform.steps.aws.aws_params import AwsParams
from duplocli.terraform.steps.aws.tf_steps import AwsTfSteps

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
