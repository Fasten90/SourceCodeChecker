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


def helper_collect_test_files():
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
    return sources_to, file_list


class TestFileAnalysisClass(unittest.TestCase):

    def test_checkers(self):

        TEST_CONFIG_FILE = 'test\\scc_config_test.json'

        sources_to, file_list = helper_collect_test_files()

        # Configs
        file_analysis = SourceCodeChecker.Checker(file_path=TEST_CONFIG_FILE)

        # Check test files
        for file_path in file_list:
            # Load + check file
            file_analysis.load(file_path)
            file_analysis.analyze()
            # file_analysis.print_issues() # Only for debug
            issues = file_analysis.get_text_of_issues()

            # Create test name from file name
            # Test result compare method:
            # 1. Check what there is after test_ --> test_name
            # 2. Check test_name is in the issue list?
            test_file_name_start = os.path.join(sources_to, "test_")
            if file_path.startswith(test_file_name_start):
                test_name = file_path[len(test_file_name_start):]
                test_name = test_name.split('_')[0].lower()
                # print(test_name) # Only for debug

                # Check test type: _fail or _ok
                test_type = os.path.splitext(file_path)[0]
                if test_type.endswith("_fail"):
                    # Check file name and issue is same?
                    assert test_name in issues.lower(), "{} test file has run in \"{}\" test, and generated issues: \"{}\"".format(file_path, test_name, issues)
                elif test_type.endswith("_ok"):
                    # Check, test name is not in the issues()
                    assert test_name not in issues.lower(), "{} test file has run in \"{}\" test, and generated issues: \"{}\"".format(file_path, test_name, issues)
                else:
                    raise Exception("Wrong test file name")
            else:
                print("WARNING! Wrong test file name: \"{}\"".format(file_path))
            # print("{} test file has run successfully in {} test".format(file_path, test_name)) # Only for debug

        print("Run {} tests".format(len(file_list)))
        print("".join("  {}\n".format(test) for test in file_list))


    def test_default_config(self):
        global CONFIG_FILE_NAME
        # Prepare the config
        original_config_name = SourceCodeChecker.CONFIG_FILE_DEFAULT_NAME
        temporary_configname = SourceCodeChecker.CONFIG_FILE_DEFAULT_NAME + "_temp"

        # Prepare: Delete the temp if need
        if os.path.exists(temporary_configname):
            os.remove(temporary_configname)

        # Rename original if need
        if os.path.exists(original_config_name):
            os.rename(original_config_name, temporary_configname)

        # Crosscheck to is it moved correctly?
        assert(not os.path.exists(original_config_name))

        # SourceCodeChecker.CONFIG_FILE_NAME = temporary_configname
        # make Analysis for checking, did it create the config?
        file_analysis = SourceCodeChecker.Checker(original_config_name)
        #file_analysis.load() # Not used because only the init shall executed

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

        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=text)

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

        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=text)

        file_analysis.run_refactor_unused_argument()

        new_file = file_analysis.debug_get_new_file()

        print(new_file)

        assert(new_file.count("UNUSED_ARGUMENT") == 4)


    def test_statistics(self):

        test_config_file = 'test/scc_config_test_statistics.json'

        test_statistics_file_path = "test" + os.sep + "StatisticsTestProject" + os.sep + "**"
        SourceCodeChecker.source_code_checker(source_paths=test_statistics_file_path,
                                              file_types='*.[c|h]',
                                              config_file_path=test_config_file,
                                              recursive=True)
        # 11 + 21 line count in the file
        self.assertEqual(32, SourceCodeChecker.STATISTICS_DATA.code_line_count)


    def test_function_description(self):

        test_code = \
"""
  /**
 * @doxygen   blabla1
  *          blabla2
 * @doxygen2 blabla3
 *          blabla4
     */
void do_not_touch();
"""
        expected = \
