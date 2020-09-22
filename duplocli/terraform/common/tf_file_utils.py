import json
import datetime
from collections import defaultdict
import os
import psutil
import shutil

class TfFileUtils:
    _tf_file_name = "main.tf.json"
    _tf_resources_file_name = "resources.json"
    _tf_state_file_name = "terraform.tfstate"
    _schema_file_suffix = "tf_schema.json"
    _tf_import_script_prefix = "tf_import_script"  # .bat .sh
    _tf_run_script_prefix = "run"  # .bat .sh
    root_folder = "duplocli/terraform/"

    def __init__(self, params, step="step1", step_type="infra"):
        self.params = params
        if psutil.WINDOWS:
            self.root_folder = self.root_folder.replace("/", "\\")

    def stage_prefix(self, msg=""):
       return  "**** import {0} {0} {2} {3}: ".format(self.params.provider, self.params.step, self.params.step_type, msg)

    ### env azure ###

    def create_azure_env_sh(self, env_list):
        env_sh_path = self.get_azure_env_sh()
        if os.path.exists(self.env_sh_path):
            return
        self.save_run_script(env_sh_path, env_list, mode="w")
        os.system("chmod  777 {0} ".format(env_sh_path))

    def get_azure_env_sh(self):
        env_sh = ".duplo_env.sh"
        home_folder = os.getenv("HOME")
        self.env_sh_path = os.path.join(home_folder, env_sh) #os.path.join(os.path.dirname(os.path.abspath(__file__)), env_sh)
        if not os.path.exists(self.env_sh_path ):
            self.env_sh_path = "/shell/.duplo_env.sh"
            if  os.path.exists(self.env_sh_path):
                print("using", self.env_sh_path)
            os.system("touch {0}; chmod  777 {1} ".format(self.env_sh_path, self.env_sh_path))
        return self.env_sh_path

    ###  work folder
    def work_folder(self):
        return self._folder_temp_sub_folder(self.params.step, self.params.step_type)
    def work_folder_for_step(self, step):
        return self._folder_temp_sub_folder(step, self.params.step_type)
    def tf_state_file_for_step(self, step):
        return os.path.join(self.work_folder_for_step(step), self._tf_state_file_name)

    #######
    def tf_resources_file(self):
        return os.path.join(self.work_folder(), self._tf_resources_file_name)

    def tf_resources_file_for_step(self, step):
        return os.path.join(self.work_folder_for_step(step), self._tf_resources_file_name)

    def tf_state_file(self):
        return os.path.join(self.work_folder(), self._tf_state_file_name)

    def tf_state_file_srep1(self):
        return os.path.join(self.work_folder_for_step("step1"), self._tf_state_file_name)

    def tf_state_file_srep2(self):
        return os.path.join(self.work_folder_for_step("step2"), self._tf_state_file_name)

    def tf_main_file(self):
        return os.path.join(self.work_folder(), self._tf_file_name)

    def tf_import_script(self):
        return os.path.join(self.work_folder(), self._script_file_name(self._tf_import_script_prefix))

    def tf_run_script(self):
        return os.path.join(self.work_folder(), self._script_file_name(self._tf_run_script_prefix))

    def log_file(self):
        log_file_name = "import-{0}-{1}.log".format(self.params.step_type, self.params.step)
        return self.log_file_by_name(log_file_name)

    def log_file_by_name(self, log_file_name):
        return os.path.join(self.log_folder(), log_file_name)

    #######

    def data_folder(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")

    # def log_folder(self):
    #     return os.path.join(self.params.temp_folder_path, "log")

    def zip_folder(self):
        return os.path.join(self.params.temp_folder_path, "zip")

    def keys_folder(self):
        return os.path.join(self.work_folder(), "keys")

    # def final_folder(self):
    #     return os.path.join(self.params.temp_folder_path, "final")
    #
    ### ### utils  ### ###
    ## windows vs bash
    def _script_ext(self):
        if psutil.WINDOWS:
            return ".bat"
        return ".sh"

    def _script_file_name(self, file_prefix):
        file_path = "{0}{1}".format(file_prefix, self._script_ext())
        return file_path

    def _folder_temp_sub_folder(self, step, step_type):
        return os.path.join(self.params.temp_folder_path, step, step_type)

    ### ### utils  ### ###

    ####### save to files
    def save_main_file(self, data_dict):
        self.save_to_json(self.tf_main_file(), data_dict)
    def save_state_file(self, data_dict):
        self.save_to_json(self.tf_state_file(), data_dict)
    def save_tf_import_script(self, data_list):
        self.save_run_script(self.tf_import_script(), data_list)
    def save_key_file(self, key_name, response_content):
        self._ensure_folder(self.keys_folder())
        self._save_key_file(self._file_inkeys_folder(key_name), response_content)
    def save_tf_run_script(self):
        run_sh_list=[]
        # print(os.getcwd())
        tf_import_script_file = os.path.basename(self.tf_import_script())
        if psutil.WINDOWS :
            run_sh_list.append("cd \"{0}\" ".format(self.work_folder()))
            run_sh_list.append("SET CURRENTDIR=\"%cd%\";  echo %CURRENTDIR%  ".format(self.work_folder()))
            run_sh_list.append("call \"{0}\" ".format(tf_import_script_file))
        else:
            run_sh_list.append("cd {0}".format(self.work_folder()))
            run_sh_list.append("chmod 777 *.sh")
            run_sh_list.append("bash {0}  ".format(tf_import_script_file))
        self.save_run_script(self.tf_run_script(), run_sh_list)
    #######

    #######
    def create_state(self, tf_run_script_file):
        if psutil.WINDOWS:
            cmd_mod = "call \"{0}\" > \"{1}\"  2>&1".format(tf_run_script_file, self.log_file())
            # cmd_mod = "call \"{0}\" ".format(tf_run_script_file )
        else:
            cmd_mod = "chmod +x {0}; bash {0} > {1}  2>&1".format(tf_run_script_file, self.log_file())
        print("START create_state ", cmd_mod)
        resp = os.system(cmd_mod)
        print("DONE create_state ", cmd_mod, resp)
        # delete terraform binaries
        print("**************** deleting terraform binaries **************** ")
        self.empty_terraform_binary_folder()
        print("**************** deleted terraform binaries : for testing - you may run ' terrafrom init ' **************** ")

    ######
    def _ensure_folders(self):
        zip_external = os.path.dirname(self.params.zip_file_path)
        self._ensure_folder(zip_external)
        self._ensure_folder(self.work_folder())
        self._ensure_folder(self.work_folder_for_step("step1"))
        self._ensure_folder(self.work_folder_for_step("step2"))
        self._ensure_folder(self.work_folder_for_step("step3"))
        self._ensure_folder(self.keys_folder())
        self._ensure_folder(self.zip_folder())
        self._ensure_folder(self.final_folder())
        self._ensure_folder(self.log_folder())

    #######
    def empty_all_folder(self):
        self.recreate_folder(self.work_folder())
        self._ensure_folders()
        print("DONE empty_all_folder")

    def delete_folder(self, folder):
        if psutil.WINDOWS:
            cmd_mod = "rmdir /s /q \"{0}\" ".format(folder)
        else:
            cmd_mod = "rm -rf  {0} ".format(folder)
        resp = os.system(cmd_mod)
        print("DONE delete_folder ", cmd_mod, "resp ", resp)
        
    def empty_folder(self):
        self.recreate_folder(self.work_folder())
        self._ensure_folders()
        #print("DONE empty_folder")

    def ensure_folder_by_path(self, path):
        self._ensure_folder(path)
        #print("DONE ensure_folder_by_path ", path)

    def recreate_folder(self, folder):
        if psutil.WINDOWS:
            cmd_mod = "rmdir /s /q \"{0}\\*\";  md `\"{0}\"  2>NUL; dir \"{0}\" ".format(folder)
        else:
            cmd_mod = "rm -rf  {0}/*; mkdir -p {0}; ls  {0}".format(folder)
        resp = os.system(cmd_mod)
        #print("DONE recreate_folder ", cmd_mod, "resp ", resp)

    def ls_folder(self, folder):
        if psutil.WINDOWS:
            cmd_mod = "dir \"{0}\" ".format(folder)
        else:
            cmd_mod = "ls  -alth {0}/*".format(folder)
        os.system(cmd_mod)

    def _ensure_folder(self, folder):
        if psutil.WINDOWS:
            cmd_mod = "md \"{0}\"  2>NUL; dir \"{0}\" ".format(folder)
        else:
            cmd_mod = "mkdir -p {0}; ls  {0}".format(folder)
        #print("DONE _ensure_folder", cmd_mod)
        os.system(cmd_mod)

    def empty_terraform_binary_folder(self):
        terraform_binary_folder = self._file_inwork_folder(".terraform")
        self.recreate_folder(terraform_binary_folder)
        print("****************  DONE empty_terraform_binary_folder **************** ")

    ##########


    def copy_to_final_folder(self, final_folder, copy_files):
        self._ensure_folder(self.final_folder())
        for copy_file in copy_files:
            src_name = os.path.basename(copy_file)
            if os.path.isdir(copy_file):
                dest_path = os.path.join(final_folder, src_name)
                shutil.copytree(copy_file, dest_path)
            else:
                dirname = os.path.basename(os.path.dirname(copy_file))
                final_sub_folder = os.path.join(final_folder, dirname)
                if not os.path.exists(final_sub_folder):
                    self._ensure_folder(final_sub_folder)
                dest_path = os.path.join(final_sub_folder, src_name)
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
        file_path = self._file_inlog_folder_json(file_name)
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
        return os.path.join(self.params.temp_folder_path, sub_folder)
        # return "{0}{1}{2}".format(self.temp_folder_path, os.path.sep, sub_folder)
    #
    # def work_folder(self):
    #     return self._temp_child_folder(self.params.step)

    def keys_folder(self):
        return self._temp_child_folder("keys")

    def zip_folder(self):
        return self.params.zip_folder_path #_temp_child_folder("zip")

    def final_folder(self):
        return self._temp_child_folder("final")

    def log_folder(self):
        return self._temp_child_folder("log")

    def data_folder(self):
        return os.path.join(self.root_folder, "data")

    ## files in folder
    def _file_inwork_folder(self, file_name):
        folder = self.work_folder()
        # TEMP_FOLDER/step1/main.tf.json
        file_path = os.path.join(folder, file_name)
        # file_path = "{0}{1}{2}".format(folder, os.path.sep, file_name)
        return file_path

    def _script_file_inwork_folder(self, file_name):
        folder = self.work_folder()
        # TEMP_FOLDER/step1/run.sh output/step1/run.bat
        file_path = "{0}{1}".format(self._file_inwork_folder(file_name), self._script_ext())
        return file_path

    def _file_inkeys_folder(self, file_name):
        folder = self.keys_folder()
        # TEMP_FOLDER/final/keys/file_name.json
        file_path = os.path.join(folder, file_name)
        # file_path = "{0}{1}{2}".format(folder, os.path.sep, file_name)
        return file_path

    def _file_in_zip_folder(self, file_name):
        folder = self.zip_folder()
        # TEMP_FOLDER/final/keys/file_name.json
        file_path = os.path.join(folder, file_name)
        # file_path = "{0}{1}{2}".format(folder, os.path.sep, file_name)
        return file_path

    def _file_inlog_folder_json(self, file_name):
        folder = self.log_folder()
        # log/abc.json
        file_path = os.path.join(folder, file_name)
        return file_path

    def _file_inlog_folder(self, file_prefix):
        folder = self.log_folder()
        # log/step1-import.log
        # file_path = "{0}-{3}.log".format(os.path.join(folder,  self.params.step), file_prefix)
        file_path = "{0}{1}{2}-{3}.log".format(folder, os.path.sep, self.params.step, file_prefix)
        return file_path

    def _file_indata_folder(self, file_name):
        folder = self.data_folder()
        # data/map.json
        file_path = os.path.join(folder, file_name)
        # file_path = "{0}{1}{2}".format(folder, os.path.sep, file_name)
        return file_path
