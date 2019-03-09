""" Source Code Checker """

import glob
import codecs
import re
from re import RegexFlag 
import os
import copy        


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


class FileAnalysis():

    # TODO: Make a config for set these
    __CONFIG_ENCODE = "utf8"

    __CONFIG_TABS_ENABLED = False
    __CONFIG_TABS_CHECKER_ENABLED = False

    __CONFIG_ASCII_CHECKER_ENABLED = False

    __CONFIG_NEWLINE_CHECKER_ENABLED = False
    __CONFIG_NEWLINE_CHARS = "\r\n"

    __CONFIG_INDENT_SPACE_NUM = 4
    __CONFIG_INDENT_CHECKER_IS_ENABLED = False

    __CONFIG_TAB_SPACE_SIZE = 4
    
    __CONFIG_TRAILING_WHITESPACE_CHECKER_ENABLED = False
    
    __CONFIG_CORRECTIZE_HEADER_ENABLED = False
    
    __CONFIG_CORRECTIZE_INCLUDE_GUARD = False
    
    __CONFIG_CORRECTIZE_DOXYGEN_KEYWORDS_ENABLED = False

    __CONFIG_RUN_REFACTOR = True
    
    
    __CONFIG_CREATOR = "Vizi Gabor"
    __CONFIG_E_MAIL = "vizi.gabor90@gmail.com"
    
    # TODO: Add "until one error" / "check all file" mode
    __CONFIG_UNTIL_FIRST_ERROR = False
    
    CONFIG_CORRECTION_ENABLED = True
    
    __debug_enabled = True


    def __init__(self, file_path):
        """ Read the file """

        self.__file_path = file_path
        self.__issues = []
        self.__new_file = ""
        self.__file = []

        print("Check file: {}".format(self.__file_path))

        #file = open(file_path,'rt')
        file = codecs.open(self.__file_path, 'r', encoding=self.__CONFIG_ENCODE)

        # Read entire file
        try:
            # This is an check for ENCODE
            self.__file = file.readlines()
            #print("File encode is OK")
        except:
            self.add_issue(0, "Not {} encoded".format(self.__CONFIG_ENCODE))

        file.close()
        
        
    def update_file(self):
        if self.__new_file != "":
            file = codecs.open(self.__file_path, 'w', encoding=self.__CONFIG_ENCODE)
            file.writelines(self.__new_file)
            file.close() 
            print("Updated file: {}".format(self.__file_path))
        else:
            print("Not need updated file: {}".format(self.__file_path))


    def analyze(self):

        if self.__CONFIG_ASCII_CHECKER_ENABLED:
            self.check_ASCII()

        if self.__CONFIG_NEWLINE_CHECKER_ENABLED:
            self.check_newline()

        if self.__CONFIG_TABS_CHECKER_ENABLED:
            if self.CONFIG_CORRECTION_ENABLED:
                self.correct_tabs()
                # self.__file  changed!
            else:
                self.check_tabs()

        if self.__CONFIG_INDENT_CHECKER_IS_ENABLED:
            self.check_indent()

        if self.__CONFIG_TRAILING_WHITESPACE_CHECKER_ENABLED:
            self.check_trailing_whitespace()
            
        if self.__CONFIG_CORRECTIZE_HEADER_ENABLED:
            self.correctize_header_comment()
            
        if self.__CONFIG_CORRECTIZE_INCLUDE_GUARD:
            self.correctize_include_guard()

        if self.__CONFIG_CORRECTIZE_DOXYGEN_KEYWORDS_ENABLED:
            self.correctize_doxygen_keywords()
            
        if self.__CONFIG_RUN_REFACTOR:
            self.refactor_macro()


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
        if self.__debug_enabled:
            print(line)

    # ----------------------------------------------------


    def check_ASCII(self):
        result = True
        for i, line in enumerate(self.__file):
            for char in line:
                if char > 127:
                    self.add_issue(i, "There is a non-ASCII character!")
                    if self.__CONFIG_UNTIL_FIRST_ERROR:
                        return False
                    else:
                        result = False
        return result


    def check_newline(self):
        # Check every line has good newline? (and the last line too)
        result = True
        for i, line in enumerate(self.__file):
            # Get last characters
            last_chars = line[-len(self.__CONFIG_NEWLINE_CHARS) : ]
            if last_chars != self.__CONFIG_NEWLINE_CHARS:
                self.add_issue(i, "There is a wrong newline in the file!")
                if self.__CONFIG_UNTIL_FIRST_ERROR:
                    return False
                else:
                    result = False
        return result


    def correct_newline(self):
        # TODO: Imlement it. Shall rewrite the file, or only replace?
        pass


    def check_tabs(self):
        result = True
        for i, line in enumerate(self.__file):
            if "\t" in line:
                self.add_issue(i, "There is a tabulator in the file!")
                if self.__CONFIG_UNTIL_FIRST_ERROR:
                    return False
                else:
                    result = False
        return result


    def correct_tabs(self):
        # replace tabs --> spaces
        mode = 1
        if mode == 1:
            new_file = []
            for i, line in enumerate(self.__file):
                new_line = line.replace("\t", " " * self.__CONFIG_TAB_SPACE_SIZE)
                self.add_issue(i, "Replaced tabulator(s) in the file!")
                new_file.append(new_line)
            self.__new_file = new_file
                    
        # replace spaces --> tab, but only in leading --> It is indent problem
        
        """
        if mode == 2:
            new_file = ""
            previous_line_tabs = []
            for i, line in enumerate(self.__file):
                # read line char by char
                column = 0
                new_line = ""
                for j in range(0, len(line)):
                    
                    after_tab = False
                    while line[j] == "\t":
                        new_line += ' ' * self.__CONFIG_TAB_SPACE_SIZE
                        column += self.__CONFIG_TAB_SPACE_SIZE
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
                new_file += new_line + self.__CONFIG_NEWLINE_CHARS
        """


    def check_trailing_whitespace(self):
        result = True
        for i, line in enumerate(self.__file):
            # Strip newline characters
            line = line.rstrip(self.__CONFIG_NEWLINE_CHARS)
            if line != line.rstrip():
                self.add_issue(i, "There is trailing whitespace!")
                if self.__CONFIG_UNTIL_FIRST_ERROR:
                    return False
                else:
                    result = False
        return result


    def check_indent(self):
        result = True
        for i, line in enumerate(self.__file):
            if self.__CONFIG_TABS_ENABLED:
                # Indent with tabs
                line_free_tab = line.lstrip('\t')
                if line_free_tab != line_free_tab.lstrip(' '):
                    self.add_issue(i, "Indent is wrong! (Space after tab)")
                    if self.__CONFIG_UNTIL_FIRST_ERROR:
                        return False
                    else:
                        result = False
            else:
                # Indent with spaces
                length_of_leading_spaces = len(line) - len(line.lstrip(' '))
                if (length_of_leading_spaces % self.__CONFIG_INDENT_SPACE_NUM) != 0:
                    self.add_issue(i, "Indent is wrong! (Wrong number of spaces)")
                    if self.__CONFIG_UNTIL_FIRST_ERROR:
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
        
        full_file = "".join(self.__file)
        #file_checking_part = "".join(self.__file[0:10])        

        # https://regex101.com/
        # Too long?
        #header_regex = r'\/\*.*\s*\* *(?P<filename>[\w._]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- \/]*).*\s*\* *Target:\s*(?P<target>[\w\d]*).*\s*\* *.*\s*\* *.*\s*\* *\/'
        #header_regex = r'\/\*.*\s*\* *(?P<filename>[\w.]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)'

        #good_header_regex = r'\/\*.*\s*\* *(?P<filename>[\w.]*).*\s*\* *Created on:\s*(?P<created_date>[\d\-]*).*\s*\* *.*\s*\* *.*\s*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)\s*\*\/'
        
        header_regex = r'\/\*[^\*]*\* *(?P<filename>[\w.]*)[^\*]*\* *Created on: *(?P<created_date>[\d\-]*)[^\*]*\* [^\*]*\*[^\*]*\* *Function:\s*(?P<function>[\w\d.\- ]*).*\s*\* *Target:\s*(?P<target>[\w\d]*)[^*]*\*'

        header_regex_compiled = re.compile(header_regex, RegexFlag.MULTILINE)
        #good_header_regex_compiled = re.compile(good_header_regex, RegexFlag.MULTILINE)

        """
        result_good = good_header_regex_compiled.match(full_file)
        if result_good is not None:
            # Good header found!
            print("{} file had good header".format(self.__file_path))
            return
        """

        result = header_regex_compiled.match(full_file)

        #print(result)

        if result is None:
            print("{} file has not header".format(self.__file_path))
        else:

            found_header = result.group(0)
            
            if full_file[len(found_header)] == '/':
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
            new_header = ''.join((line + self.__CONFIG_NEWLINE_CHARS) for line in new_header_format)
            new_header = new_header.rstrip(self.__CONFIG_NEWLINE_CHARS)  # delete last new chars
            
            new_header = new_header.format(
                filename=result.group("filename"),
                created_date=result.group("created_date"),
                creator=self.__CONFIG_CREATOR,
                email=self.__CONFIG_E_MAIL,
                function=result.group("function"),
                target=result.group("target")
                )
            
            
            #full_file = full_file.replace(found_header, new_header)
            pos = full_file.find("*/")
            pos += 2  # Because the "*/" length
            
            #print(new_header)
            self.__new_file = new_header + full_file[pos:]
            
            
    def correctize_include_guard(self):
        
        if self.__file_path.endswith(".h"):
            print("{} file checked with include guard".format(self.__file_path))
            
            # Normalized file name
            # TODO: Move to init
            file_name = os.path.basename(self.__file_path)
            file_name = file_name.split(".")[0]
            
            file_name = file_name.upper()
            header_text =  "{}_H_".format(file_name)
            
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
            
            new_file = "".join(self.__file)
            
            saved_last_line_index = -1
            
            for i, line in enumerate(self.__file):
                #new_line = line
                if not expected_guard1_ok and "#ifndef" in line:
                    if line == expected_guard1 + self.__CONFIG_NEWLINE_CHARS:
                        self.debug_print_ok("Guard1 was okay")
                    else:
                        # Replace
                        new_file = new_file.replace(line, expected_guard1 + self.__CONFIG_NEWLINE_CHARS)
                        guard_changed = True
                        
                    expected_guard1_ok = True
                    continue
                
                if not expected_guard2_ok and "#define" in line:
                    if line == expected_guard2 + self.__CONFIG_NEWLINE_CHARS:
                        self.debug_print_ok("Guard2 was okay")
                    else:
                        # Replace
                        new_file = new_file.replace(line, expected_guard2 + self.__CONFIG_NEWLINE_CHARS)
                        guard_changed = True
                        
                    expected_guard2_ok = True
                    continue
                
                if "#endif" in line:
                    # #endif shall be checked only if it is the last
                    saved_last_line_index = i

            # Finished, check the last line #endif
            if saved_last_line_index >= 0:
                line = self.__file[saved_last_line_index]
                if line == expected_guard3 + self.__CONFIG_NEWLINE_CHARS:
                    self.debug_print_ok("Guard3 was okay")
                else:
                    # Replace
                    new_file = new_file.replace(line, expected_guard3 + self.__CONFIG_NEWLINE_CHARS)
                    guard_changed = True
                    
                expected_guard3_ok = True
                
            
            if not (expected_guard1_ok and expected_guard2_ok and expected_guard3_ok):
                print("ERROR! Include guard error!")

            if guard_changed:
                print("Include guards changed")
                self.__new_file = new_file

        else:
            self.debug_print_ok("{} file not checked with include guard".format(self.__file_path))
    
        
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

        new_file = "".join(self.__file)

        file_changed = False
        for keyword_from, keyword_to in doxygen_keywords:
            if keyword_from in new_file:
                file_changed = True
                new_file = new_file.replace(keyword_from, keyword_to)
                
        if file_changed:
            print("{} file has changed by Doxygen keyword replace(s)".format(self.__file_path))
            self.__new_file = new_file

            
    def refactor_macro(self):
        # Refactor
        
        full_file = "".join(self.__file)
        
        #myRe = re.compile(r"(myFunc\(.+?\,.+?\,)(.+?)(\,.+?\,.+?\,.+?\,.+?\))")
        #print myRe.sub(r'\1"noversion"\3', val)
        # \1 means: 1. group
        regex_text_from = re.compile(r"([^_])MODULE_")
        file_new = regex_text_from.sub(r'\1CONFIG_MODULE_', full_file)

        
        """
        "// comment" --> /* comment */
        But do not change: "///<"
        And finished with // 
        """
        regex_text_from = re.compile(r"\/\/[^\/\<]([^\r\n]+)")
        file_new = regex_text_from.sub(r'/* \1 */', file_new)
        if file_new != full_file:
            self.__new_file = file_new
        


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
        
        # TODO: Move out from here
        # Rewrite file
        if file_analysis.CONFIG_CORRECTION_ENABLED:
            file_analysis.update_file()
    
    print("Finished")


if __name__ == "__main__":
    # execute only if run as a script
    run_checker(dir_path="Fasten\\**", dir_relative=True, recursive=True)


# TODO: Unittest for TAB
# TODO: Unittest for not tab (indent!)
