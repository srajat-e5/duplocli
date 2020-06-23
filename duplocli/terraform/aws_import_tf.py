
from duplocli.terraform.step1.aws.aws_tf_import import AwsTfImport
from duplocli.terraform.import_parameters import AwsImportParameters

######## ####
def main(params):
    tenant = AwsTfImport(params)
    tenant.execute()

if __name__ == '__main__':
    params_resovler = AwsImportParameters()
    parsed_args = params_resovler.get_parser().parse_args()
    params_resovler.parsed_args(parsed_args)
    params_resovler.validate()
    main(params_resovler)
