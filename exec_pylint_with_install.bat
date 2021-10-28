python -m venv env
env\Scripts\python.exe -m pip install -r requirements.txt
set PYTHON_FILE_LIST=SourceCodeChecker.py
echo "Execute with only errors"
env\Scripts\python.exe -m pylint %PYTHON_FILE_LIST% --disable=C,R,W
echo "Execute full but do not fail the job"
env\Scripts\python.exe -m pylint %PYTHON_FILE_LIST% --exit-zero


