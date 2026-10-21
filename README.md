# MagicScript for Linux

An unofficial, per-user Linux installer for **MagicScript 1.2.3** in **DaVinci Resolve Studio 21.1+**.

**MagicScript was created by MrAlexTech (MrAlexTech Ltd).** This repository adapts the installation and interface for Linux; the original MagicScript engine and catalogue scripts are the creator's work.

**[Original MagicScript page, downloads and optional donations](https://magic-toolkit.com/magicscript)**

This project is independent of MrAlexTech Ltd and Blackmagic Design.

## Easy installation

You need DaVinci Resolve **Studio** 21.1 or newer installed on Linux. The free edition is not supported. The installer assumes Resolve is installed in `/opt/resolve`.

1. Install these command-line tools using your distribution's package manager: `git`, `bash`, `curl`, `python3`, `patch`, `bsdtar` (libarchive), and `sha256sum` (coreutils).
2. Open a terminal and run:

   ```bash
   git clone https://github.com/fixtse/magicscript_linux.git
   cd magicscript_linux
   bash install.sh
   ```

3. Restart Resolve, then open **Workspace → Scripts → Utility → MagicScript**.

Run the installer as your normal user, without `sudo`. Installation downloads the original macOS package directly from the creator's download server, verifies its pinned SHA-256, and extracts its Python files. No macOS or Windows executable is run. An internet connection is needed for installation.

The installer refuses to overwrite an existing installation or launcher. It currently installs version 1.2.3; it is not an automatic updater.

## What this Linux adaptation changes

- Launches the original Python catalogue window through Resolve's **Scripts → Utility** menu.
- Installs into your home directory, with separate editable scripts, reports and state.
- Uses Linux LUT and Fusion template paths.
- Makes `MAGICSCRIPT.md` show Linux paths, instructions and Python examples only. Both the engine and personal copies retain this guide.
- Removes the unavailable Stream Deck button, integration code and plugin files.
- Replaces **AI guide** with **Install AI skill…**, a chooser with **Codex**, **Claude Code** and **Manual / export** options. **Read guide** remains available in the chooser.
- Generates a `create-magicscript` skill with the Linux guide as a reference. Existing skills are preserved; an identical installation can be reused.
- Creates a fresh chooser with the current event dispatcher, raises it to the front, and shows installation results or errors in the chooser. Opening failures are logged in MagicScript.
- Gives the chooser's explanation dedicated space and a larger minimum window size to prevent clipped text.

The original engine, catalogue scripts and licence notices are retained in the downloaded installation. This repository contains installation helpers and patches, rather than a complete copy of MagicScript.

## Set up your AI assistant

In MagicScript, click **Install AI skill…**, then choose:

| Option | Result | Use it |
|---|---|---|
| Install for Codex | Creates `~/.agents/skills/create-magicscript/` | Start a new session and ask `$create-magicscript` followed by your request. |
| Install for Claude Code | Creates `~/.claude/skills/create-magicscript/` | Start a new session and ask `/create-magicscript` followed by your request. |
| Manual / export | Creates a skill folder and ZIP under `<MagicScript folder>/assistant-skills/` and opens that directory | Copy the folder into your assistant's skills directory, or upload the ZIP if it supports skill uploads. For a chat without skills, attach the guide from the exported `references/` folder. |

Installation adds instructions; it does not sign into an assistant, configure an MCP connection, or run catalogue scripts. Your assistant needs access to Resolve tools and your files to perform live tests. The local Claude Code installation does not install a skill into the Claude website.

## Installed locations

| Item | Location |
|---|---|
| Engine | `~/.local/share/magicscript-linux/1.2.3/` |
| Resolve menu launcher | `~/.local/share/DaVinciResolve/Fusion/Scripts/Utility/MagicScript.py` |
| Personal MagicScript folder | `~/.local/share/DaVinciResolve/MagicScript/` |
| Editable scripts | `<MagicScript folder>/scripts/<Category>/<id>.py` |
| Guide | `<MagicScript folder>/MAGICSCRIPT.md` |
| Reports and state | `<MagicScript folder>/reports/` and `<MagicScript folder>/state.json` |

## Verification and limitations

Verified on Linux x86_64 with Resolve Studio **21.1.1.10**:

- The original offline validator accepted all **58** bundled catalogue scripts.
- The catalogue window and assistant chooser initialized inside Resolve.
- Linux paths discovered **125 LUT files** on the test machine.
- Skill installation, repeat installation, conflict preservation, manual ZIP export and success messaging were checked; installation tests used temporary directories.
- A clean installation with all patches applied successfully.

This does not establish that every catalogue script or UI interaction works on every Linux system. Individual catalogue scripts have not all been tested against projects. The Electron Workflow Integration browser is not included. Upstream Ctrl/Shift-click modifier detection has no Linux implementation, so those shortcuts remain limited.

## Troubleshooting

- **No MagicScript menu entry:** restart Resolve and confirm the launcher exists at the path above.
- **Chooser does not open or text is clipped after an update:** close and reopen MagicScript so it loads the current code. Opening errors appear in its log.
- **Missing command:** install the named tool using your distribution's package manager. `bsdtar` is provided by libarchive; some distributions name the package `libarchive-tools`.
- **Existing installation or skill:** the installer will not overwrite it. Back up your files and move the existing engine/launcher or conflicting skill aside before reinstalling. Keep your personal scripts folder.
- **Checksum mismatch:** stop and verify the upstream download/version. The package is pinned to 1.2.3; do not bypass verification.

## Uninstall

Remove these two installation items:

```bash
rm -- "$HOME/.local/share/DaVinciResolve/Fusion/Scripts/Utility/MagicScript.py"
rm -r -- "$HOME/.local/share/magicscript-linux/1.2.3"
```

Your personal scripts, reports and state remain in `~/.local/share/DaVinciResolve/MagicScript/`. Skills installed through the chooser also remain; remove their `create-magicscript` folders separately if desired.

## Attribution and upstream package

All credit for **MagicScript and its catalogue** belongs to **MrAlexTech / MrAlexTech Ltd**. Visit the [original MagicScript page](https://magic-toolkit.com/magicscript) for the official product, supported installers and ways to support its creator.

MagicScript is proprietary freeware, not an open-source project. Its original licence and third-party notices are preserved in the installed payload. This Linux adaptation does not change the creator's ownership or licence terms.

- Original package: [MagicScript-Setup-1.2.3.pkg](https://downloads.magic-toolkit.com/magicscript/mac/MagicScript-Setup-1.2.3.pkg)
- Pinned SHA-256: `62e8d3a2bef019fe35fa093f8dae4967ca37daef41931b2719ef2d15e62a0c02`
