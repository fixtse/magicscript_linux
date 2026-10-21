"""Transaction checks; no network, Resolve, or real user settings required."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

BUNDLE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('installer', BUNDLE / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def prepare_stub(source, stage, bundle, version):
    (stage / 'MagicScript.py').write_text('# validated engine\n')


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / '.local/share/magicscript-linux'
        self.launcher = self.home / '.local/share/DaVinciResolve/Fusion/Scripts/Utility/MagicScript.py'
        self.personal = self.home / '.local/share/DaVinciResolve/MagicScript/state.json'
        self.personal.parent.mkdir(parents=True)
        self.personal.write_text('my settings')

    def install(self):
        with patch.object(installer, 'prepare', side_effect=prepare_stub):
            installer.install(Path('/unused'), BUNDLE, self.home, auto_update=False)

    def test_repeat_install_preserves_engine_and_personal_data(self):
        self.install()
        active = (self.root / 'current').resolve()
        self.install()
        self.assertEqual((self.root / 'current').resolve(), active)
        self.assertEqual(self.personal.read_text(), 'my settings')
        self.assertTrue((self.home / '.local/bin/magicscript-update').stat().st_mode & 0o111)

    def test_prepare_failure_leaves_legacy_installation_untouched(self):
        legacy = self.root / '1.2.3'
        legacy.mkdir(parents=True)
        (legacy / 'MagicScript.py').write_text('old engine')
        self.launcher.parent.mkdir(parents=True)
        self.launcher.write_text('# Unofficial Linux launcher for MagicScript\nold launcher')
        with patch.object(installer, 'prepare', side_effect=RuntimeError('patch failed')):
            with self.assertRaisesRegex(RuntimeError, 'patch failed'):
                installer.install(Path('/unused'), BUNDLE, self.home, False)
        self.assertEqual(self.launcher.read_text(), '# Unofficial Linux launcher for MagicScript\nold launcher')
        self.assertEqual((legacy / 'MagicScript.py').read_text(), 'old engine')
        self.assertFalse((self.root / 'current').exists())
        self.assertEqual(list((self.root / 'releases').iterdir()), [])
        self.assertEqual(self.personal.read_text(), 'my settings')

    def test_activation_failure_restores_previous_release_and_launcher(self):
        self.install()
        old_target = (self.root / 'current').readlink()
        old_launcher = self.launcher.read_bytes()
        receipt = self.root / 'current/.linux-install.json'
        receipt.write_text('{"fingerprint":"previous-release"}')
        original_write = installer.atomic_write
        def fail_updater(path, content, mode=0o644):
            if path.name == 'magicscript-update' and content == installer.UPDATER.encode():
                raise OSError('simulated write failure')
            original_write(path, content, mode)
        with patch.object(installer, 'prepare', side_effect=prepare_stub), patch.object(installer, 'atomic_write', side_effect=fail_updater):
            with self.assertRaises(OSError):
                installer.install(Path('/unused'), BUNDLE, self.home, False)
        self.assertEqual((self.root / 'current').readlink(), old_target)
        self.assertEqual(self.launcher.read_bytes(), old_launcher)
        self.assertEqual(len(list((self.root / 'releases').iterdir())), 1)

    def test_scheduler_failure_rolls_back_after_switch(self):
        self.install()
        old_target = (self.root / 'current').readlink()
        (self.root / 'current/.linux-install.json').write_text('{"fingerprint":"old"}')
        def fake_systemctl(*args, check=True):
            if args[0] == 'enable':
                raise subprocess.CalledProcessError(1, args)
            code = 1 if args[0] in ('is-active', 'is-enabled') else 0
            return subprocess.CompletedProcess(args, code)
        with patch.object(installer, 'prepare', side_effect=prepare_stub), patch.object(installer.shutil, 'which', return_value='/usr/bin/systemctl'), patch.object(installer, 'systemctl', side_effect=fake_systemctl):
            with self.assertRaises(subprocess.CalledProcessError):
                installer.install(Path('/unused'), BUNDLE, self.home, True)
        self.assertEqual((self.root / 'current').readlink(), old_target)
        self.assertFalse((self.home / '.config/systemd/user/magicscript-update.timer').exists())
        self.assertEqual(len(list((self.root / 'releases').iterdir())), 1)

    def test_unrecognized_launcher_is_preserved(self):
        self.launcher.parent.mkdir(parents=True)
        self.launcher.write_text('my own launcher')
        with self.assertRaisesRegex(RuntimeError, 'unrecognized'):
            self.install()
        self.assertEqual(self.launcher.read_text(), 'my own launcher')


if __name__ == '__main__':
    unittest.main()
