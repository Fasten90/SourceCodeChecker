""" Source Code Checker """

import glob
import codecs
import re
from re import RegexFlag
import os
import copy
import json
from collections import namedtuple

CONFIG_FILE_NAME = "scc_config.json"


class FileIssue():

    # Helper class for Issue administration
    def __init__(self, file_path, line_number, issue):
        self.__file_path = file_path
        self.__line_number = line_number
        self.__issue = issue

    def print_issue(self):
        print("{} file, {}. line has issue: {}".format(
            self.__file_path,
            self.__line_number,
            self.__issue
            ))

    def get_text(self):
        return self.__issue


class FileAnalysisConfig():

    def __init__(self):

        # TODO: Make a config for set these
        self.CONFIG_ENCODE = "utf8"

        self.CONFIG_TABS_ENABLED = False
        self.CONFIG_TABS_CHECKER_ENABLED = False

        self.CONFIG_ASCII_CHECKER_ENABLED = False

        self.CONFIG_NEWLINE_CHECKER_ENABLED = True
        self.CONFIG_NEWLINE_CHARS = "\r\n"

        self.CONFIG_INDENT_SPACE_NUM = 4
        self.CONFIG_INDENT_CHECKER_IS_ENABLED = True

        self.CONFIG_TAB_SPACE_SIZE = 4

        self.CONFIG_TRAILING_WHITESPACE_CHECKER_ENABLED = False

        self.CONFIG_CORRECTIZE_HEADER_ENABLED = False

        self.CONFIG_CORRECTIZE_INCLUDE_GUARD = False

        self.CONFIG_CORRECTIZE_DOXYGEN_KEYWORDS_ENABLED = False

        self.CONFIG_RUN_REFACTOR = True

        self.CONFIG_CREATOR = "Vizi Gabor"
        self.CONFIG_E_MAIL = "vizi.gabor90@gmail.com"

        # TODO: Add "until one error" / "check all file" mode
        self.CONFIG_UNTIL_FIRST_ERROR = False

        self.CONFIG_CORRECTION_ENABLED = True

        self.CONFIG_EOF_MANDATORY_ENABLED = True

        self.debug_enabled = True

    def toJSON(self):
        # return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        return json.dumps(self.__dict__, sort_keys=True, indent=4)


class ConfigHandler():

    # https://stackoverflow.com/questions/3768895/how-to-make-a-class-json-serializable
    @staticmethod
    def toJSON(config):
        # return json.dumps(config, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        # return json.dumps(config, sort_keys=True, indent=4)
        # return json.dumps(config, indent=4)
        # return json.dumps(config.__dict__, indent=4)
        pass

    @staticmethod
    def SaveToFile(config):
        # config_json = ConfigHandler.toJSON(config)
        config_json = config.toJSON()
        with open(CONFIG_FILE_NAME, "w") as file:
            file.write(config_json)
        print("Saved SCC config to {}".format(CONFIG_FILE_NAME))

    # https://stackoverflow.com/questions/6578986/how-to-convert-json-data-into-a-python-object
    @staticmethod
    def LoadFromFile():
        # Two-step loading
        global _CONFIG_FILE_NAME
        config = None
        print("Start load SCC config from {}".format(CONFIG_FILE_NAME))
        # with open(_CONFIG_FILE_NAME, "r") as file:
        with open(CONFIG_FILE_NAME, "r") as file:
            config = file.read()

        # self = json.loads(config)
        config = json.loads(config, object_hook=lambda d: namedtuple('X', d.keys())(*d.values()))

        print("Loaded SCC config from {}".format(CONFIG_FILE_NAME))

        return config
        # o.__dict__ = config

        # obj2_dict = simplejson.loads(config)
        # obj2 = MyCustom.from_json(obj2_dict)

    @staticmethod
    def ConfigIsAvailable():
        return os.path.exists(CONFIG_FILE_NAME)


