import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TestInstall(unittest.TestCase):
    def run_installer(self, home, *args):
        env = dict(os.environ, HOME=str(home))
        return subprocess.run(["bash", "install.sh", *args], cwd=ROOT,
                              env=env, check=True, capture_output=True, text=True).stdout

    def test_no_ide_install_target(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            output = self.run_installer(home, "--dry-run")
            self.assertNotIn(".gemini/config/skills", output)
            self.assertIn(".gemini/antigravity-cli/skills/humanizer-kr", output)
            self.assertEqual(output.count("INSTALL (copy):"), 4)
            self.assertEqual(list(home.iterdir()), [])

    def test_one_command_installs_and_updates(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            targets = [
                home / ".omp/agent/skills/humanizer-kr",
                home / ".gemini/antigravity-cli/skills/humanizer-kr",
                home / ".codex/skills/humanizer-kr",
                home / ".claude/skills/humanizer-kr",
            ]
            self.run_installer(home)
            for target in targets:
                self.assertTrue((target / "SKILL.md").exists())
            self.assertFalse((home / ".gemini/config/skills/humanizer-kr").exists())
            self.assertEqual(self.run_installer(home).count("UP-TO-DATE:"), 4)
            marker = targets[0] / "SKILL.md"
            marker.write_text("modified\n")
            self.run_installer(home)
            self.assertNotEqual(marker.read_text(), "modified\n")
            backups = list(targets[0].parent.glob("humanizer-kr.bak.*"))
            self.assertEqual(len(backups), 1)
            self.assertEqual((backups[0] / "SKILL.md").read_text(), "modified\n")

if __name__ == "__main__":
    unittest.main()
