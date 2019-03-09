""" SourceCodeChecker - FileAnalysis UnitTest """

import unittest
import glob

import SourceCodeChecker


class TestFileAnalysisClass(unittest.TestCase):

    def test_1(self):
        # Walk directories
        file_list = glob.glob("test\\Src\\*.c")
    
        # Check test files
        for file_path in file_list:
            file_analysis = SourceCodeChecker.FileAnalysis(file_path)
            file_analysis.analyze()
            #file_analysis.print_issues() # Only for debug
            issues = file_analysis.get_text_of_issues()
            
            # Create test name from file name
            #file_path.split
            test_file_name_start = "test\\Src\\test_"
            if file_path.startswith(test_file_name_start):
                test_name = file_path[len(test_file_name_start):]
                test_name = test_name.split('_')[0]
                #print(test_name) # Only for debug

            # Check file name and issue is same?
            assert test_name in issues.lower(), "{} test file has run in {} test, and generated issue: \"{}\"".format(file_path, test_name, issues)
            #print("{} test file has run successfully in {} test".format(file_path, test_name)) # Only for debug

    
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

