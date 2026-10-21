"""Personal Linux installation using the publisher's original Python payload."""
import os
import shutil
import sys
from pathlib import Path

source = Path(sys.argv[1])
root = Path.home() / '.local/share/magicscript-linux'
app = root / '1.2.3'
if app.exists():
    raise SystemExit(f'{app} already exists; installation left unchanged.')
app.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(source, app, ignore=shutil.ignore_patterns('._*', '__pycache__', 'streamdeck', 'magicscript_streamdeck.py'))
main = app / 'MagicScript.py'
text = main.read_text(encoding="utf-8")
text = text.replace('    return "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"', '    return "/opt/resolve/LUT" if sys.platform.startswith("linux") else "/Library/Application Support/Blackmagic Design/DaVinci Resolve/LUT"')
needle = '    else:\n        roots.append("/Applications/DaVinci Resolve/'
assert text.count(needle) == 1
text = text.replace(needle, '''    elif sys.platform.startswith("linux"):
        roots.extend([
            "/opt/resolve/Fusion/Templates/Templates.drfx",
            "/opt/resolve/Fusion/Templates/Edit",
            os.path.expanduser("~/.local/share/DaVinciResolve/Fusion/Templates/Edit"),
        ])
    else:
        roots.append("/Applications/DaVinci Resolve/''')
main.write_text(text, encoding="utf-8")
import subprocess
with (Path(__file__).resolve().parent / "no-streamdeck.patch").open() as patch:
    subprocess.run(["patch", "--batch", str(main)], stdin=patch, check=True)
with (Path(__file__).resolve().parent / "guide-linux.patch").open() as patch:
    subprocess.run(["patch", "--batch", str(app / "MAGICSCRIPT.md")], stdin=patch, check=True)
with (Path(__file__).resolve().parent / "ai-skills.patch").open() as patch:
    subprocess.run(["patch", "--batch", str(main)], stdin=patch, check=True)
shutil.copy2(Path(__file__).resolve().parent / "magicscript_skills.py", app / "magicscript_skills.py")
# Resolve requires Python for its native UIManager; retain the original engine.
launcher = Path.home() / '.local/share/DaVinciResolve/Fusion/Scripts/Utility/MagicScript.py'
launcher.parent.mkdir(parents=True, exist_ok=True)
if launcher.exists():
    raise SystemExit(f'{launcher} exists; refusing to overwrite it. Payload is at {app}.')
launcher.write_text('''# Unofficial Linux launcher for MagicScript. Original notices remain in the app.
import os
import traceback
from pathlib import Path

try:
    app = Path.home() / ".local/share/magicscript-linux/1.2.3"
    os.environ["MAGICSCRIPT_APP"] = str(app)
    os.environ["MAGICSCRIPT_SEED"] = "1"
    entry = app / "MagicScript.py"
    namespace = dict(globals(), __file__=str(entry), __name__="__main__")
    exec(compile(entry.read_text(encoding="utf-8"), str(entry), "exec"), namespace)
except Exception:
    print("MagicScript Linux: failed to open the catalogue")
    traceback.print_exc()
''')
print(f'Installed: {app}\nLauncher: {launcher}\nOpen Workspace > Scripts > Utility > MagicScript (restart Resolve if needed).')
