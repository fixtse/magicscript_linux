"""Create local assistant skills from the installed MagicScript guide."""
from pathlib import Path
import os
import shutil
import tempfile
import time
import zipfile

SKILL_NAME = 'create-magicscript'


def skill_text(kit):
    return f'''---
name: create-magicscript
description: Create, adapt, validate, and save reusable Python scripts for MagicScript in DaVinci Resolve Studio. Use when the user requests a MagicScript script or changes to one.
---

# Create MagicScript

Read [the Linux MagicScript guide](references/MAGICSCRIPT.md) before creating or
adapting a script; it defines MANIFEST, run(ctx), supported variable types, and
Resolve API pitfalls. The live guide is `{kit}/MAGICSCRIPT.md`.

Search `{kit}/CATALOGUE.md` and `{kit}/scripts/` for a suitable existing script.
Reuse or adapt one when it fits the user's request. Save new scripts to
`{kit}/scripts/<Category>/<id>.py`, using a new id for a new script. Keep the
filename and MANIFEST id identical. Expose user choices through MANIFEST variables.

Use available Resolve documentation/tools to verify APIs. Validate syntax and the
manifest using the installed validator when available. Distinguish offline validation
from a successful live run. Execute project-changing operations only within the
user's authorized scope; use a duplicate timeline for risky testing and preserve
existing work. Do not treat skill installation as permission to execute scripts.

Report the script name, saved path, what was verified, and any remaining limitations.
Tell the user to press Reload in MagicScript to see the saved script.
'''


def install_skill(target, guide, kit, home=None):
    """Install without overwriting existing skills; stage a complete folder first."""
    home = Path(home) if home else Path.home()
    roots = {'codex': home / '.agents/skills', 'claude': home / '.claude/skills',
             'manual': Path(kit) / 'assistant-skills'}
    if target not in roots:
        raise ValueError('Choose Codex, Claude Code or manual export.')
    parent = roots[target]
    dest = parent / SKILL_NAME
    content = skill_text(str(kit))
    reference = Path(guide).read_text(encoding='utf-8')
    if dest.exists() or dest.is_symlink():
        if (not dest.is_symlink() and (dest / 'SKILL.md').is_file()
                and (dest / 'SKILL.md').read_text(encoding='utf-8') == content
                and (dest / 'references/MAGICSCRIPT.md').is_file()
                and (dest / 'references/MAGICSCRIPT.md').read_text(encoding='utf-8') == reference):
            return dest
        raise FileExistsError(f'{dest} already exists. Move it aside to install a new copy; nothing was overwritten.')
    parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.magicscript-', dir=parent))
    try:
        (stage / 'references').mkdir()
        (stage / 'SKILL.md').write_text(content, encoding='utf-8')
        (stage / 'references/MAGICSCRIPT.md').write_text(reference, encoding='utf-8')
        stage.rename(dest)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return dest


def export_manual(guide, kit):
    dest = install_skill('manual', guide, kit)
    archive = dest.parent / (SKILL_NAME + '.zip')
    if archive.exists():
        # Never overwrite a user-modified export.
        with zipfile.ZipFile(archive) as z:
            expected = {str(p.relative_to(dest.parent)): p.read_bytes() for p in dest.rglob('*') if p.is_file()}
            if {n: z.read(n) for n in z.namelist()} != expected:
                raise FileExistsError(f'{archive} already exists with different contents.')
        return dest, archive
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for p in dest.rglob('*'):
            if p.is_file():
                z.write(p, p.relative_to(dest.parent))
    return dest, archive


def open_install_window(ui, dispatcher, style, guide, kit, log, open_path):
    """Non-modal dialog; the main MagicScript dispatcher handles its events."""
    base = 'com.mralextech.resolve.MagicScript.installskill'
    # A window left by a previous script host has no live event handlers.
    # Always create this window with the current dispatcher instead of reusing it.
    old = ui.FindWindow(base)
    if old:
        old.Hide()
        old.Close()
    wid = f'{base}.{time.time_ns()}'
    window = dispatcher.AddWindow(
        {'ID': wid, 'WindowTitle': 'Create MagicScript skill', 'Geometry': [260, 180, 700, 440], 'MinimumSize': [620, 420], 'StyleSheet': style},
        ui.VGroup({'Spacing': 10}, [
            ui.Label({'ID': 'heading', 'Text': 'Teach your assistant to create reusable MagicScript scripts.', 'WordWrap': True, 'Weight': 0, 'MinimumSize': [0, 32]}),
            ui.Label({'ID': 'instructions', 'Text': 'Choose where to install the skill.\nThis adds the skill and Linux guide.\nIt does not run scripts or connect to your AI account.', 'WordWrap': True, 'Weight': 0, 'MinimumSize': [0, 78], 'Alignment': {'AlignTop': True, 'AlignLeft': True}}),
            ui.HGroup({'Weight': 0, 'Spacing': 8}, [
                ui.Button({'ID': 'codex', 'Text': 'Install for Codex'}),
                ui.Button({'ID': 'claude', 'Text': 'Install for Claude Code'}),
                ui.Button({'ID': 'manual', 'Text': 'Manual / export'}),
            ]),
            ui.TextEdit({'ID': 'status', 'ReadOnly': True, 'Text': 'Codex: ~/.agents/skills/create-magicscript\nClaude Code: ~/.claude/skills/create-magicscript\nManual: export a skill folder and ZIP to use with your assistant.', 'Weight': 1}),
            ui.HGroup({'Weight': 0}, [
                ui.Button({'ID': 'guide', 'Text': 'Read guide'}),
                ui.HGap(0, 1),
                ui.Button({'ID': 'close', 'Text': 'Close'}),
            ]),
        ]))
    items = window.GetItems()

    def install(target):
        items['status'].PlainText = 'Installing skill...'
        try:
            if target == 'manual':
                dest, archive = export_manual(guide, kit)
                message = (f'Exported: {archive}\n\nFor a local assistant, copy the create-magicscript folder into its skills directory. '
                           'For an assistant with skill uploads, upload the ZIP. For a chat without skills, attach references/MAGICSCRIPT.md and ask it to create a MagicScript script. '
                           'Remote assistants need access to your Resolve tools and files for live testing.')
                open_path(str(dest.parent))
            else:
                dest = install_skill(target, guide, kit)
                invocation = '$create-magicscript' if target == 'codex' else '/create-magicscript'
                message = f'Installed: {dest}\n\nStart a new assistant session and use {invocation}, followed by what you want the script to do.'
            items['status'].PlainText = message
            log(message)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            items['status'].PlainText = f'Could not install skill: {exc}'
            log(f'Create MagicScript skill installation failed ({target}): {exc}')

    window.On['codex'].Clicked = lambda ev: install('codex')
    window.On['claude'].Clicked = lambda ev: install('claude')
    window.On['manual'].Clicked = lambda ev: install('manual')
    window.On['guide'].Clicked = lambda ev: open_path(guide)
    window.On['close'].Clicked = lambda ev: window.Hide()
    window.On[wid].Close = lambda ev: window.Hide()
    window.Show()
    window.RecalcLayout()
    window.Raise()
    return window
