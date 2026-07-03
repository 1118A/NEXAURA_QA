import unittest
from pathlib import Path
from app.models.schemas import CodeFile
from app.services.parser_service import ParserService
from app.services.git_service import GitService

class TestParserService(unittest.TestCase):
    def setUp(self):
        self.parser_service = ParserService()

    def test_detect_language(self):
        self.assertEqual(self.parser_service.detect_language(".py"), "python")
        self.assertEqual(self.parser_service.detect_language(".js"), "javascript")
        self.assertEqual(self.parser_service.detect_language(".tsx"), "typescript")
        self.assertEqual(self.parser_service.detect_language(".txt"), "unknown")

    def test_split_lines_to_sub_chunks(self):
        lines = ["line 1", "line 2", "line 3", "line 4"]
        # If max_chars is small (e.g. 15 characters, including newlines), lines should split
        # line 1 is 6 chars + 1 = 7. line 2 is 6 chars + 1 = 7. Sum = 14 <= 15.
        # line 3 is 6 chars + 1 = 7. Sum with next would exceed 15.
        sub_blocks = self.parser_service.split_lines_to_sub_chunks(lines, 1, 15)
        self.assertEqual(len(sub_blocks), 2)
        self.assertEqual(sub_blocks[0][0], "line 1\nline 2")
        self.assertEqual(sub_blocks[0][1], 1)
        self.assertEqual(sub_blocks[0][2], 2)
        self.assertEqual(sub_blocks[1][0], "line 3\nline 4")

    def test_python_parsing(self):
        code = """def my_function():
    print("hello")

class MyClass:
    def my_method(self):
        pass
"""
        code_file = CodeFile(
            file_path="mock.py",
            relative_path="mock.py",
            content=code,
            extension=".py"
        )
        
        chunks = self.parser_service.parse_code_file(code_file, max_chunk_chars=100)
        # Should have parsed function, class, and the method inside class
        self.assertTrue(len(chunks) >= 2)
        
        # Verify metadata is loaded
        types = [c.symbol_type for c in chunks]
        self.assertIn("function", types)
        self.assertIn("class", types)

class TestGitService(unittest.TestCase):
    def test_get_repo_name(self):
        git_service = GitService()
        self.assertEqual(git_service.get_repo_name("https://github.com/octocat/Spoon-Knife"), "Spoon-Knife")
        self.assertEqual(git_service.get_repo_name("https://github.com/psf/requests.git"), "requests")
        self.assertEqual(git_service.get_repo_name("https://github.com/django/django/"), "django")

if __name__ == "__main__":
    unittest.main()
