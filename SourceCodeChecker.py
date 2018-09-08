""" Source Code Checker """

import glob
import codecs


# TODO: Make a config for set these
__CONFIG_ENCODE = "utf8"

__CONFIG_TABS_ENABLED = False

__CONFIG_ASCII_CHECKER = False

__CONFIG_NEWLINE_CHARS = "\r\n"

__CONFIG_ENABLED_INDENT_NUM = 4


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
    
    if __CONFIG_ASCII_CHECKER:
        check_ASCII(file)

    file.seek(0)
    check_newline(file)

    file.seek(0)
    if not __CONFIG_TABS_ENABLED:
        check_tabs(file)

    file.seek(0)
    if not __CONFIG_TABS_ENABLED:
        check_indent(file)

    file.seek(0)
    check_trailing_whitespace(file)
    
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


def check_ASCII(file):
    for line in file.readlines():
        for char in line:
            if char > 127:
                print("File corrupt! There is a non-ASCII character!")
                return False    
    return True


def check_newline(file):
    # Check every line has good newline? (and the last line too)
    for line in file.readlines():
        # Get last characters
        last_chars = line[-len(__CONFIG_NEWLINE_CHARS) : ]
        if last_chars != __CONFIG_NEWLINE_CHARS:
            print("File corrupt! There is a wrong newline in the file!")
            return False
    return True


def correct_newline(file):
    # TODO: Imlement it. Shall rewrite the file, or only replace?
    pass


def check_tabs(file):
    for line in file.readlines():
        if "\t" in line:
            print("File corrupt! There is a tabulator in the file!")
            return False
    return True


def correct_tabs(file):
    pass
    # TODO: Implement:
    # 1. replace tabs --> spaces
    # 2. replace spaces --> tab, but only in leading


def check_trailing_whitespace(file):
    for line in file.readlines():
        # Strip newline characters
        line = line.rstrip(__CONFIG_NEWLINE_CHARS)
        if line != line.rstrip():
            print("File problem! There is trailing whitespace!")
            return False
    return True


def check_indent(file):
    # Indent is only interested in space-indented mode, not in tab mode
    for line in file.readlines():
        length_of_leading_spaces = len(line) - len(line.lstrip(' '))
        if (length_of_leading_spaces % __CONFIG_ENABLED_INDENT_NUM) != 0:
            print("File problem! Indent is wrong!")
            return False
    return True


if __name__ == "__main__":
    # execute only if run as a script
    main(dir_path="test\\Src", dir_relative=True)


# TODO: Unittest for TAB
# TODO: Unittest for not tab (indent!)
