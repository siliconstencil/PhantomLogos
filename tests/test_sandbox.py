import os
import unittest

from src.utils.sandbox import LightSandbox


class TestLightSandbox(unittest.TestCase):
    def setUp(self):
        self.sandbox = LightSandbox()

    def tearDown(self):
        self.sandbox.cleanup()

    def test_basic_execution(self):
        stdout, stderr = self.sandbox.run("print('Hello World')")
        self.assertEqual(stdout.strip(), "Hello World")
        self.assertEqual(stderr, "")

    def test_timeout(self):
        stdout, stderr = self.sandbox.run("import time\nwhile True: time.sleep(1)", timeout_sec=2)
        self.assertIn("Error: Execution timed out.", stderr)

    def test_isolation_filesystem(self):
        # Test relative path isolation (should stay within temp_dir)
        code = """
import os
with open('test_local.txt', 'w') as f:
    f.write('inside')
print(f"FILE_EXISTS: {os.path.exists('test_local.txt')}")
"""
        stdout, stderr = self.sandbox.run(code)
        self.assertIn("FILE_EXISTS: True", stdout)
        # Verify it's not in the project root
        self.assertFalse(os.path.exists(os.path.join(os.getcwd(), "test_local.txt")))

    def test_env_stripping(self):
        code = """
import os
print(f"PATH_LEN: {len(os.environ.get('PATH', ''))}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'NOT_SET')}")
"""
        stdout, stderr = self.sandbox.run(code)
        # PYTHONPATH should be truly absent from env
        self.assertIn("PYTHONPATH: NOT_SET", stdout)

    def test_windows_dll_support(self):
        # Test if basic math (which might need some DLLs) works
        code = "import math\nprint(math.sqrt(16))"
        stdout, stderr = self.sandbox.run(code)
        self.assertEqual(stdout.strip(), "4.0")

    def test_absolute_path_block(self):
        code = "with open('C:/Windows/System32/drivers/etc/hosts', 'r') as f: print(f.read())"
        stdout, stderr = self.sandbox.run(code)
        self.assertIn("Error: Absolute paths or network shares are forbidden", stderr)


if __name__ == "__main__":
    unittest.main()
