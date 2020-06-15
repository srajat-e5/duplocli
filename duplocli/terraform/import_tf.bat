set PYTHONPATH="C:\Program Files (x86)\Duplo.AuthService\duplocli";%PYTHONPATH%
cd "C:\Program Files (x86)\Duplo.AuthService\duplocli\duplocli\terraform\aws\"
set file_path=%1
echo %file_path%
python aws_tf_import.py --params_json_file_path %1