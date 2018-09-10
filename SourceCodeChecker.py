""" Source Code Checker """

import glob
import codecs


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

    __CONFIG_ASCII_CHECKER = False

    __CONFIG_NEWLINE_CHARS = "\r\n"

    __CONFIG_ENABLED_INDENT_NUM = 4


    def __init__(self, file_path):
        """ Read the file """

        self.__file_path = file_path
        self.__issues = []
        self.__new_file = []
        self.__file = []

        print("Check file: {}".format(file_path))

        #file = open(file_path,'rt')
        file = codecs.open(file_path, 'r', encoding=self.__CONFIG_ENCODE)

        # Read entire file
        try:
            # This is an check for ENCODE
            self.__file = file.readlines()
            #print("File encode is OK")
        except:
            self.add_issue(0, "Not {} encoded".format(self.__CONFIG_ENCODE))

        file.close()


    def analyze(self):

        if self.__CONFIG_ASCII_CHECKER:
            self.check_ASCII()

        self.check_newline()

        if not self.__CONFIG_TABS_ENABLED:
            self.check_tabs()

        if not self.__CONFIG_TABS_ENABLED:
            self.check_indent()

        self.check_trailing_whitespace()


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


    def check_ASCII(self):
        for i, line in enumerate(self.__file):
            for char in line:
                if char > 127:
                    self.add_issue(i, "There is a non-ASCII character!")
                    return False
        return True


    def check_newline(self):
        # Check every line has good newline? (and the last line too)
        for i, line in enumerate(self.__file):
            # Get last characters
            last_chars = line[-len(self.__CONFIG_NEWLINE_CHARS) : ]
            if last_chars != self.__CONFIG_NEWLINE_CHARS:
                self.add_issue(i, "There is a wrong newline in the file!")
                return False
        return True


    def correct_newline(self):
        # TODO: Imlement it. Shall rewrite the file, or only replace?
        pass


    def check_tabs(self):
        for i, line in enumerate(self.__file):
            if "\t" in line:
                self.add_issue(i, "There is a tabulator in the file!")
                return False
        return True


    def correct_tabs(self):
        pass
        # TODO: Implement:
        # 1. replace tabs --> spaces
        # 2. replace spaces --> tab, but only in leading


    def check_trailing_whitespace(self):
        for i, line in enumerate(self.__file):
            # Strip newline characters
            line = line.rstrip(self.__CONFIG_NEWLINE_CHARS)
            if line != line.rstrip():
                self.add_issue(i, "There is trailing whitespace!")
                return False
        return True


    def check_indent(self):
        for i, line in enumerate(self.__file):
            if self.__CONFIG_TABS_ENABLED:
                # Indent with tabs
                line_free_tab = line.lstrip('\t')
                if line_free_tab != line_free_tab.lstrip(' '):
                    self.add_issue(i, "Indent is wrong! (Space after tab)")
                    return False
            else:
                # Indent with spaces
                length_of_leading_spaces = len(line) - len(line.lstrip(' '))
                if (length_of_leading_spaces % self.__CONFIG_ENABLED_INDENT_NUM) != 0:
                    self.add_issue(i, "Indent is wrong! (Wrong number of spaces)")
                    return False
        return True


def run_checker(dir_path=".", dir_relative=True, file_types="*.c", checks=[], change_mode=False):
    print("Directory: {}\n" \
          "File types: {}".format(
              dir_path, file_types))

    # Walk directories
    file_list = glob.glob(dir_path + "\\" + file_types)

    # Check files
    for file_path in file_list:
        file_analysis = FileAnalysis(file_path)
        file_analysis.analyze()
        file_analysis.print_issues()


if __name__ == "__main__":
    # execute only if run as a script
    run_checker(dir_path="test\\Src", dir_relative=True)


# TODO: Unittest for TAB
# TODO: Unittest for not tab (indent!)
