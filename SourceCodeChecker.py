""" Source Code Checker """

import glob
import codecs
import re
from re import RegexFlag
import os
import copy
import json
import argparse

CONFIG_FILE_DEFAULT_NAME = 'scc_config.json'
CONFIG_FILE_EXTENSION_DEFAULT_FILTER = '*.[c|h]'
CONFIG_STATISTICS_ENABLED = True
STATISTICS_DATA = None


def log_warning(line):
    print(line)


class FileIssue:

    # Helper class for Issue administration
    def __init__(self, file_path, line_number, issue):
        self.__file_path = file_path
        self.__line_number = line_number
        self.__issue = issue

    def print_issue(self):
        print("[issue] {} file, {}. line has issue: {}".format(
            self.__file_path,
            self.__line_number,
            self.__issue
            ))

    def get_text(self):
        return self.__issue


def Load_UnitTest_CheckerConfig(test_config_name):
    global CONFIG_FILE_DEFAULT_NAME

    CONFIG_FILE_DEFAULT_NAME = test_config_name


class ConfigHandler:

    @staticmethod
    def convert_config_to_dict(config):
        default_config_dict = {}
        [default_config_dict.update({name: key['default_value']}) for name, key in config.items()]
        return default_config_dict

    @staticmethod
    def toJSON(obj):
        # return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
        return json.dumps(obj, sort_keys=True, indent=4)

    @staticmethod
    def SaveToFile(ConfigObj):
        config_obj = ConfigHandler.convert_config_to_dict(ConfigObj.config)
        config_json = ConfigHandler.toJSON(config_obj)
        with open(CONFIG_FILE_DEFAULT_NAME, "w") as file:
            file.write(config_json)
        print("Saved SCC config to {}".format(CONFIG_FILE_DEFAULT_NAME))

    @staticmethod
    def LoadFromFile():
        # Two-step loading
        config = None
        print("Start load SCC config from {}".format(CONFIG_FILE_DEFAULT_NAME))
        # with open(_CONFIG_FILE_NAME, "r") as file:
        with open(CONFIG_FILE_DEFAULT_NAME, "r") as file:
            config_raw = file.read()

        try:
            Configs = json.loads(config_raw)
        except Exception as ex:
            # TODO: Check Exception type
            log_warning('Wrong JSON config. Check the syntax')

        print("Loaded SCC config from {}".format(CONFIG_FILE_DEFAULT_NAME))

        # Restructure default config
        default_config = CheckerConfig().config
        default_config_dict = {}
        [default_config_dict.update({name: key['default_value']}) for name, key in default_config.items()]
        # Restructure
        # From
        #         "ASCII checker": {
        #             "checker": Checker.check_ASCII,
        #             "default_value": False,
        #         },
        # To
        # "ASCII checker" : false

        # Check saved config
        for key, val in Configs.items():
            # Check in default config
            if key in default_config_dict:
                # it is in the supported. Leave as is.
                pass
            else:
                # Unknown settings
                log_warning('Unknown, not supported key in the config! "{}"'.format(key))
        # Check default config
        for key, val in default_config_dict.items():
            # Check in loaded configs
            if key in Configs:
                # it is in the supported. Leave as is.
                pass
            else:
                # Unknown settings, adding
                default_value = default_config[key]['default_value']
                Configs.update({key: default_value})
                log_warning('Unknown, missed value from config! "{}" Activated default value: {}'.format(key, default_value))

        return Configs

    @staticmethod
    def ConfigIsAvailable(config_file_path):
        return os.path.exists(config_file_path)


