import boto3
import os
import psutil
import shutil

class BackupImportFolders:

    def __init__(self ):
        self.u
        self.params = params

    def get_tenants(self):
        terraform_folder = os.path.join(self.import_folder, "terraform")
        tenants = set(os.listdir(terraform_folder))
        return tenants

    def backup_folder(self):
        pass

    def sync_local_to_s3(self, bucket, local):
        tenants = self.get_tenants(local)
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket)
        for obj in bucket.objects.all():
            file = obj.key
            print(file)
            # if file not in files:
            #     bucket.download_file(file, os.path.join(local, file))



if __name__ == '__main__':
    backup_folders = BackupImportFolders()
    #sync_local_to_s3("duploservices-default-backupterraform","/Users/brighu/Downloads/import" )