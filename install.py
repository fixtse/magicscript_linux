"""Stage, validate and atomically activate a personal MagicScript Linux release."""
import argparse
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import uuid

from browser_port import BROWSER_COMMAND, RESOLVE_BROWSER, desktop_entry, prepare_browser

FILES = ('install.py', 'release.json', 'no-streamdeck.patch', 'guide-linux.patch',
         'ai-skills.patch', 'magicscript_skills.py', 'browser_port.py',
         'browser/catalogue-linux.patch', 'browser/window-button.patch', 'browser/renderer-linux.patch',
         'browser/dist/main.js', 'browser/dist/linux-update.js')
UPDATER = '''#!/usr/bin/env bash
set -euo pipefail
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
curl --fail --location --retry 3 https://raw.githubusercontent.com/fixtse/magicscript_linux/main/install.sh -o "$work/install.sh"
bash "$work/install.sh" "$@"
'''
LAUNCHER = '''# Unofficial Linux launcher for MagicScript. Original notices remain in the app.
import os
import traceback
from pathlib import Path

try:
    # Resolve the immutable release once so an update cannot mix engine versions.
    app = (Path.home() / ".local/share/magicscript-linux/current").resolve(strict=True)
    os.environ["MAGICSCRIPT_APP"] = str(app)
    os.environ["MAGICSCRIPT_SEED"] = "1"
    entry = app / "MagicScript.py"
    namespace = dict(globals(), __file__=str(entry), __name__="__main__")
    exec(compile(entry.read_text(encoding="utf-8"), str(entry), "exec"), namespace)
except Exception:
    print("MagicScript Linux: failed to open the catalogue")
    traceback.print_exc()
'''
SERVICE = '''[Unit]
Description=Update the unofficial MagicScript Linux installation

[Service]
Type=oneshot
ExecStart=%h/.local/bin/magicscript-update --no-auto-update
'''
TIMER = '''[Unit]
Description=Check for MagicScript Linux updates daily

[Timer]
OnCalendar=daily
RandomizedDelaySec=30m
Persistent=true

[Install]
WantedBy=timers.target
'''


