
#NOTE: not arguments for tf file for export from aws

# fill more info into main.tf without state file.


# instances -- ec2
# s3 buckets
# elastic cache
# rds
# dynamodb



#step - 1
    1.a - # exported list pre-defined objects to be exported 
       objects = aws_iam_role, aws_iam_instance_profile, aws_security_group, aws_instance aws_s3_bucket,
          aws_db_instance 
        
    1.b - for each object
            -- get the list from aws... apply filter by tenant name
    1.c - generate tf - which defines all list instance of each object above with duplo given name as Terraform variable name
        - generate sh file - create terrform import = using each instance-id of each object 
    1.d - crearte state - execute the sh file to create terraform.tfstate
#step - 2
    2.a - copy terraform.tfstate file from step-1. we do not copy main.tf.json from step1 but instead regenerate this file in 2.c
    2.b - load schema ../data/aws_tf_schema.json (pre-generated). which has instance field details 
          required, computed, sensitive, optional, data-type,  nested hash tables fields.
          nested hash tables fields - are recursive and has same structure.
        2-b-1 - bugs in tf - we need to add some exception (todo; add list). 
        2-b-2 - aws_to_tf_sync_id_mapping.json: we need mapping for object to object-id field to sync aws and tf 
    2.c - generate tf - using tfstate and schema files.
    2.d - generate sh file -  with terraform init and terraform plan commands and verify no state change needed during plan.
    2.e - final output are =  main.tf.json + terraform.tfstate
    
    
# run 
        




# 1 use case:
# export tenant, terminate duplo, enhance tf , apply changes
    #  RESULT: update existing tenant
    # CAUTION: if duplo is running than it will remove the enhancement,
    # since the new resources have duplo signature, but not in duplo state db.

# 2   use case : Export Tenant and import with a new name in same a/c.
# export tenant, terminate duplo, copy tf file into new tf to new folder,  string replace tanant name to new tanant name
    # , no state-file  for new tf file, ( original tf + state file are intact apply changes
    # RESULT: old tenant artificats are intact in aws, new tenant artificats are created as per the new tf.
    # CAUTION: if duplo is running than it will remove the enhancement,
    # since the new resources have duplo signature, but not in duplo state db.

# 3 use case: Export Tenant and import with a new name in new aws a/c.
# export tenant, terminate  duplo, copy tf file into new tf to new folder,  string replace tanant name to new tanant name, update vpc-ids
    # , no state-file  for new tf file,  apply changes
    # RESULT: new tenant artificats are created in new aws a/c as per the new terraform tf file.
    # CAUTION: if duplo is running in another aws a/c - than it will remove the enhancement,
    # since the new resources have duplo signature, but not in duplo state db.

# 4 use case: Co-exists duplo and terraform provisioning.
# you can run use case (2), but in tf file remove the duplo signature.
