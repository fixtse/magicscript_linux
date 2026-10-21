"""Adapt the publisher's Browser assets to a standalone Linux Electron host."""
import json
import os
from pathlib import Path
import shutil
import subprocess

BROWSER_COMMAND = '''#!/usr/bin/env bash
set -euo pipefail
app=$(readlink -f "$HOME/.local/share/magicscript-linux/current")
export MAGICSCRIPT_APP="$app"
unset ELECTRON_RUN_AS_NODE
# Resolve's private Qt/GL libraries must not override the system Electron runtime.
unset LD_LIBRARY_PATH LD_PRELOAD QT_PLUGIN_PATH QT_QPA_PLATFORM_PLUGIN_PATH
runtime=${ELECTRON_BIN:-}
if [[ -z "$runtime" ]]; then
    for name in electron electron45 electron44 electron43 electron42 electron41 electron40 electron39; do
        if command -v "$name" >/dev/null; then runtime=$(command -v "$name"); break; fi
    done
fi
if [[ -z "$runtime" ]]; then
    echo 'MagicScript Browser needs a Linux Electron runtime. Install electron with your package manager, or set ELECTRON_BIN to its executable.' >&2
    exit 1
fi
exec "$runtime" "$app/browser" "$@"
'''
RESOLVE_BROWSER = '''# MagicScript Browser — standalone Linux host for MrAlexTech's original Browser.
import os
import subprocess
import traceback

try:
    subprocess.Popen([os.path.expanduser("~/.local/bin/magicscript-browser")], start_new_session=True)
except Exception:
    print("Could not launch MagicScript Browser. Try ~/.local/bin/magicscript-browser in a terminal.")
    traceback.print_exc()
'''


def electron_runtime():
    custom = os.environ.get('ELECTRON_BIN')
    if custom:
        runtime = shutil.which(custom)
        if runtime:
            return runtime
        raise RuntimeError('ELECTRON_BIN does not name an executable.')
    for name in ('electron', 'electron45', 'electron44', 'electron43', 'electron42', 'electron41', 'electron40', 'electron39'):
        runtime = shutil.which(name)
        if runtime:
            return runtime
    raise RuntimeError('The Browser needs Linux Electron. Install electron using your package manager, or set ELECTRON_BIN. Previous installation is unchanged.')


def prepare_browser(source, stage, bundle):
    upstream = source.parents[1] / 'Blackmagic Design/DaVinci Resolve/Workflow Integration Plugins/com.mralextech.magicscriptbrowser'
    if not upstream.is_dir():
        raise RuntimeError('The upstream package does not contain the MagicScript Browser.')
    target = stage / 'browser'
    shutil.copytree(upstream, target, ignore=shutil.ignore_patterns('._*', '*.node', 'main.js', 'manifest.xml'))
    with (bundle / 'browser/catalogue-linux.patch').open() as patch:
        subprocess.run(['patch', '--batch', '--forward', '--fuzz=0', str(target / 'catalogue.js')], stdin=patch, check=True)
    with (bundle / 'browser/renderer-linux.patch').open() as patch:
        subprocess.run(['patch', '--batch', '--forward', '--fuzz=0', str(target / 'renderer.js')], stdin=patch, check=True)
    shutil.copy2(bundle / 'browser/dist/main.js', target / 'main.cjs')
    shutil.copy2(bundle / 'browser/dist/linux-update.js', target / 'linux-update.js')
    (target / 'package.json').write_text(json.dumps({
        'name': 'magicscript-browser-linux', 'version': '0.1.0', 'main': 'main.cjs',
        'description': "Unofficial Linux host for MrAlexTech's MagicScript Browser",
    }))
    # Preserve upstream artwork/UI, with attribution for this host in the footer.
    page = target / 'index.html'
    page.write_text(page.read_text().replace('<span id="counts"></span>', '<span id="counts"></span><span class="hint">Original by MrAlexTech · Unofficial Linux host</span>'))
    runtime = electron_runtime()
    env = dict(os.environ, ELECTRON_RUN_AS_NODE='1')
    for name in ('LD_LIBRARY_PATH', 'LD_PRELOAD'):
        env.pop(name, None)
    for file in ('main.cjs', 'linux-update.js', 'preload.js', 'renderer.js', 'catalogue.js'):
        subprocess.run([runtime, '--check', str(target / file)], env=env, check=True, capture_output=True)
    # The Browser is just a catalogue manager; no native Resolve module is needed.
    assert not list(target.glob('*.node'))


def desktop_entry(home):
    executable = str(home / '.local/bin/magicscript-browser').replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    return f'''[Desktop Entry]
Type=Application
Name=MagicScript Browser
Comment=Browse and install MagicScript scripts for DaVinci Resolve — by MrAlexTech
Exec="{executable}"
Icon=applications-multimedia
Terminal=false
Categories=AudioVideo;Video;
'''