class Checker:

    def __init__(self, file_path=CONFIG_FILE_DEFAULT_NAME):
        """ Set/Load configs """

        self.config_file_path = file_path

        # Default config
        self.config = CheckerConfig()

        if ConfigHandler.ConfigIsAvailable(self.config_file_path):
            self.config = ConfigHandler.LoadFromFile()
        else:
            print("Create default config")
            ConfigHandler.SaveToFile(self.config)


    def load(self, file_path, test_text=None):
        """ Read the file """

        if not file_path and not test_text:
            # Do nothing!
            raise Exception("Used FileAnalysis with incorrect inputs")

        self.__issues = []

        if not file_path:
            # This was necessary for test text and not a file
            print("Test mode")
            if isinstance(test_text, list):
                self.__file_content_string_list = test_text
            elif isinstance(test_text, str):
                self.__file_content_string_list = test_text.splitlines(keepends=True)
            # Update new file will fill the other string values
            self.__update_new_file()
            # Test name:
            self.__file_path = "TestText_NotAFile"
            return

        self.__file_path = file_path

        self.__file_content_string_list = []  # This will be loaded
        self.__file_content_enumerated_list = [()]  # This is from the loaded file
        self.__file_content_full_string = ""  # This is from the loaded file

        self.__new_file_string = ""  # This will be the updated file


        print("Check file: {}".format(self.__file_path))

        # file = open(file_path,'rt')
        file = codecs.open(self.__file_path, 'r', encoding=self.config['ENCODE'])

        # Read entire file
        try:
            # This is an check for ENCODE
            self.__file_content_string_list = file.readlines()
            # print("File encode is OK")
            self.__update_new_file()
        except UnicodeDecodeError:
            self.add_issue(0, "Not {} encoded".format(self.config['ENCODE']))

        file.close()

    def get_code_lines_count(self):
        return len(self.__file_content_string_list)

    def get_file_name(self):
        return self.__file_path

    def update_changed_file(self):
        if self.__new_file_string != "":
            if isinstance(self.__new_file_string, list):
                # List
                self.__file_content_string_list = self.__new_file_string
            else:
                # Not list, normally it is string
                # Note: be careful - hold the newlines!
                self.__file_content_string_list = self.__new_file_string.splitlines(keepends=True)
                # self.__file_content_string_list = []
                # self.__file_content_string_list.append(line + self.config['Newline chars'] for line in self.__new_file_string.splitlines())
            file = codecs.open(self.__file_path, 'w', encoding=self.config['ENCODE'])
            file.writelines(self.__new_file_string)
            file.close()
            print("Updated file: {}".format(self.__file_path))
        else:
            self.debug_print_ok("Not need updated file: {}".format(self.__file_path))

    def __update_new_file(self):
        self.__new_file_string = ""
        # Update new_file
        # TODO: It was extreme died idea, if we only could start with "string list". REFACTOR
        try:
            self.__file_content_enumerated_list = enumerate(self.__file_content_string_list)
        except Exception as e:
            print(("ERROR! Problem with update new file! {}".format(str(e))))
            raise e
        self.__file_content_full_string = "".join(self.__file_content_string_list)
        # self.__file_content_full_string = "".join((line + self.config['Newline chars']) for line in self.__file_content_string_list)
        self.__file_content_enumerated_list = enumerate(self.__file_content_string_list)

    def analyze(self):
        # Analyze with all required checker on one file

        # TODO: This is a trick: Use the original configs for look around
        new_checkers = CheckerConfig().config
        for checker_name, checker_dict in new_checkers.items():
            if 'checker' not in checker_dict:
                # This is a config and not a checker
                continue

            # Rewrite file
            if self.config['Correction enabled']:
                self.__update_new_file()

            # Execute
            if self.config[checker_name]:  # This is the config value
                self.debug_print_ok("Run \"{}\" checker".format(checker_name))
                try:
                    checker_dict["checker"](self)
                except Exception as e:
                    print("ERROR! Exception: {}".format(str(e)))
                    raise

            # Rewrite file
            if self.config['Correction enabled']:
                self.update_changed_file()

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
        if self.config['debug enabled']:
            print(line)

    # ----------------------------------------------------

    def debug_get_new_file(self):
        return self.__new_file_string

    def debug_set_correctize_enabled(self):
        self.config['Correction enabled'] = True

    # ----------------------------------------------------

    def check_ASCII(self):
        result = True
        for i, line in self.__file_content_enumerated_list:
            for char in line:
                if isinstance(char, str):
                    # char type is string --> problem
                    #self.add_issue(i, "There is a non-ASCII character!")
                    continue
                    # TODO Debug..
                if char > 127:
                    self.add_issue(i, "There is a non-ASCII character!")
                    if self.config['Until first error']:
                        self.add_issue(0, "Not {} encoded".format(self.config['ENCODE']))
                        # TODO: Change the immediately return code
                        return False
                    else:
                        result = False
        return result

    def check_newline(self):
        # Check every line has good newline? (and the last line too)
        is_ok = True
        for i, line in self.__file_content_enumerated_list:
            # Get last characters
            last_chars = line[-len(self.config['Newline chars']) : ]
            if last_chars != self.config['Newline chars']:
                self.add_issue(i, "There is a wrong newline in the file!")
                if self.config['Until first error']:
                    return False
                else:
                    is_ok = False
        if not is_ok and self.config['Correction enabled']:
            print('Correctize the newline(s)')
            # TODO: Due the enumerates, it shall be restarted?
            self.__file_content_enumerated_list = enumerate(self.__file_content_string_list)
            self.correct_newline()

        return is_ok


    # TODO: Can be add as new checker / correctizer, but not is can be called from check_newline(from the checker version)
    def correct_newline(self):
        new_file_list = []
        is_changed = False
        for i, line in self.__file_content_enumerated_list:
            # Get last characters
            last_chars = line[-len(self.config['Newline chars']) : ]
            if last_chars != self.config['Newline chars']:
                is_changed = True
                if len(self.config['Newline chars']) == 1:
                    line = line[:-1] + self.config['Newline chars']
                elif len(self.config['Newline chars']) == 2:
                    if line[-2] not in self.config['Newline chars']:
                        # E.g. Only '\n' instead of '\r\n'
                        line = line[:-1] + self.config['Newline chars']
                    else:
                        # Same newline char numbers
                        line = line[:-2] + self.config['Newline chars']
                else:
                    raise Exception('Required Newline chars is not supported!')
            new_file_list.append(line)
        new_file = ''.join(new_file_list)
        self.__new_file_string = new_file
        return self.__new_file_string


    def check_tabs(self):

        if not self.config['Correction enabled']:
            # Only checker, do not correct
            result = True
            for i, line in self.__file_content_enumerated_list:
                if "\t" in line:
                    self.add_issue(i, "There is a tabulator in the file!")
                    if self.config['Until first error']:
                        return False
                    else:
                        result = False
            return result
        else:
            # Correct
            # replace tabs --> spaces
            new_file = []
            result = True
            # TODO: Change to line replacer solution?
            for i, line in self.__file_content_enumerated_list:
                new_line = line.replace("\t", " " * self.config['Tab space size'])
                if new_line != line:
                    self.add_issue(i, "Replaced tabulator(s) in the file!")
                    result = False
                new_file.append(new_line)
            self.__new_file_string = new_file

            return result

    def check_trailing_whitespace(self):
        is_ok = True
        for i, line in self.__file_content_enumerated_list:
            # Strip newline characters
            #line = line.rstrip(self.config['Newline chars'])
            while len(line) > 0 and line[-1] in self.config['Newline chars']:
                line = line[0:-1]
            if line != line.rstrip(" \t"):
                # Now, if "blabla " will not same with "blabla", it has trailing whitespace
                self.add_issue(i+1, "There is trailing whitespace!")  # +1 from starting line from 1.
                if self.config['Until first error']:
                    return False
                else:
                    is_ok = False
        if not is_ok and self.config['Correction enabled']:
            print('Trailing whitespace correction started')
            # TODO: "restart" file
            self.__file_content_enumerated_list = enumerate(self.__file_content_string_list)
            self.correct_trailing_whitespace()

        return is_ok

    # TODO: Can be add as new checker / correctizer, but not is can be called from check_newline(from the check_trailing_whitespace)
    def correct_trailing_whitespace(self):
        new_file_list = []
        for i, line in self.__file_content_enumerated_list:
            # Get last characters
            while len(line) > 0 and line[-1] in self.config['Newline chars']:
                line = line[0:-1]
            if line != line.rstrip(" \t"):
                # trailing whitespaces are here
                line = line.rstrip(" \t")
            new_file_list.append(line + self.config['Newline chars'])
        new_file = ''.join(new_file_list)
        self.__new_file_string = new_file
        return self.__new_file_string

    def check_indent(self):
        result = True
        for i, line in self.__file_content_enumerated_list:
            if self.config['Tabs enabled']:
                # Indent with tabs
                line_free_tab = line.lstrip('\t')
                # TODO: Think on C: '/*'.. and '*' problem
                if line_free_tab != line_free_tab.lstrip(' '):
                    self.add_issue(i+1, "Indent is wrong! (Space after tab)")  # +1 from starting line from 1.
                    if self.config['Until first error']:
                        return False
                    else:
                        result = False
            else:
                # Indent with spaces
                stripped_line = line.lstrip(' ')
                # C special:
                # TODO: Check it is in multiline coment?
                if stripped_line.startswith('/*') or stripped_line.startswith('*'):
                    # Comment line, skip
                    # result = True, but do not overwrite
                    pass
                else:
                    length_of_leading_spaces = len(line) - len(stripped_line)
                    if (length_of_leading_spaces % self.config['Indent space num']) != 0:
                        self.add_issue(i+1, "Indent is wrong! (Wrong number of spaces)")  # +1 from starting line from 1.
                        if self.config['Until first error']:
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

        # file_checking_part = "".join(self.__file_content_string_list[0:10])

        # https://regex101.com/
        # Too long?
        # header_regex = r'\/\*.*\s*\* *(?P<filename>[\w._]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- \/]*).*\s*\* *Target:\s*(?P<target>[\w\d]*).*\s*\* *.*\s*\* *.*\s*\* *\/'
        # header_regex = r'\/\*.*\s*\* *(?P<filename>[\w.]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)'

        # good_header_regex = r'\/\*.*\s*\* *(?P<filename>[\w.]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)\s*\*\/'

        header_regex = r'\/\*[^\*]*\* *(?P<filename>[\w.]*)[^\*]*\* *Created on: *(?P<created_date>[\d\-]*)[^\*]*\* [^\*]*\*[^\*]*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)[^*]*\*'
        # TODO: Put regex101 link to here

        header_regex_compiled = re.compile(header_regex, RegexFlag.MULTILINE)
        # good_header_regex_compiled = re.compile(good_header_regex, RegexFlag.MULTILINE)

        """
        result_good = good_header_regex_compiled.match(full_file)
        if result_good is not None:
            # Good header found!
            print("{} file had good header".format(self.__file_path))
            return
        """

        result = header_regex_compiled.match(self.__file_content_full_string)

        # print(result)

        if result is None:

            print("{} file has not header".format(self.__file_path))
            self.add_issue(0, "file has not header")
        else:

            found_header = result.group(0)

            if self.__file_content_full_string[len(found_header)] == '/':
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
            new_header = ''.join((line + self.config['Newline chars']) for line in new_header_format)
            new_header = new_header.rstrip(self.config['Newline chars'])  # delete last new chars

            new_header = new_header.format(
                filename=result.group("filename"),
                created_date=result.group("created_date"),
                creator=self.config['Creator'],
                email=self.config['E-mail'],
                function=result.group("function"),
                target=result.group("target")
                )

            # full_file = full_file.replace(found_header, new_header)
            pos = self.__file_content_full_string.find("*/")
            pos += 2  # Because the "*/" length

            # print(new_header)
            self.__new_file_string = new_header + self.__file_content_full_string[pos:]

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

            new_file = "".join(self.__file_content_string_list)

            saved_last_line_index = -1

            for i, line in enumerate(self.__file_content_string_list):
                # new_line = line
                if not expected_guard1_ok and "#ifndef" in line:
                    if line == expected_guard1 + self.config['Newline chars']:
                        self.debug_print_ok("Guard1 was okay")
                    else:
                        # Replace
                        new_file = new_file.replace(line, expected_guard1 + self.config['Newline chars'])
                        guard_changed = True
                        self.add_issue(i, "Header guard was wrong - line:\"{}\"".format(line))

                    expected_guard1_ok = True
                    continue

                if not expected_guard2_ok and "#define" in line:
                    if line == expected_guard2 + self.config['Newline chars']:
                        self.debug_print_ok("Guard2 was okay")
                    else:
                        # Replace
                        new_file = new_file.replace(line, expected_guard2 + self.config['Newline chars'])
                        guard_changed = True
                        self.add_issue(i, "Header guard was wrong - line:\"{}\"".format(line))

                    expected_guard2_ok = True
                    continue

                if "#endif" in line:
                    # #endif shall be checked only if it is the last
                    saved_last_line_index = i

            # Finished, check the last line #endif
            if saved_last_line_index >= 0:
                line = self.__file_content_string_list[saved_last_line_index]
                if line == expected_guard3 + self.config['Newline chars']:
                    self.debug_print_ok("Guard3 was okay")
                else:
                    # Replace
                    new_file = new_file.replace(line, expected_guard3 + self.config['Newline chars'])
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

        new_file = self.__file_content_full_string

        file_changed = False
        for keyword_from, keyword_to in doxygen_keywords:
            if keyword_from in new_file:
                file_changed = True
                new_file = new_file.replace(keyword_from, keyword_to)
                self.add_issue(-1, "Found \"{}\" doxygen keyword, which shall be replaced".format(keyword_from))

        if file_changed:
            print("{} file has changed by Doxygen keyword replace(s)".format(self.__file_path))
            self.__new_file_string = new_file

    def run_refactor_comment(self):
        # Refactor

        # Idea:
        # myRe = re.compile(r"(myFunc\(.+?\,.+?\,)(.+?)(\,.+?\,.+?\,.+?\,.+?\))")
        # print myRe.sub(r'\1"noversion"\3', val)
        # \1 means: 1. group

        # "// comment" --> /* comment */
        # But do not change: "///<"
        # And finished with //
        # Tested with: https://regex101.com/
        #                                 html - http*:*//
        #                                 ˇ
        #                                      //  normal line comment
        #                                      ˇ
        #                                              ///< or //* - do not catch
        #                                              ˇ

        # TODO: Delete
        #regex_text_full_line = re.compile(r"([^:])+\/\/(([^\/\<\*])[^\r\n]+)")
        regex_text_full_line = re.compile(r"([^\:\r\n\/\*]*)\/\/[^\/\<\*]([^\r\n]+)[\r\n]")
        regex_replace = re.compile(r"\/\/([^\r\n]+)[\r\n]")
        is_changed = False
        for i, line in self.__file_content_enumerated_list:
            result = regex_text_full_line.match(line)
            if result is not None:
                if result.regs[0][0] == 0:  # This check: the full match is start with first character of line?
                    # So, if regex found full line, we can replace:
                    new_line = regex_replace.sub(r"/* \1 */", line)
                    self.__file_content_string_list[i] = new_line
                    is_changed = True
                    self.add_issue(i, "Comment has been replaced from\n"
                                      "  \"{}\"\n"
                                      "   to\n"
                                      "   \"{}\"\n".format(line, new_line))
                # Found, not full line: so wrong line
            # else: does not match. anything, so it is not comment line
        if is_changed:
            self.__new_file_string = "".join(self.__file_content_string_list)

        # TODO: Remark, file is changed

        # TODO: What shall happen with "///<" ?
        # TODO: Add test: //* ?
        # TODO: Check: /* blabla //bla */
        # TODO: Do not replace http://

    def run_refactor_function_description_comment(self):
        """
        /**
         * @brief   Convert signed decimal to string
         * @note     Only max INT_MAX / 2 number can be converted
         * @return    created string length
         */
        """

        # 1. step
        """
        /**
        * blabla
        */

        /** test */
        """

        # https://regex101.com/r/iJIhCq/1
        """
        /**
         * @doxygen   blabla1
         *          blabla2
         * @doxygen2 blabla3
         *          blabla4
         */
        """
        # r"( *\/\*\*[\s\S]*?\*\/ *)"
        #regex_multiline_comment = re.compile(r"( *\/\*\*.*?\*\/ *)", RegexFlag.MULTILINE)  # Grouping was problematic!
        regex_multiline_comment = re.compile(r" *\/\*\*[\s\S]*?\*\/ *", RegexFlag.MULTILINE)

        is_changed = False
        # TODO: UnitTest
        #result = regex_multiline_comment.match(self.__file_content_full_string)
        result = True
        if result is None:
            self.debug_print_ok("{} file has not function description comment".format(self.__file_path))
        else:
            print("{} file has function description comment".format(self.__file_path))

            self.__new_file_string = copy.deepcopy(self.__file_content_full_string)

            #for multiline_comment in result.groups():
            for multiline_comment in regex_multiline_comment.findall(self.__file_content_full_string):

                if "@" in multiline_comment:
                    print(multiline_comment)
                else:
                    self.debug_print_ok("Skip this multiline comment")
                    continue
                lines = multiline_comment.splitlines()
                # First line mandatory: "/**"
                lines[0] = "/**"
                # Last line mandatory " */"
                lines[-1] = " */"
                previous_indent = 0
                refactored_lines = copy.deepcopy(lines)
                for line_index, line in enumerate(lines[1:-1]):
                    # " * @blabla   blabla"
                    try:
                        # TODO: Only " * @" acceptable
                        pos_at = line.index("@")  # TODO: Hardcoded doxygen start char
                        if line[pos_at-1] != ' ': # Before @ There is a space?
                            # If not space, perhaps another situation, like e-mail address
                            break
                        pos_doxygen_key = pos_at + 1
                        calculated_msg_index = pos_doxygen_key
                        doxygen_keyword = ""
                        # Optimize with index(" ") ?
                        for space_after_doxygen_char in line[pos_doxygen_key:]:
                            if space_after_doxygen_char != ' ':
                                calculated_msg_index += 1
                                doxygen_keyword += space_after_doxygen_char
                            else:
                                # First space
                                break
                        # Here: at after first space
                        for space_after_doxygen_char in line[calculated_msg_index:]:
                            if space_after_doxygen_char == ' ':
                                calculated_msg_index += 1
                            else:
                                # First not space - started msg
                                break
                        msg = line[calculated_msg_index:]
                        # Here: at after last space  --> Indent!

                        refactored_line = " * @" + doxygen_keyword
                        # " @VeryLongPls "
                        calculated_msg_index = max(16, calculated_msg_index)
                        previous_indent = calculated_msg_index
                        refactored_line += " " * (calculated_msg_index - len(refactored_line))
                        refactored_line += msg
                        #line = refactored_line
                        refactored_lines[line_index + 1] = refactored_line
                        is_changed = True
                    except ValueError:
                        # no @
                        # Indent as previous line
                        if previous_indent:
                            try:
                                star_pos = line.index("*")
                            except ValueError:
                                star_pos = 0
                            last_space_pos = star_pos + 1
                            for space_char in line[last_space_pos:]:
                                if space_char == " ":
                                    last_space_pos += 1
                                else:
                                    break
                            msg = line[last_space_pos:]
                            refactored_line = " * "
                            refactored_line += " " * (previous_indent - len(refactored_line))
                            refactored_line += msg
                            #line = refactored_line
                            refactored_lines[line_index + 1] = refactored_line
                            is_changed = True
                        else:
                            # There is no calculated indent
                            print("No calculated indent")
                # Finished
                if is_changed:
                    refactored_lines = "".join([item + "\r\n" for item in refactored_lines])
                    refactored_lines = refactored_lines.rstrip()
                    self.__new_file_string = self.__new_file_string .replace(multiline_comment, refactored_lines)
                # TODO: Save
                # self.add_issue(0, "file has not header")

        if not is_changed:
            self.__new_file_string = ""

    def run_refactor_unused_argument(self):
        """
        (void)argc;
        -->
        UNUSED_ARGUMENT(argc)
        """
        # Deleted: flags=RegexFlag.MULTILINE
        regex_text_from = re.compile(r"^( *)\( *void *\) *([^;]*);", flags=RegexFlag.MULTILINE)
        # Save+restore the space before ( and and after ) and before ;
        self.__new_file_string = regex_text_from.sub(r'\1UNUSED_ARGUMENT(\2);', self.__file_content_full_string)

        # TODO:
        # bool --> bool_t
        # float --> float32_t
        # regex_text_from
        # file_new

    def run_refactor_config_define(self):
        # TODO: Implement
        """
        Change MODULE_DEFINES... --> to CONFIG_MODULE_DEFINES...
        Reason: There are some BLABLA_MODULE_ defines, which shall not be changed! (see !!! _MODULE (before module))
        """
        # regex_text_from = re.compile(r"([^_])MODULE_")
        # self.__new_file_string = regex_text_from.sub(r'\1CONFIG_MODULE_', self.__file_content_full_string)
        pass

    def checker_EOF(self):
        last_chars = self.__file_content_full_string[-len(self.config['Newline chars']):]
        if last_chars != self.config['Newline chars']:
            self.add_issue(0, "There is no correct EOF!")
            if self.config['Correction enabled']:
                self.__new_file_string = self.__file_content_full_string + self.config['Newline chars']
            return False

        return True


