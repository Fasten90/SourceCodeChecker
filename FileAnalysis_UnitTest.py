""" SourceCodeChecker - FileAnalysis UnitTest """

import unittest
import glob
import os

import SourceCodeChecker


class TestFileAnalysisClass(unittest.TestCase):

    def test_checkers(self):

        global CONFIG_FILE_NAME
        # Prepare the config
        original_config_name = SourceCodeChecker.CONFIG_FILE_NAME

        test_config_name = "test\\scc_config_test.json"

        SourceCodeChecker.CONFIG_FILE_NAME = test_config_name

        # Walk directories
        file_list = glob.glob("test\\Src\\*.c")

        # Check test files
        for file_path in file_list:
            file_analysis = SourceCodeChecker.FileAnalysis(file_path)
            file_analysis.analyze()
            # file_analysis.print_issues() # Only for debug
            issues = file_analysis.get_text_of_issues()

            # Create test name from file name
            # file_path.split
            test_file_name_start = "test\\Src\\test_"
            if file_path.startswith(test_file_name_start):
                test_name = file_path[len(test_file_name_start):]
                test_name = test_name.split('_')[0].lower()
                # print(test_name) # Only for debug

            # Check file name and issue is same?
            assert test_name in issues.lower(), "{} test file has run in \"{}\" test, and generated issue: \"{}\"".format(file_path, test_name, issues)
            # print("{} test file has run successfully in {} test".format(file_path, test_name)) # Only for debug

        # End of test
        SourceCodeChecker.CONFIG_FILE_NAME = original_config_name

    def test_default_config(self):
        global CONFIG_FILE_NAME
        # Prepare the config
        original_config_name = SourceCodeChecker.CONFIG_FILE_NAME
        temporary_configname = SourceCodeChecker.CONFIG_FILE_NAME + "_temp"

        # Prepare: Delete the temp if need
        if os.path.exists(temporary_configname):
            os.remove(temporary_configname)

        # Rename original if need
        if os.path.exists(original_config_name):
            os.rename(original_config_name, temporary_configname)

        assert(not os.path.exists(original_config_name))

        # SourceCodeChecker.CONFIG_FILE_NAME = temporary_configname
        # make Analysis for checking, did it create the config?
        SourceCodeChecker.FileAnalysis(None)

        # Shall exists
        assert(os.path.exists(original_config_name))

        # Reset
        if os.path.exists(temporary_configname):
            os.remove(original_config_name)  # This is the default file. Could be deleted
            os.rename(temporary_configname, original_config_name)
        # End

    def test_refactor_comment(self):
        text = \
        "//blabla\r\n" \
        "// blabla\r\n" \
        "  //blabla\r\n" \
        "  if (a) //blabla\r\n" \
        "///< blabla\r\n"

        file_analysis = SourceCodeChecker.FileAnalysis(file_path=None, test_text=text)

        file_analysis.run_refactor()

        new_file = file_analysis.debug_get_new_file()

        print(new_file)

        assert(new_file.count("/*") == 4)

    def test_refactor_notused_argument(self):
        text = \
        "(void)a;\r\n" \
        "(void) a;\r\n" \
        "(void)b_c;\r\n" \
        "(void) b_c;\r\n" \
        "\r\n" \
        "// Do not replace these:\r\n" \
        "blabla (void)a;\r\n"

        file_analysis = SourceCodeChecker.FileAnalysis(file_path=None, test_text=text)

        file_analysis.run_refactor()

        new_file = file_analysis.debug_get_new_file()

        print(new_file)

        assert(new_file.count("UNUSED_ARGUMENT") == 4)


if __name__ == '__main__':
    unittest.main()