class FileAnalysis():

    def __init__(self, file_path, test_text=None):
        """ Read the file """

        # Create config
        # TODO: Read from json
        self.config = FileAnalysisConfig()

        if ConfigHandler.ConfigIsAvailable():
            self.config = ConfigHandler.LoadFromFile()
        else:
            print("Create default config")
            ConfigHandler.SaveToFile(self.config)

        if not file_path and not test_text:
            # Do nothing!
            return

        if not file_path:
            print("Test mode")
            self.__file_content_string = test_text
            self.__update_new_file()
            return

        self.__file_path = file_path

        self.__file_content_string = []  # This will be loaded
        self.__file_content_list = [()]  # This is from the loaded file
        self.__full_file = ""  # This is from the loaded file

        self.__new_file_string = ""  # This will be the updated file

        self.__issues = []

        print("Check file: {}".format(self.__file_path))

        # file = open(file_path,'rt')
        file = codecs.open(self.__file_path, 'r', encoding=self.config.CONFIG_ENCODE)

        # Read entire file
        try:
            # This is an check for ENCODE
            self.__file_content_string = file.readlines()
            # print("File encode is OK")
            self.__file_content_list = enumerate(self.__file_content_string)
        except:
            self.add_issue(0, "Not {} encoded".format(self.config.CONFIG_ENCODE))

        file.close()

    def update_file(self):
        if self.__new_file_string != "":
            self.__file_content_string = self.__new_file_string.splitlines()
            file = codecs.open(self.__file_path, 'w', encoding=self.config.CONFIG_ENCODE)
            file.writelines(self.__new_file_string)
            file.close()
            print("Updated file: {}".format(self.__file_path))
        else:
            print("Not need updated file: {}".format(self.__file_path))

    def __update_new_file(self):
        self.__new_file_string = ""
        # Update new_file
        try:
            self.__file_content_list = enumerate(self.__file_content_string)
        except Exception as e:
            print((str(e)))
            raise e
        self.__full_file = "".join(self.__file_content_string)

    def analyze(self):

        analyze_list = [
            {
                "name": "ASCII checker",
                "config": self.config.CONFIG_ASCII_CHECKER_ENABLED,
                "checker": self.check_ASCII
            },
            {
                "name": "Newline checker",
                "config": self.config.CONFIG_NEWLINE_CHECKER_ENABLED,
                "checker": self.check_newline
            },
            {
                "name": "Tabs checker",
                "config": self.config.CONFIG_TABS_CHECKER_ENABLED,
                "checker": self.check_tabs
            },
            {
                "name": "Indent Checker",
                "config": self.config.CONFIG_INDENT_CHECKER_IS_ENABLED,
                "checker": self.check_indent
            },
            {
                "name": "Trailing whitspace checker",
                "config": self.config.CONFIG_TRAILING_WHITESPACE_CHECKER_ENABLED,
                "checker": self.check_trailing_whitespace
            },
            {
                "name": "Header comment checker",
                "config": self.config.CONFIG_CORRECTIZE_HEADER_ENABLED,
                "checker": self.correctize_header_comment
            },
            {
                "name": "Include guard hecker",
                "config": self.config.CONFIG_CORRECTIZE_INCLUDE_GUARD,
                "checker": self.correctize_include_guard
            },
            {
                "name": "Doxygen keywords checker",
                "config": self.config.CONFIG_CORRECTIZE_DOXYGEN_KEYWORDS_ENABLED,
                "checker": self.correctize_doxygen_keywords
            },
            {
                "name": "Refactor hecker",
                "config": self.config.CONFIG_RUN_REFACTOR,
                "checker": self.run_refactor
            },
            {
                "name": "EOF hecker",
                "config": self.config.CONFIG_EOF_MANDATORY_ENABLED,
                "checker": self.correctize_EOF
            },

            ]

        # Check the list
        for element in analyze_list:
            assert("name" in element.keys())
            assert("config" in element.keys())
            assert("checker" in element.keys())

        # Execute command
        for element in analyze_list:
            # Rewrite file
            if self.config.CONFIG_CORRECTION_ENABLED:
                self.__update_new_file()

            # Execute
            if element["config"]:
                self.debug_print_ok("Run \"{}\" checker".format(element["name"]))
                element["checker"]()

            # Rewrite file
            if self.config.CONFIG_CORRECTION_ENABLED:
                self.update_file()

    def add_issue(self, line_number, issue_text):
        self.__issues.append(FileIssue(self.__file_path,
                                    line_number,
                                    issue_text))

    def print_issues(self):
        for issue in self.__issues:
            issue.print_issue()

    def get_text_of_issues(self):
        text = ""
        for issue in self.__issues:
            text += issue.get_text()
        return text

    # ----------------------------------------------------

    def debug_print_ok(self, line):
        if self.config.debug_enabled:
            print(line)

    # ----------------------------------------------------

    def debug_get_new_file(self):
        return self.__new_file_string

    # ----------------------------------------------------

    def check_ASCII(self):
        result = True
        for i, line in self.__file_content_list:
            for char in line:
                if isinstance(char, str):
                    # char type is string --> problem
                    self.add_issue(i, "There is a non-ASCII character!")
                    continue
                if char > 127:
                    self.add_issue(i, "There is a non-ASCII character!")
                    if self.config.CONFIG_UNTIL_FIRST_ERROR:
                        self.add_issue(0, "Not {} encoded".format(self.config.CONFIG_ENCODE))
                        # TODO: Change the immediately return code
                        return False
                    else:
                        result = False
        return result

    def check_newline(self):
        # Check every line has good newline? (and the last line too)
        result = True
        for i, line in self.__file_content_list:
            # Get last characters
            last_chars = line[-len(self.config.CONFIG_NEWLINE_CHARS) : ]
            if last_chars != self.config.CONFIG_NEWLINE_CHARS:
                self.add_issue(i, "There is a wrong newline in the file!")
                if self.config.CONFIG_UNTIL_FIRST_ERROR:
                    return False
                else:
                    result = False
        return result

    def correct_newline(self):
        # TODO: Imlement it. Shall rewrite the file, or only replace?
        pass

    def check_tabs(self):

        if not self.config.CONFIG_CORRECTION_ENABLED:
            # Only checker, do not correct
            result = True
            for i, line in self.__file_content_list:
                if "\t" in line:
                    self.add_issue(i, "There is a tabulator in the file!")
                    if self.config.CONFIG_UNTIL_FIRST_ERROR:
                        return False
                    else:
                        result = False
            return result
        else:
            # Correct
            # replace tabs --> spaces
            new_file = []
            for i, line in self.__file_content_list:
                new_line = line.replace("\t", " " * self.config.CONFIG_TAB_SPACE_SIZE)
                self.add_issue(i, "Replaced tabulator(s) in the file!")
                new_file.append(new_line)
            self.__new_file_string = new_file

            # replace spaces --> tab, but only in leading --> It is indent problem

            """
            if mode == 2:
                new_file = ""
                previous_line_tabs = []
                for i, line in enumerate(self.__file_content_string):
                    # read line char by char
                    column = 0
                    new_line = ""
                    for j in range(0, len(line)):
                        
                        after_tab = False
                        while line[j] == "\t":
                            new_line += ' ' * self.config.CONFIG_TAB_SPACE_SIZE
                            column += self.config.CONFIG_TAB_SPACE_SIZE
                            j += 1
                            after_tab = True
                        # When we here, we are after the tab
                        if after_tab:
                            if j != len(line):
                                # Check the column
                                previous_line_tabs.append(j-1)
                            else:
                                # End of line
                                break
                        
                            
                    # Save new_line
                    new_file += new_line + self.config.CONFIG_NEWLINE_CHARS
            """

    def check_trailing_whitespace(self):
        result = True
        for i, line in self.__file_content_list:
            # Strip newline characters
            line = line.rstrip(self.config.CONFIG_NEWLINE_CHARS)
            if line != line.rstrip():
                self.add_issue(i, "There is trailing whitespace!")
                if self.config.CONFIG_UNTIL_FIRST_ERROR:
                    return False
                else:
                    result = False
        return result

    def check_indent(self):
        result = True
        for i, line in self.__file_content_list:
            if self.config.CONFIG_TABS_ENABLED:
                # Indent with tabs
                line_free_tab = line.lstrip('\t')
                if line_free_tab != line_free_tab.lstrip(' '):
                    self.add_issue(i, "Indent is wrong! (Space after tab)")
                    if self.config.CONFIG_UNTIL_FIRST_ERROR:
                        return False
                    else:
                        result = False
            else:
                # Indent with spaces
                length_of_leading_spaces = len(line) - len(line.lstrip(' '))
                if (length_of_leading_spaces % self.config.CONFIG_INDENT_SPACE_NUM) != 0:
                    self.add_issue(i, "Indent is wrong! (Wrong number of spaces)")
                    if self.config.CONFIG_UNTIL_FIRST_ERROR:
                        return False
                    else:
                        result = False
        return result

    def correctize_header_comment(self):
        """
        /*
         *        Logic.c
         *        Created on:        2017-06-23
         *        Author:            Vizi Gabor
         *        E-mail:            vizi.gabor90@gmail.com
         *        Function:        Logical functions
         *        Target:            STM32Fx
         *        Version:        v1
         *        Last modified:    2017-06-23
         */
        """

        # file_checking_part = "".join(self.__file_content_string[0:10])

        # https://regex101.com/
        # Too long?
        # header_regex = r'\/\*.*\s*\* *(?P<filename>[\w._]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- \/]*).*\s*\* *Target:\s*(?P<target>[\w\d]*).*\s*\* *.*\s*\* *.*\s*\* *\/'
        # header_regex = r'\/\*.*\s*\* *(?P<filename>[\w.]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)'

        # good_header_regex = r'\/\*.*\s*\* *(?P<filename>[\w.]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)\s*\*\/'

        header_regex = r'\/\*[^\*]*\* *(?P<filename>[\w.]*)[^\*]*\* *Created on: *(?P<created_date>[\d\-]*)[^\*]*\* [^\*]*\*[^\*]*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)[^*]*\*'

        header_regex_compiled = re.compile(header_regex, RegexFlag.MULTILINE)
        # good_header_regex_compiled = re.compile(good_header_regex, RegexFlag.MULTILINE)

        """
        result_good = good_header_regex_compiled.match(full_file)
        if result_good is not None:
            # Good header found!
            print("{} file had good header".format(self.__file_path))
            return
        """

        result = header_regex_compiled.match(self.__full_file)

        # print(result)

        if result is None:

            print("{} file has not header".format(self.__file_path))
            self.add_issue(0, "file has not header")
        else:

            found_header = result.group(0)

            if self.__full_file[len(found_header)] == '/':
                # Finished header
                # Good header found!
                print("{} file had good header".format(self.__file_path))
                return

            print("{} file had header, tried change".format(self.__file_path))

            new_header_format = [
                "/*",
                " *    {filename}",
                " *    Created on:   {created_date}",
                " *    Author:       {creator}",
                " *    E-mail:       {email}",
                " *    Function:     {function}",
                " *    Target:       {target}",
                " */"
            ]
            new_header = ''.join((line + self.config.CONFIG_NEWLINE_CHARS) for line in new_header_format)
            new_header = new_header.rstrip(self.config.CONFIG_NEWLINE_CHARS)  # delete last new chars

            new_header = new_header.format(
                filename=result.group("filename"),
                created_date=result.group("created_date"),
                creator=self.config.CONFIG_CREATOR,
                email=self.config.CONFIG_E_MAIL,
                function=result.group("function"),
                target=result.group("target")
                )

            # full_file = full_file.replace(found_header, new_header)
            pos = self.__full_file.find("*/")
            pos += 2  # Because the "*/" length

            # print(new_header)
            self.__new_file_string = new_header + self.__full_file[pos:]

    def correctize_include_guard(self):

        if self.__file_path.endswith(".h"):
            print("{} file checked with include guard".format(self.__file_path))

            # Normalized file name
            # TODO: Move to init
            file_name = os.path.basename(self.__file_path)
            file_name = file_name.split(".")[0]

            file_name = file_name.upper()
            header_text = "{}_H_".format(file_name)

            # Example for INCLUDE GUARD
            # #ifndef COMMON_HANDLER_SWWATCHDOG_H_
            # #define COMMON_HANDLER_SWWATCHDOG_H_
            # #endif /* COMMON_HANDLER_SWWATCHDOG_H_ */

            expected_guard1 = "#ifndef {}".format(header_text)
            expected_guard2 = "#define {}".format(header_text)
            expected_guard3 = "#endif /* {} */".format(header_text)

            expected_guard1_ok = False
            expected_guard2_ok = False
            expected_guard3_ok = False

            guard_changed = False

            new_file = "".join(self.__file_content_string)

            saved_last_line_index = -1

            for i, line in enumerate(self.__file_content_string):
                # new_line = line
                if not expected_guard1_ok and "#ifndef" in line:
                    if line == expected_guard1 + self.config.CONFIG_NEWLINE_CHARS:
                        self.debug_print_ok("Guard1 was okay")
                    else:
                        # Replace
                        new_file = new_file.replace(line, expected_guard1 + self.config.CONFIG_NEWLINE_CHARS)
                        guard_changed = True
                        self.add_issue(i, "Header guard was wrong - line:\"{}\"".format(line))

                    expected_guard1_ok = True
                    continue

                if not expected_guard2_ok and "#define" in line:
                    if line == expected_guard2 + self.config.CONFIG_NEWLINE_CHARS:
                        self.debug_print_ok("Guard2 was okay")
                    else:
                        # Replace
                        new_file = new_file.replace(line, expected_guard2 + self.config.CONFIG_NEWLINE_CHARS)
                        guard_changed = True
                        self.add_issue(i, "Header guard was wrong - line:\"{}\"".format(line))

                    expected_guard2_ok = True
                    continue

                if "#endif" in line:
                    # #endif shall be checked only if it is the last
                    saved_last_line_index = i

            # Finished, check the last line #endif
            if saved_last_line_index >= 0:
                line = self.__file_content_string[saved_last_line_index]
                if line == expected_guard3 + self.config.CONFIG_NEWLINE_CHARS:
                    self.debug_print_ok("Guard3 was okay")
                else:
                    # Replace
                    new_file = new_file.replace(line, expected_guard3 + self.config.CONFIG_NEWLINE_CHARS)
                    guard_changed = True

                expected_guard3_ok = True
            else:
                # Did not found last #endif
                self.add_issue(-1, "Header guard was wrong - missing last #endif")

            if not (expected_guard1_ok and expected_guard2_ok and expected_guard3_ok):
                print("ERROR! Include guard error!")
                self.add_issue(-1, "Header guard was wrong")

            if guard_changed:
                print("Include guards changed")
                self.__new_file_string = new_file

        else:
            self.debug_print_ok("{} file not checked with include guard, because it is not header file".format(self.__file_path))

    def correctize_doxygen_keywords(self):

        doxygen_keywords = [
            # From to what
            ("\\brief", "@brief"),
            ("\\param", "@param"),
            ("\\note", "@note"),
            ("\\return", "@return"),
            ("\\retval", "@retval"),
            ("\\sa", "@sa")
            ]

        new_file = "".join(self.__file_content_string)

        file_changed = False
        for keyword_from, keyword_to in doxygen_keywords:
            if keyword_from in new_file:
                file_changed = True
                new_file = new_file.replace(keyword_from, keyword_to)
                self.add_issue(-1, "Found \"{}\" doxygen keyword, which shall be replaced".format(keyword_from))

        if file_changed:
            print("{} file has changed by Doxygen keyword replace(s)".format(self.__file_path))
            self.__new_file_string = new_file

    def run_refactor(self):
        # Refactor
        # TODO: Make beautiful list handled refactor method
        file_new = copy.copy(self.__full_file)

        # Idea:
        # myRe = re.compile(r"(myFunc\(.+?\,.+?\,)(.+?)(\,.+?\,.+?\,.+?\,.+?\))")
        # print myRe.sub(r'\1"noversion"\3', val)
        # \1 means: 1. group

        """
        Change MODULE_DEFINES... --> to CONFIG_MODULE_DEFINES...
        Reason: There are some BLABLA_MODULE_ defines, which shall not be changed! (see !!! _MODULE (before module))
        """
        regex_text_from = re.compile(r"([^_])MODULE_")
        file_new = regex_text_from.sub(r'\1CONFIG_MODULE_', file_new)

        """
        "// comment" --> /* comment */
        But do not change: "///<"
        And finished with // 
        """
        regex_text_from = re.compile(r"\/\/[^\/\<]([^\r\n]+)")
        file_new = regex_text_from.sub(r'/* \1 */', file_new)

        # TODO: What shall happen with "///<" ?

        """
        (void)argc;
        -->
        UNUSED_ARGUMENT()
        """
        regex_text_from = re.compile(r"^( *)\( *void *\) *([^;]*);", flags=RegexFlag.MULTILINE)
        file_new = regex_text_from.sub(r'\1UNUSED_ARGUMENT(\2);', file_new)

        # TODO:
        # bool --> bool_t
        # float --> float32_t
        # regex_text_from
        # file_new

        # Save if need
        if file_new != self.__full_file:
            self.__new_file_string = file_new

    def correctize_EOF(self):
        last_chars = self.__full_file[-len(self.config.CONFIG_NEWLINE_CHARS):]
        if last_chars != self.config.CONFIG_NEWLINE_CHARS:
            self.add_issue(0, "There is no correct EOF!")
            if self.config.CONFIG_CORRECTION_ENABLED:
                self.__new_file_string = self.__full_file + self.config.CONFIG_NEWLINE_CHARS
            return False

        return True
# TODO: Add type checker


def run_checker(dir_path=".", dir_relative=True, file_types="*.[c|h]", checks=[], change_mode=False, recursive=True):
    # TODO: Delete dir_relative
    # TODO: Implement checks
    # TODO: Implement change_mode

    print("Directory: {}\n" \
          "File types: {}".format(
              dir_path, file_types))

    # Walk directories
    # glob use:<path>\**\*.c, recursive=True for subdirectory discovery
    patten = dir_path + "\\" + file_types
    file_list = glob.glob(patten, recursive=recursive)

    # Check files
    for file_path in file_list:
        file_analysis = FileAnalysis(file_path)
        file_analysis.analyze()
        file_analysis.print_issues()

    print("Finished")


if __name__ == "__main__":
    # execute only if run as a script
    # Test:
    FileAnalysis(file_path=None)
    run_checker(dir_path="Fasten\\**", dir_relative=True, recursive=True)

# TODO: Unittest for TAB
# TODO: Unittest for not tab (indent!)
