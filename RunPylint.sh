# https://docs.pylint.org/en/1.6.0/run.html
# 1 - fatal, 2 - error, ..., 32 - usage

# This file should has "LF" instead of "CRLF" because the BitBucket bash script executing

python -m pylint SourceCodeChecker.py --rcfile=pylintrc

PYLINT_EXIT_CODE=$?

if [ $PYLINT_EXIT_CODE % 2 == 1 ] || [ $PYLINT_EXIT_CODE % 4 == 2 ]
then
  echo 'Pylint exited with important error code: ' $PYLINT_EXIT_CODE
  exit 1
else
  echo 'Pylint exited with ok / small error code: ' $PYLINT_EXIT_CODE
  exit 0
fi