class Statistics:
    code_line_count = 0

    def __init__(self):
        # self.code_line_count
        pass

    def inc_code(self, count=1):
        # Add +1 line, or the parameterized
        self.code_line_count += count


def statistics_prepare():
    if CONFIG_STATISTICS_ENABLED:
        global STATISTICS_DATA
        STATISTICS_DATA = Statistics()


def statistics_inc_code_line(count=1):
    if CONFIG_STATISTICS_ENABLED:
        STATISTICS_DATA.inc_code(count)


def statistics_file_code_line(count=0, filename=""):
    if CONFIG_STATISTICS_ENABLED:
        STATISTICS_DATA.inc_code(count)
        print("File: \"{}\" has {} line codes".format(filename, count))


def statistics_finish():
    if CONFIG_STATISTICS_ENABLED:
        print("Project has {} line codes".format(STATISTICS_DATA.code_line_count))


def source_code_checker(source_paths=['.'], file_types='*.[c|h]',
                        config_file_path=CONFIG_FILE_DEFAULT_NAME, recursive=True):

    print("Directories: {}\n"
          "File types: {}".format(
              source_paths, file_types))

    # Walk directories
    # glob use:<path>\**\*.c, recursive=True for subdirectory discovery
    file_glob_list = [source_path + os.sep + file_types for source_path in source_paths]
    file_list = []
    for file_glob_pattern in file_glob_list:
        file_list.extend(glob.glob(file_glob_pattern, recursive=recursive))

    # Config, settings - once
    file_analysis = Checker(config_file_path)

    # TODO: Move statistics to config related
    statistics_prepare()

    # Check files
    # TODO: Export to csv/md
    #         with open(file) as csv_file:
    #             csv_reader = csv.reader(csv_file, delimiter=',')
    #             for row in csv_reader:
    for file_path in file_list:
        file_analysis.load(file_path)
        file_analysis.analyze()
        file_analysis.print_issues()
        statistics_file_code_line(file_analysis.get_code_lines_count(), file_analysis.get_file_name())

    statistics_finish()

    print("Finished")

    return True



