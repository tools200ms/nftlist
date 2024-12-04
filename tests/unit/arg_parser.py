import io
import sys
import unittest
from contextlib import redirect_stdout

from nftlist import Nftlist  # Adjust the import path as necessary

class TestArgParser(unittest.TestCase):
    def test_main_function(self):
        cmd = sys.argv[0]
        """Test if Nftlist.main()."""
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                Nftlist.main([cmd, "help"])

            out1 = output.getvalue()
            self.assertIn("Command syntax:", out1)
            self.assertIn("refresh", out1)
            self.assertIn("clean", out1)
            self.assertIn("panic", out1)
            self.assertIn("--do_pretend", out1)
            self.assertIn("--verbose", out1)
            self.assertIn("--debug", out1)
            self.assertIn("--quiet", out1)
            self.assertIn("--help", out1)
            self.assertIn("--version", out1)

            output = io.StringIO()
            with redirect_stdout(output):
                Nftlist.main([cmd, "-h"])
            out2 = output.getvalue()
            self.assertEquals(out1, out2)

            output = io.StringIO()
            with redirect_stdout(output):
                Nftlist.main([cmd, "--version"])

            out1 = output.getvalue()
            self.assertIn("NFT List", out1)
            self.assertIn("by:", out1)

            output = io.StringIO()
            with redirect_stdout(output):
                Nftlist.main([cmd, "-v"])
            out2 = output.getvalue()
            self.assertEquals(out1, out2)

        except Exception as e:
            self.fail(f"Nftlist.main() raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
