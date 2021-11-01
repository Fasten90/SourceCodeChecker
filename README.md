# SourceCodeChecker
Edited by VG

## Goals
This project is for checking a project source code files (*.c, *.h, *.py and later others).

The script shall print/list the problems, and resolve the problems, if can


## Arguments
* --project-path
* --is-pipeline
* --source-file-path
* --file-extension-filter
* --config-file-path
* --export-csv-file-path

Config file: Check the `scc_config.json`


Execution:

`python SourceCodeChecker.py --project-path=..\\..\\AtollicWorkspace\\FastenHomeAut --source-file-path='Src\**,Inc\**,Drivers\x86\**'`

Where:
* project-path is the root folder where the source files are will be given by relative paths. It is recommended to be the project root
* source-file-path is a list (separated with ',' and glob (*) can be used), where the check files can be find. It is a filter
* Other parameters shall not used, but can be used.


## Limitations
Only for c,h files