class CheckerConfig:

    config = {
        "ENCODE": {
            "default_value": "utf8"
        },
        "ASCII checker": {
            "checker": Checker.check_ASCII,
            "default_value": False,
        },
        "EOF checker": {  # It is important to EOF checker shall be upper than newline checker due the missing EOF is newline issue also
            "checker": Checker.checker_EOF,
            "default_value": True
        },
        "Newline chars": {
            "default_value": "\r\n"
        },
        "Newline checker": {
            "checker": Checker.check_newline,
            "default_value": True
        },
        "Tabs enabled": {
            "default_value": False
        },
        "Tab space size": {
            "default_value": 4
        },
        "Tabs checker": {
            "checker": Checker.check_tabs,
            "default_value": False
        },
        "Indent space num": {
            "default_value": 4
        },
        "Indent checker": {
            "checker": Checker.check_indent,
            "default_value": True
        },
        "Trailing whitespace checker": {
            "checker": Checker.check_trailing_whitespace,
            "default_value": True
        },
        "Header comment checker": {
            "checker": Checker.correctize_header_comment,
            "default_value": False
        },
        "Include guard checker": {
            "checker": Checker.correctize_include_guard,
            "default_value": False
        },
        "Doxygen keywords checker": {
            "checker": Checker.correctize_doxygen_keywords,
            "default_value": False
        },
        "Function description comment": {
            "checker": Checker.run_refactor_function_description_comment,
            "default_value": True
        },
        "Refactor checker - Comment": {
            "checker": Checker.run_refactor_comment,
            "default_value": True
        },
        "Refactor checker - Unused argument": {
            "checker": Checker.run_refactor_unused_argument,
            "default_value": True
        },
        "debug enabled": {
            "default_value": True
        },
        "Creator": {
            "default_value": "Vizi Gabor"
        },
        "E-mail": {
            "default_value": "vizi.gabor90@gmail.com"
        },
        "Until first error": {
            "default_value": False
        },
        "Correction enabled": {
            "default_value": False
        },
        "Statistics enabled": {
            "default_value": True
        }

        # XXX: Add here the new checker
    }

    def __init__(self):
        # Check the list
        for key, value in self.config.items():
            assert "default_value" in value
            # assert "checker" in element.keys()  # Not mandatory

    def get_config(self):
        return ConfigHandler.convert_config_to_dict(self.config)

