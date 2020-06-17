import json
import datetime
from collections import defaultdict
import os
import psutil
import shutil

class TfFileUtils:
    root_folder="duplocli/terraform/aws/"
    #tf files
    _tf_file_name = "main.tf.json"
    _tf_state_file_name = "terraform.tfstate"

    #data jasons
    _mapping_keys_file_name = "mapping_aws_keys_to_tf_keys.json"
    _schema_file_name = "aws_tf_schema.json"

    #scripts
    _tf_import_script_prefix = "tf_import_script" #.bat .sh
    _tf_run_script_prefix = "run" #.bat .sh

    #TEMP_FOLDER
    temp_folder_path="output"
    zip_folder_path="output/zip"
    zip_folder_local_path = "output/zip"

    def __init__(self, params, step="step1", set_temp_and_zip_folders=True):
        self.params = params
        self.step = step
        if set_temp_and_zip_folders:
            self.set_temp_and_zip_folder()
        if psutil.WINDOWS:
            self.root_folder=self.root_folder.replace("/", "\\")

    def set_temp_and_zip_folder(self):
        if self.params is None:
            return
        self.zip_folder_local_path = self.zip_folder_path
        if self.params.temp_folder is not None:
            self.temp_folder_path = self.params.temp_folder
        if self.params.zip_folder is not None:
            self.zip_folder_path = self.params.zip_folder
        if psutil.WINDOWS:
            self.zip_folder_path = self.zip_folder_path.replace("/", "\\")
            self.temp_folder_path = self.temp_folder_path.replace("/", "\\")
            self.zip_folder_local_path = self.zip_folder_local_path.replace("/", "\\")
        else:
            self.zip_folder_path = self.zip_folder_path.replace("\\", "/")
            self.temp_folder_path = self.temp_folder_path.replace("\\", "/")
            self.zip_folder_local_path = self.zip_folder_local_path.replace("/", "\\")

            ####### get file paths
    # TEMP_FOLDER/step1/aws_tf_schema.json

    def tf_state_file(self):
        return self._file_in_temp_folder(self._tf_state_file_name)
    # TEMP_FOLDER/step1/terraform.tfstate
    def tf_main_file(self):
        return self._file_in_temp_folder(self._tf_file_name)
    # log/step1_import.log
    def log_file(self):
        return self._file_in_log_folder("import")
    # TEMP_FOLDER/step1/tf_import_script.sh
    def tf_import_script(self):
        return self._script_file_in_temp_folder(self._tf_import_script_prefix)
    # TEMP_FOLDER/step1/run.sh
    def tf_run_script(self):
        return self._script_file_in_temp_folder(self._tf_run_script_prefix)
    # data/mapping_aws_keys_to_tf_keys.json
    def mapping_aws_keys_to_tf_keys_file(self):
        return self._file_in_data_folder(self._mapping_keys_file_name)
    # data/aws_tf_schema.json
    def aws_tf_schema_file(self):
        return self._file_in_data_folder(self._schema_file_name)
    def keys_folder(self):
        return self._temp_keys_folder()
    def zip_folder(self):
        return self._temp_zip_folder()

    ####### save to files
    def save_main_file(self, data_dict):
        self.save_to_json(self.tf_main_file(), data_dict)
    def save_state_file(self, data_dict):
        self.save_to_json(self.tf_state_file(), data_dict)
    def save_tf_import_script(self, data_list):
        self.save_run_script(self.tf_import_script(), data_list)
    def save_tf_run_script(self):
        run_sh_list=[]
        # print(os.getcwd())
        tf_import_script_file = os.path.basename(self.tf_import_script())
        if psutil.WINDOWS :
            run_sh_list.append("cd \"{0}\" ".format(self._temp_folder()))
            run_sh_list.append("SET CURRENTDIR=\"%cd%\";  echo %CURRENTDIR%  ".format(self._temp_folder()))
            run_sh_list.append("call \"{0}\" ".format(tf_import_script_file))
        else:
            run_sh_list.append("cd {0}".format(self._temp_folder()))
            run_sh_list.append("chmod 777 *.sh")
            run_sh_list.append("bash {0}  ".format(tf_import_script_file))

        self.save_run_script(self.tf_run_script(), run_sh_list)
    def save_key_file(self, key_name, response_content):
        self._ensure_folder(self._temp_keys_folder())
        self._save_key_file(self._file_in_temp_keys_folder(key_name), response_content)


    #######
    def delete_folder(self, folder):
        if psutil.WINDOWS:
            cmd_mod = "rmdir /s /q \"{0}\" ".format(folder)
        else:
            cmd_mod = "rm -rf  {0} ".format(folder)
        os.system(cmd_mod)
        print("DONE delete_folder ", cmd_mod)

    def ensure_empty_temp_folder(self, folder):
        if psutil.WINDOWS:
            cmd_mod = "rmdir /s /q \"{0}\\*\";  md \"{0}\"  2>NUL; dir \"{0}\" ".format(folder)
        else:
            cmd_mod = "rm -rf  {0}/*; mkdir -p {0}; ls  {0}".format(folder)
        os.system(cmd_mod)
        print("DONE ensure_empty_temp_folder ", cmd_mod)

    def _ensure_folder(self, folder):
        if psutil.WINDOWS:
            cmd_mod = "md \"{0}\"  2>NUL; dir \"{0}\" ".format(folder)
        else:
            cmd_mod = "mkdir -p {0}; ls  {0}".format(folder)
        print("DONE _ensure_folder", cmd_mod)
        os.system(cmd_mod)

    def empty_temp_folder(self):
        self.ensure_empty_temp_folder(self._temp_folder())
        self._ensure_folders()
        print("DONE empty_temp_folder")

    def empty_terraform_binary_folder(self):
        terraform_binary_folder = self._file_in_temp_folder(".terraform")
        self.ensure_empty_temp_folder(terraform_binary_folder)
        print("****************  DONE empty_terraform_binary_folder **************** ")

    def empty_all_folder(self):
        self.ensure_empty_temp_folder(self._temp_folder()) # step1 step2
        self.ensure_empty_temp_folder(self._temp_keys_folder())
        # self.ensure_empty_temp_folder(self._temp_zip_folder()) #keep zip files
        self.ensure_empty_temp_folder(self._temp_final_folder())
        self._ensure_folders()
        print("DONE empty_all_folder")

    def create_state(self, tf_run_script_file):
        if psutil.WINDOWS:
            cmd_mod = "call \"{0}\" > \"{1}\"  2>&1".format(tf_run_script_file, self.log_file())
            # cmd_mod = "call \"{0}\" ".format(tf_run_script_file )
        else:
            cmd_mod = "chmod +x {0}; bash {0} > {1}  2>&1".format(tf_run_script_file, self.log_file())
        print("START create_state ", cmd_mod)
        os.system(cmd_mod)
        print("DONE create_state ", cmd_mod)
        #delete terraform binaries
        print("**************** deleting terraform binaries **************** ")
        self.empty_terraform_binary_folder()
        print("**************** to get back terraform binaries please run ' terrafrom init ' **************** ")

    ######
    def _ensure_folders(self):
        self._ensure_folder(self._temp_folder())
        self._ensure_folder(self._temp_keys_folder())
        self._ensure_folder(self._temp_zip_folder())
        self._ensure_folder(self._temp_final_folder())
        self._ensure_folder(self._data_folder())
        self._ensure_folder(self._log_folder())

    ##########
    def copy_to_final_folder(self, final_folder , copy_files):
        self._ensure_folder(self._temp_final_folder())
        for copy_file in copy_files:
            src_name = os.path.basename(copy_file)
            dest_path = os.path.join(final_folder, src_name)
            if os.path.isdir(copy_file):
                shutil.copytree(copy_file, dest_path)
            else:
                shutil.copy(copy_file, dest_path)

    def zip_final_folder(self, tenant, final_folder, zip_folder, copy_files):
        self.copy_to_final_folder(final_folder, copy_files)
        now = datetime.datetime.now()
        now_str = now.strftime("%m-%d-%Y--%H-%M-%S")
        zipfile_name="import-{0}-{1}".format(tenant, now_str)
        #save to out
        zip_file_to_zip_folder= "{0}{1}{2}".format(zip_folder, os.path.sep, zipfile_name)

        shutil.make_archive(zip_file_to_zip_folder, 'zip', root_dir=final_folder)
        #if zip folder is not same
        if self.params.zip_file_path is not None and self.params.zip_file_path != self.zip_folder():
            shutil.make_archive( self.params.zip_file_path, 'zip', root_dir=final_folder)


   #######
    def load_json_file(self, file):
        with open(file) as f:
            data = json.load(f)
        return data

    def print_json(self, response, sort_keys=True):
        resp_json = json.dumps(response,
                               sort_keys=sort_keys,
                               indent=3,
                               default=self.default)
        print(resp_json)

    def _save_key_file (self, file_name, content):
        f = open(file_name, "wb")
        f.write(content)
        f.close()

    def save_run_script(self, file_name, data_dict, mode="w"):
        new_line="\n"
        if psutil.WINDOWS:
            new_line = "\r\n"
        f = open(file_name, mode)
        f.write(new_line)
        for line in data_dict:
            f.write(line + new_line)
        f.write(new_line)
        f.close()


    def save_json_to_log(self, file_name, data_dict):
        file_path= self._log_folder(file_name)
        self.save_to_json(file_path, data_dict)

    def save_to_json(self, file_name, data_dict):
        resp_json = json.dumps(data_dict,
                               indent=2,
                               default=self.default)
        f = open(file_name, "w")
        f.write(resp_json)
        f.close()

    #######

    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()

    def to_json_str(self, response):
        resp_json = json.dumps(response, default=self.default)
        return resp_json.replace('"', '\\"')


    ########
    ## windows vs bash
    def _script_ext(self):
        if psutil.WINDOWS:
            return ".bat"
        return ".sh"

    def _script_file_name(self, file_prefix):
        file_path = "{0}{1}".format(file_prefix, self._script_ext())
        return file_path

    ## folders
    def _temp_child_folder(self, sub_folder):
        return os.path.join(self.temp_folder_path,sub_folder)
        # return "{0}{1}{2}".format(self.temp_folder_path, os.path.sep, sub_folder)

    def _temp_folder(self):
        return self._temp_child_folder(self.step)

    def _temp_keys_folder(self):
        return self._temp_child_folder("keys")

    def _temp_zip_folder(self):
        return self.zip_folder_path #_temp_child_folder("zip")

    def _temp_final_folder(self):
        return self._temp_child_folder("final")

    def _log_folder(self):
        return self._temp_child_folder("log")

    def _data_folder(self):
        return os.path.join(self.root_folder, "data")

    ## files in folder
    def _file_in_temp_folder(self, file_name):
        folder = self._temp_folder()
        # TEMP_FOLDER/step1/main.tf.json
        file_path = os.path.join(folder, file_name)
        # file_path = "{0}{1}{2}".format(folder, os.path.sep, file_name)
        return file_path

    def _script_file_in_temp_folder(self, file_name):
        folder = self._temp_folder()
        # TEMP_FOLDER/step1/run.sh output/step1/run.bat
        file_path = "{0}{1}".format(self._file_in_temp_folder(file_name), self._script_ext())
        return file_path

    def _file_in_temp_keys_folder(self, file_name):
        folder = self._temp_keys_folder()
        # TEMP_FOLDER/final/keys/file_name.json
        file_path = os.path.join(folder, file_name)
        # file_path = "{0}{1}{2}".format(folder, os.path.sep, file_name)
        return file_path

    def _file_in_zip_folder(self, file_name):
        folder = self._temp_zip_folder()
        # TEMP_FOLDER/final/keys/file_name.json
        file_path = os.path.join(folder, file_name)
        # file_path = "{0}{1}{2}".format(folder, os.path.sep, file_name)
        return file_path

    def _file_in_log_folder(self, file_prefix):
        folder = self._log_folder()
        # log/step1-import.log
        # file_path = "{0}-{3}.log".format(os.path.join(folder,  self.step), file_prefix)
        file_path = "{0}{1}{2}-{3}.log".format(folder, os.path.sep, self.step, file_prefix)
        return file_path

    def _file_in_data_folder(self, file_name):
        folder = self._data_folder()
        # data/map.json
        file_path = os.path.join(folder, file_name)
        # file_path = "{0}{1}{2}".format(folder, os.path.sep, file_name)
        return file_path
