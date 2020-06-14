import boto3
import os
import psutil
import shutil
import time, sys
from duplocli.terraform.aws.common.tf_utils import TfUtils
from duplocli.terraform.aws.common.tf_file_utils import TfFileUtils

class BackupImportFolders:
    def __init__(self , backup_settings_json="backup_settings.json", region_name=None):
        self.region_name = region_name
        if region_name is None:
            self.region_name = os.environ['AWS_DEFAULT_REGION']
        if region_name is None:
            raise Exception('AWS_DEFAULT_REGION is not set.')

        self.file_utils = TfFileUtils(None, step="step1", set_temp_and_zip_folders=False)
        self.params = self.file_utils.load_json_file(backup_settings_json)

    def backup_folders(self):
        if self.params['backup_enable'] == "yes" :
            self._ensure_backup_folder()
            tenants = self._get_tenants()
            for tenant in tenants:
                backup_folder =  self._get_backup_folder_for_tenant(tenant)
                import_folders = self._get_import_folders_for_tenant(tenant)
                for import_folder in import_folders:
                    self._backup_folder(backup_folder, import_folder)

            if self.params['s3_backup_enable'] == "yes":
                self.sync_local_to_s3()

    def sync_local_to_s3(self):
        tenants = self._get_tenants()
        s3 = boto3.resource("s3", region_name=self.region_name ) #"us-east-1")
        bucket = s3.Bucket(self.params.s3_bucket_backup)
        all_s3_files = bucket.objects.all()
        for tenant in tenants:
            backup_files = self._get_backup_files_for_tenant(tenant)
            for backup_file in backup_files:
                backup_file_relative =  os.path.join(tenant, backup_file)
                if backup_file_relative not in all_s3_files:
                    bucket.upload_file(os.path.join(self.params.backup_root_folder, backup_file_relative), backup_file_relative)

    ####
    def _backup_folder(self, backup_folder, import_folder):

        #create zip and add to backup folder
        import_folder_name = os.path.basename(import_folder)
        zip_file_name = os.path.join(backup_folder,import_folder_name)
        shutil.make_archive(zip_file_name, 'zip', root_dir=import_folder)

        #delete import_folder - only if older than 1 day
        now = time.time()
        if os.stat(import_folder).st_mtime > now - 1 * 86400:
            self.file_utils.empty_folder(import_folder)

    ######
    def _get_backup_folder_for_tenant(self, tenant):
        terraform_folder = os.path.join(self.params.backup_root_folder, "terraform")
        backup_folder = os.path.join(terraform_folder, tenant)
        self.file_utils._ensure_folder(backup_folder)
        return backup_folder

    def _get_backup_files_for_tenant(self, tenant):
        backup_folder  = self._get_backup_folder_for_tenant(tenant)
        backup_files = set(os.listdir(backup_folder))
        return backup_files

    def _get_import_folders_for_tenant(self, tenant):
        terraform_folder = os.path.join(self.params.terraform_folder, "terraform")
        import_folder = os.path.join(terraform_folder, tenant)
        self.file_utils._ensure_folder(import_folder)
        import_folders = set(os.listdir(terraform_folder))
        # #filter folders older than 1 day
        # import_folders_to_bckup=[]
        # now = time.time()
        # for import_folder in import_folders:
        #     if os.stat(import_folder).st_mtime > now - 1 * 86400 :
        #         import_folders_to_bckup.append(import_folder)
        return import_folders

    def _ensure_backup_folder(self):
        tenants = self._get_tenants()
        for tenant in tenants:
            self._get_backup_folder_for_tenant(tenant)

    def _get_tenants(self):
        terraform_folder = os.path.join(self.params.import_root_folder, "terraform")
        tenants = set(os.listdir(terraform_folder))
        return tenants






if __name__ == '__main__':
    backup_folders = BackupImportFolders()
    #sync_local_to_s3("duploservices-default-backupterraform","/Users/brighu/Downloads/import" )