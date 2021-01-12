
REM set PYTHONPATH=%PYTHONPATH%;duplocli\terraform\aws;.

set PYTHONPATH=duplocli\terraform\aws;.


REM @ECHO OFF
set json_file_path="%1"
set import_name="%2"
set run_python=true
set mydate="%date:~10,4%_%date:~4,2%_%date:~7,2%_%time:~0,2%_%time:~3,2%_%time:~6,2%"
if "%2"=="" (
    set import_name=%mydate%
)

if %json_file_path%=="" (
   set run_python=false
   echo json_file_path must be provided
)

echo run_python-value %run_python%
if %run_python%==true (

python duplocli\terraform\aws\aws_tf_import.py --params_json_file_path %json_file_path% --import_name %import_name%

)