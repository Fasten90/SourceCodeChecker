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
    __CONFIG_TABS_CHECKER_ENABLED = False

    __CONFIG_ASCII_CHECKER_ENABLED = False

    __CONFIG_NEWLINE_CHECKER_ENABLED = False
    __CONFIG_NEWLINE_CHARS = "\r\n"

    __CONFIG_INDENT_SPACE_NUM = 4
    __CONFIG_INDENT_CHECKER_IS_ENABLED = False

    __CONFIG_TAB_SPACE_SIZE = 4
    
    __CONFIG_TRAILING_WHITESPACE_CHECKER_ENABLED = False
    
    # TODO: Add "until one error" / "check all file" mode
    __CONFIG_UNTIL_FIRST_ERROR = False
    
    CONFIG_CORRECTION_ENABLED = True


    def __init__(self, file_path):
        """ Read the file """

        self.__file_path = file_path
        self.__issues = []
        self.__new_file = []
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
        file = codecs.open(self.__file_path, 'w', encoding=self.__CONFIG_ENCODE)
        file.writelines(self.__file)
        file.close() 
        print("Updated file: {}".format(self.__file_path))


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
            self.__file = new_file
                    
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


if __name__ == "__main__":
    # execute only if run as a script
    run_checker(dir_path="test\\Src\\**", dir_relative=True, recursive=True)


# TODO: Unittest for TAB
# TODO: Unittest for not tab (indent!)
