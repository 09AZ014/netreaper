import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parent.parent))

import netreaper


class TestBootstrap(unittest.TestCase):
    def test_get_project_venv_python_uses_workspace_virtualenv(self):
        project_root = Path("/tmp/example-project")
        self.assertEqual(
            netreaper.get_project_venv_python(project_root),
            Path("/tmp/example-project/.venv/bin/python"),
        )


if __name__ == "__main__":
    unittest.main()