# Load default configs
config = CheckerConfig().config




def main():
    parser = argparse.ArgumentParser(description='SourceCodeChecker')

    cwd = os.getcwd()

    parser.add_argument('--project-path', required=False, type=str,
                        default=cwd,
                        help='path for project root. It should be directory, it can be relative or absolute path\n'
                             'Default is the cwd')

    parser.add_argument('--is-pipeline', required=False, action='store_true',
                        default=False,
                        help='Is it pipeline? It used for default values')

    parser.add_argument('--source-file-path', required=True, type=str,
                        help='Source(s) file(s) path, what shall be the checker analyzed.\n'
                             'It shall be relative "path filter" from the project-path.\n'
                             '  E.g. Scr\\**,Inc\\**')

    parser.add_argument('--file-extension-filter', required=False, type=str,
                        default=CONFIG_FILE_EXTENSION_DEFAULT_FILTER,
                        help='File filter in regex format.\n'
                             '  E.g. [*.c|h]')

    parser.add_argument('--config-file-path', required=False, type=str,
                        default=CONFIG_FILE_DEFAULT_NAME,
                        help='Config file path. It shall be relative path from project-path\n'
                             'Recommended name: scc_config.json')

    args = parser.parse_args()

    is_pipeline = os.getenv("PIPELINE_WORKSPACE")
    if is_pipeline:
        # Override the argument
        args.is_pipeline = True

    if not os.path.isabs(args.project_path):
        args.project_path = os.path.join(cwd, args.project_path)
    if not os.path.exists(args.project_path):
        raise Exception('The project-path argument does not exist!')
    if not os.path.isdir(args.project_path):
        raise Exception('The project-path argument is not a directory!')

    args.config_file_path = os.path.join(args.project_path, args.config_file_path)
    if not os.path.exists(args.config_file_path):
        raise Exception('The config-file-path argument is not exist!')

    source_filter_list = args.source_file_path.split(',')
    source_list = [os.path.join(args.project_path, item) for item in source_filter_list]

    value_result_list = source_code_checker(source_paths=source_list,
                                            file_types=args.file_extension_filter,
                                            config_file_path=args.config_file_path)


if __name__ == '__main__':
    main()

