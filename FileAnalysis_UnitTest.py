""" SourceCodeChecker - FileAnalysis UnitTest """

import unittest
import glob
import os
import shutil

import SourceCodeChecker


def copytree(src, dst, symlinks=False, ignore=None):
    # Solution from:
    # https://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


class TestFileAnalysisClass(unittest.TestCase):

    def test_checkers(self):

        SourceCodeChecker.LoadTestConfig()

        # Copy the test files, because it will be changed
        sources_from = "test" + os.sep + "Src" + os.sep
        sources_to = "test" + os.sep + "TestSrc" + os.sep
        # Remove + Copy
        if os.path.isdir(sources_to):
            shutil.rmtree(sources_to)
        # Create
        os.mkdir(sources_to)
        # Copy
        copytree(sources_from, sources_to)

        # Walk directories
        file_list = glob.glob(sources_to + "*.c")

        # Check test files
        for file_path in file_list:
            file_analysis = SourceCodeChecker.FileAnalysis(file_path)
            file_analysis.analyze()
            # file_analysis.print_issues() # Only for debug
            issues = file_analysis.get_text_of_issues()

            # Create test name from file name
            # Test result compare method:
            # 1. Check what there is after test_ --> test_name
            # 2. Check test_name is in the issue list?
            test_file_name_start = os.path.join(sources_to,"test_")
            if file_path.startswith(test_file_name_start):
                test_name = file_path[len(test_file_name_start):]
                test_name = test_name.split('_')[0].lower()
                # print(test_name) # Only for debug

                # Check file name and issue is same?
                assert test_name in issues.lower(), "{} test file has run in \"{}\" test, and generated issue: \"{}\"".format(file_path, test_name, issues)
            else:
                print("WARNING! Wrong test file name: \"{}\"".format(file_path))
            # print("{} test file has run successfully in {} test".format(file_path, test_name)) # Only for debug

        print("Run {} tests".format(len(file_list)))
        print("".join("  {}\n".format(test) for test in file_list))

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
        # TODO: List or full file?
        text = [
            "//blabla\r\n",
            "// blabla\r\n",
            "  //blabla\r\n",
            "  if (a) //blabla\r\n",
            "///< blabla\r\n"
            "http://blabla.com\r\n",
            " //* Blabla do not change me please\r\n",
            " /* blabla please realize, this is trick inline comment in another comment//bla */\r\n",
            " Please do not change me, I am link, http://blabla\r\n"
        ]

        text_expected_result = \
"""/* blabla */
/*  blabla */
  /* blabla */
  if (a) /* blabla */
///< blabla
http://blabla.com
 //* Blabla do not change me please
 /* blabla please realize, this is trick inline comment in another comment//bla */
 Please do not change me, I am link, http://blabla
"""

        file_analysis = SourceCodeChecker.FileAnalysis(file_path=None, test_text=text)

        file_analysis.run_refactor_comment()

        new_file = file_analysis.debug_get_new_file()

        print(new_file)

        # TODO: Old solution for test result checking, delete
        #assert(new_file.count("/*") == 4)
        self.assertEqual(text_expected_result.replace("\r","").replace("\n",""), new_file.replace("\r","").replace("\n",""))

    def test_refactor_notused_argument(self):

        # TODO: Change to multiline string
        text = \
        "(void)a;\r\n" \
        "(void) a;\r\n" \
        "(void)b_c;\r\n" \
        "(void) b_c;\r\n" \
        "\r\n" \
        "// Do not replace these:\r\n" \
        "blabla (void)a;\r\n"

        file_analysis = SourceCodeChecker.FileAnalysis(file_path=None, test_text=text)

        file_analysis.run_refactor_unused_argument()

        new_file = file_analysis.debug_get_new_file()

        print(new_file)

        assert(new_file.count("UNUSED_ARGUMENT") == 4)

    def test_statistics(self):

        # Save + set config
        global CONFIG_FILE_NAME
        original_config_file_name = SourceCodeChecker.CONFIG_FILE_NAME
        SourceCodeChecker.CONFIG_FILE_NAME = "test" + os.sep + "scc_config_test_statistics.json"

        test_statistics_file_path = "test" + os.sep + "StatisticsTestProject" + os.sep + "**"

        SourceCodeChecker.run_checker(dir_path=test_statistics_file_path, dir_relative=True, recursive=True)
        # 10 + 20 line count in the file
        self.assertEqual(30, SourceCodeChecker.STATISTICS_DATA.code_line_count)

        # Restore config
        SourceCodeChecker.CONFIG_FILE_NAME = original_config_file_name

if __name__ == '__main__':
    unittest.main()

