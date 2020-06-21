
cur_script_path=`dirname $0`
cur_path=`pwd`
cd $cur_script_path\..\..\..
root_folder="`pwd`"
echo "root_folder $root_folder cur_path=$cur_path cur_script_path=$cur_script_path $0"
set PYTHONPATH="$cur_script_path/../../duplocli";%PYTHONPATH%
echo "PYTHONPATH=$PYTHONPATH"

json_file_path="$1"
import_name="$2"
if [ ! -n "$json_file_path" ]
then
	echo "$0 - Error \json_file_path not set or NULL"
else
	echo "\$json_file_path set '$json_file_path'"
fi

if [ ! -n "$import_name" ]
then
  import_name="`date +"%m_%d_%y__%H_%M_%S"`"
	echo "$0 - import_name not provided using $import_name"
fi


python aws_tf_import.py --params_json_file_path "$json_file_path" --import_name "$import_name"