def atomic_write(path, content, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.magicscript-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(content)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def snapshot(path):
    if path.is_symlink():
        return ('link', os.readlink(path), None)
    if path.exists():
        if not path.is_file():
            raise RuntimeError(f'Refusing to replace a directory: {path}')
        return ('file', path.read_bytes(), path.stat().st_mode & 0o777)
    return ('missing', None, None)


def restore(path, state):
    if snapshot(path) == state:
        return
    kind, content, mode = state
    if kind == 'file':
        atomic_write(path, content, mode)
    elif kind == 'link':
        switch_link(path, content)
    else:
        path.unlink(missing_ok=True)


def switch_link(path, target):
    temporary = path.with_name('.current-' + uuid.uuid4().hex)
    try:
        temporary.symlink_to(target)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def prepare(source, stage, bundle, version):
    shutil.copytree(source, stage, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('._*', '__pycache__', 'streamdeck', 'magicscript_streamdeck.py'))
    main = stage / 'MagicScript.py'
    text = main.read_text(encoding='utf-8')
    old = '    return "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"'
    if text.count(old) != 1:
        raise RuntimeError('Unsupported engine: LUT path anchor changed.')
    text = text.replace(old, '    return "/opt/resolve/LUT" if sys.platform.startswith("linux") else "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"')
    needle = '    else:\n        roots.append("/Applications/DaVinci Resolve/'
    if text.count(needle) != 1:
        raise RuntimeError('Unsupported engine: template path anchor changed.')
    text = text.replace(needle, '''    elif sys.platform.startswith("linux"):
        roots.extend([
            "/opt/resolve/Fusion/Templates/Templates.drfx",
            "/opt/resolve/Fusion/Templates/Edit",
            os.path.expanduser("~/.local/share/DaVinciResolve/Fusion/Templates/Edit"),
        ])
    else:
        roots.append("/Applications/DaVinci Resolve/''')
    main.write_text(text, encoding='utf-8')
    for patch_name, target in (('no-streamdeck.patch', main),
                               ('guide-linux.patch', stage / 'MAGICSCRIPT.md'),
                               ('ai-skills.patch', main)):
        with (bundle / patch_name).open() as patch:
            subprocess.run(['patch', '--batch', '--forward', '--fuzz=0', str(target)], stdin=patch, check=True)
    guide = stage / 'MAGICSCRIPT.md'
    guide.write_text(guide.read_text(encoding='utf-8').replace(
        '~/.local/share/magicscript-linux/1.2.3', '~/.local/share/magicscript-linux/current'), encoding='utf-8')
    with guide.open('a', encoding='utf-8') as stream:
        stream.write("\n## Linux Browser\n\nOpen the Browser button in MagicScript, Workspace > Scripts > Utility > MagicScript Browser,\nor the Linux application menu. The standalone Electron Browser installs catalogue scripts into\nthe same personal scripts folder; press Reload in MagicScript afterwards. It does not run scripts.\nCommand: `~/.local/bin/magicscript-browser`. It uses your system Electron runtime and the\ninstalled Python validator; signed catalogue and script hash checks remain enabled.\n")
    shutil.copy2(bundle / 'magicscript_skills.py', stage / 'magicscript_skills.py')
    for path in stage.rglob('*.py'):
        ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
    # The upstream validator imports scripts but does not run run(ctx).
    subprocess.run(['python3', str(stage / 'validate_scripts.py')], check=True,
                   stdout=subprocess.DEVNULL)
    with (bundle / 'browser/window-button.patch').open() as patch:
        subprocess.run(['patch', '--batch', '--forward', '--fuzz=0', str(main)], stdin=patch, check=True)
    ast.parse(main.read_text(encoding='utf-8'))
    prepare_browser(source, stage, bundle)
    ast.parse(LAUNCHER)


def systemctl(*args, check=True):
    return subprocess.run(['systemctl', '--user', *args], check=check,
                          capture_output=True, text=True)


def install(source, bundle, home, auto_update=True):
    root = home / '.local/share/magicscript-linux'
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.update.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('Another MagicScript update is in progress.') from exc
        return install_locked(source, bundle, home, root, auto_update)


def install_locked(source, bundle, home, root, auto_update):
    release = json.loads((bundle / 'release.json').read_text())
    fingerprint = hashlib.sha256(b''.join((bundle / name).read_bytes() for name in FILES)).hexdigest()
    current = root / 'current'
    launcher = home / '.local/share/DaVinciResolve/Fusion/Scripts/Utility/MagicScript.py'
    updater = home / '.local/bin/magicscript-update'
    units = home / '.config/systemd/user'
    service, timer = units / 'magicscript-update.service', units / 'magicscript-update.timer'
    browser_command = home / '.local/bin/magicscript-browser'
    browser_launcher = launcher.with_name('MagicScript Browser.py')
    desktop = home / '.local/share/applications/magicscript-browser.desktop'
    receipt = current / '.linux-install.json'
    up_to_date = receipt.is_file() and json.loads(receipt.read_text()).get('fingerprint') == fingerprint
    if launcher.exists() and 'MagicScript loader' not in launcher.read_text() and 'Unofficial Linux launcher for MagicScript' not in launcher.read_text():
        raise RuntimeError(f'Refusing to replace an unrecognized launcher: {launcher}')
    if current.exists() and not current.is_symlink():
        raise RuntimeError(f'Expected a managed symlink at {current}; leaving it unchanged.')
    can_schedule = auto_update and shutil.which('systemctl') and systemctl('show-environment', check=False).returncode == 0
    paths = [current, launcher, updater, browser_command, browser_launcher, desktop] + ([service, timer] if can_schedule else [])
    backups = {path: snapshot(path) for path in paths}
    was_enabled = can_schedule and systemctl('is-enabled', 'magicscript-update.timer', check=False).returncode == 0
    was_active = can_schedule and systemctl('is-active', 'magicscript-update.timer', check=False).returncode == 0
    stage = None
    committed = False
    try:
        if not up_to_date:
            releases = root / 'releases'
            releases.mkdir(exist_ok=True)
            stage = Path(tempfile.mkdtemp(prefix=release['version'] + '-', dir=releases))
            prepare(source, stage, bundle, release['version'])
            (stage / '.linux-install.json').write_text(json.dumps({'version': release['version'], 'fingerprint': fingerprint}))
        if stage:
            switch_link(current, str(stage.relative_to(root)))
        atomic_write(launcher, LAUNCHER.encode())
        atomic_write(updater, UPDATER.encode(), 0o755)
        atomic_write(browser_command, BROWSER_COMMAND.encode(), 0o755)
        atomic_write(browser_launcher, RESOLVE_BROWSER.encode())
        atomic_write(desktop, desktop_entry(home).encode())
        if can_schedule:
            atomic_write(service, SERVICE.encode())
            atomic_write(timer, TIMER.encode())
            systemctl('daemon-reload')
            systemctl('enable', '--now', 'magicscript-update.timer')
        committed = True
    except BaseException:
        errors = []
        for path in reversed(paths):
            try:
                restore(path, backups[path])
            except Exception as exc:
                errors.append(f'{path}: {exc}')
        if can_schedule:
            if not was_active:
                systemctl('stop', 'magicscript-update.timer', check=False)
            if not was_enabled:
                systemctl('disable', 'magicscript-update.timer', check=False)
            systemctl('daemon-reload', check=False)
        if errors:
            raise RuntimeError('Rollback needs attention: ' + '; '.join(errors))
        print('Update failed. Previous installation restored; personal scripts and settings were untouched.')
        raise
    finally:
        if stage and not committed:
            shutil.rmtree(stage)
    print(('Already up to date: ' if up_to_date else 'Installed/updated: ') + release['version'])
    print(f'Launcher: {launcher}\nBrowser: {browser_command}\nUpdate command: {updater}')
    if can_schedule:
        print('Automatic updates: daily user timer enabled (with up to 30 minutes random delay).')
    elif auto_update:
        print('No running systemd user manager: automatic scheduling unavailable. Run magicscript-update manually.')
    print('Close and reopen MagicScript to use the active release.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--no-auto-update', action='store_true', help='Do not create/enable the daily user timer.')
    args = parser.parse_args()
    # Convert a normal termination into an exception so transaction rollback runs.
    def terminate(signum, frame):
        raise KeyboardInterrupt('Installation interrupted')
    signal.signal(signal.SIGTERM, terminate)
    install(args.source, Path(__file__).resolve().parent, Path.home(), not args.no_auto_update)


if __name__ == '__main__':
    main()
