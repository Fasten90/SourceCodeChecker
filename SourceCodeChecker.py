""" Source Code Checker """

import glob
import codecs


__CONFIG_ENCODE = "utf8"


def main(dir_path=".", dir_relative=True, file_types="*.c", checks=[], change_mode=False):
    print("Directory: {}\n" \
          "File types: {}".format(
              dir_path, file_types))
    

    # Walk directories
    file_list = glob.glob(dir_path + "\\" + file_types)
    
    for file_path in file_list:
        check_file(file_path)


def check_file(file_path):
    """ Check the file """
    print("Check file: {}".format(file_path))
    #file = open(file_path,'rt')
    file = codecs.open(file_path, 'r', encoding=__CONFIG_ENCODE)

    check_encode(file)
    check_tabs(file)
    
    file.close()
    
    
def check_encode(file):
    try:
        #file.read().decode(__CONFIG_ENCODE)
        file.readlines()
        file.seek(0)
        #print("File encode is OK")
        return True
    except:
        print("File corrupt! Not {} encoded".format(__CONFIG_ENCODE))
        return False


def check_tabs(file):
    for line in file.readlines():
        if "\t" in line:
            print("File corrupt! There is a tabulator in the file!")
            return False
    


if __name__ == "__main__":
    # execute only if run as a script
    main(dir_path="c:\\Engineer\\Projects\\EclipseWorkspace\\SourceCodeChecker\\test\\Src", dir_relative=False)