"""
/**
 * @doxygen     blabla1
 *              blabla2
 * @doxygen2    blabla3
 *              blabla4
 */
void do_not_touch();
"""
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)

        file_analysis.run_refactor_function_description_comment()

        new__file = file_analysis.debug_get_new_file()
        # TODO: Modify the test
        new__file = new__file.replace("\r\n", "\n")
        self.assertEqual(expected, new__file)


    # TODO: Test
    #  Implement newline
    #  trailing whitespace correctizer
    #  TAB
    #  not tab (indent!)


    def test_check_newline_false(self):
        test_code = """bla\nbla2\n"""  # wrong
        expected_update_code = """bla\r\nbla2\r\n"""
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)
        file_analysis.debug_set_correctize_enabled()  # Special

        res = file_analysis.check_newline()

        self.assertFalse(res)

        # correct_newline
        new_file = file_analysis.debug_get_new_file()
        self.assertEqual(expected_update_code, new_file)


    def test_check_newline_OK(self):
        test_code = """bla\r\nbla2\r\n"""
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)

        res = file_analysis.check_newline()

        self.assertTrue(res)


    def test_check_trailing_whitespace_false(self):
        test_code = """bla  \r\nbla2\r\n"""  # wrong
        expected_update_code = """bla\r\nbla2\r\n"""
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)
        file_analysis.debug_set_correctize_enabled()  # Special

        res = file_analysis.check_trailing_whitespace()

        self.assertFalse(res)

        # correct_trailing_whitespace
        new_file = file_analysis.debug_get_new_file()
        self.assertEqual(expected_update_code, new_file)


    def test_check_trailing_whitespace_OK(self):
        test_code = """bla\r\nbla2\r\n"""
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)

        res = file_analysis.check_trailing_whitespace()

        self.assertTrue(res)


    def test_check_tabs_false(self):
        test_code = """\t \tExtremely mixed tabs bla\r\nbla2\r\n"""  # wrong
        expected_update_code = [ '         Extremely mixed tabs bla\r\n', 'bla2\r\n' ]
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)
        file_analysis.debug_set_correctize_enabled()  # Special

        res = file_analysis.check_tabs()

        self.assertFalse(res)

        # correction
        new_file = file_analysis.debug_get_new_file()
        self.assertEqual(new_file, expected_update_code)


    def test_check_tabs_OK(self):
        # TODO: Maybe the default case is the tabs disabled?
        # test_code = """\t\tbla\r\nbla2\r\n"""
        test_code = """        bla\r\nbla2\r\n"""
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)

        res = file_analysis.check_tabs()

        self.assertTrue(res)


    def test_check_indent_false(self):
        test_code = """   Extremely wrong indent bla\r\nbla2\r\n"""  # wrong
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)
        file_analysis.debug_set_correctize_enabled()  # Special

        res = file_analysis.check_indent()

        self.assertFalse(res)

        # No correction


    def test_check_indent_OK(self):
        test_code = """    bla\r\nbla2\r\n"""
        file_analysis = SourceCodeChecker.Checker()
        file_analysis.load(file_path=None, test_text=test_code)

        res = file_analysis.check_indent()

        self.assertTrue(res)


    #def test_correctize(self):
    #    file_analysis = SourceCodeChecker.Checker()
    #    file_analysis.load(file_path=None, test_text=test_code)

    #    res = file_analysis.check_newline()

    #    new__file = file_analysis.debug_get_new_file()
    #    new__file = new__file.replace("\r\n", "\n")
    #    self.assertEqual(expected, new__file)


    def test_existing_config_full_enabled(self):
        test_config_file = 'scc_config_full_enabled.json'

        source_to, file_list = helper_collect_test_files()

        # Check test files
        for file_path in file_list:
            file_analysis = SourceCodeChecker.Checker(test_config_file)
            file_analysis.load(file_path)
            file_analysis.analyze()
            # file_analysis.print_issues() # Only for debug
            issues = file_analysis.get_text_of_issues()


    def test_existing_config_full_disabled(self):
        test_config_file = 'scc_config_full_disabled.json'

        source_to, file_list = helper_collect_test_files()

        # Check test files
        for file_path in file_list:
            file_analysis = SourceCodeChecker.Checker(test_config_file)
            file_analysis.load(file_path)
            file_analysis.analyze()
            # file_analysis.print_issues() # Only for debug
            issues = file_analysis.get_text_of_issues()


if __name__ == '__main__':
    unittest.main()

