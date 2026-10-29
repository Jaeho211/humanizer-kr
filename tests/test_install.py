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
            self.assertEqual(backups, [])

    def test_removes_only_previous_installer_backups(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            self.run_installer(home)
            target = home / ".omp/agent/skills/humanizer-kr"
            old = target.parent / "humanizer-kr.bak.20261029105201"
            old.mkdir()
            (old / "SKILL.md").write_text("---\nname: humanizer-kr\n---\n")
            unrelated = target.parent / "humanizer-kr.bak.20261029105202"
            unrelated.mkdir()
            (unrelated / "SKILL.md").write_text("---\nname: other-skill\n---\n")
            manual = target.parent / "humanizer-kr.bak.manual"
            manual.mkdir()
            (manual / "SKILL.md").write_text("---\nname: humanizer-kr\n---\n")
            output = self.run_installer(home)
            self.assertIn("REMOVE OLD BACKUP:", output)
            self.assertFalse(old.exists())
            self.assertTrue(unrelated.exists())
            self.assertTrue(manual.exists())

    def test_dry_run_preserves_backups(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            self.run_installer(home)
            target = home / ".omp/agent/skills/humanizer-kr"
            old = target.parent / "humanizer-kr.bak.20261029105201"
            old.mkdir()
            (old / "SKILL.md").write_text("---\nname: humanizer-kr\n---\n")
            output = self.run_installer(home, "--dry-run")
            self.assertIn("REMOVE OLD BACKUP:", output)
            self.assertTrue(old.exists())

    def test_symlink_backups_and_project_targets(self):
        with tempfile.TemporaryDirectory() as td:
            home = Path(td)
            project = home / "project"
            project.mkdir()
            self.run_installer(home, "--scope", "project", "--project", str(project))
            target = project / ".agents/skills/humanizer-kr"
            self.assertTrue((target / "SKILL.md").exists())
            old = target.parent / "humanizer-kr.bak.20261029105201"
            old.symlink_to(ROOT / "skills/humanizer-kr", target_is_directory=True)
            self.run_installer(home, "--scope", "project", "--project", str(project))
            self.assertFalse(old.exists())


if __name__ == "__main__":
    unittest.main()
