# MagicScript for Linux

An unofficial, per-user Linux installer for **MagicScript 1.2.3** in **DaVinci Resolve Studio 21.1+**.

**MagicScript was created by MrAlexTech (MrAlexTech Ltd).** This repository adapts the installation and interface for Linux; the original MagicScript engine and catalogue scripts are the creator's work.

**[Original MagicScript page, downloads and optional donations](https://magic-toolkit.com/magicscript)**

This project is independent of MrAlexTech Ltd and Blackmagic Design.

## Easy installation

You need DaVinci Resolve **Studio** 21.1 or newer installed on Linux. The free edition is not supported. The installer assumes Resolve is installed in `/opt/resolve`.

1. Install these command-line tools using your distribution's package manager: `bash`, `curl`, `python3`, `patch`, `bsdtar` (libarchive), `tar`, `sha256sum` (coreutils), and a Linux `electron` runtime.
2. Open a terminal and run this one-line installer (no Git required):

   ```bash
   curl -fsSL https://raw.githubusercontent.com/fixtse/magicscript_linux/main/install.sh | bash
   ```

3. Restart Resolve, then open **Workspace → Scripts → Utility → MagicScript**.
4. Click **Browser** in MagicScript, open **Workspace → Scripts → Utility → MagicScript Browser**,
   or select **MagicScript Browser** from your Linux application menu.

The Browser uses your system Electron runtime (the `electron` command, or a versioned
`electron39`–`electron45` command). Keep that runtime updated through your distribution.
For a custom executable, set `ELECTRON_BIN` when installing **and** launching the Browser.
The installer checks the Browser's JavaScript with Electron before activating the release;
if Electron is missing, the previous installation remains intact. No Node.js, pnpm, Git,
or TypeScript compiler is needed for end-user installation.

Run as your normal user, without `sudo`. The command downloads the Linux installer files
from this repository and the original macOS package from the creator's download server.
It verifies the package's SHA-256 before extracting its Python files. No macOS or Windows
executable is run. An internet connection is required.

If you prefer to inspect the installer first, download this repository as a ZIP, extract it,
and run `bash install.sh` from its folder. A Git checkout also works.

## Automatic updates and rollback

The installer also acts as an updater: run the same one-liner again at any time. It fetches
the latest Linux adaptation and installs the upstream version recorded in `release.json`.
In the Browser, open **Installed → Check for Linux updates**. This runs the same
transactional updater: every click downloads the latest installer and patch files from
GitHub, verifies the upstream package, prepares the Linux changes, and activates only a
validated result. Future versions and Linux patch revisions use this same action; users
do not need to install a new Browser first just to learn the new patches. New upstream
releases still need a compatible `release.json` and patches published in this repository.

The Browser shows progress and a success/failure result, prevents duplicate update runs,
and stays open while the updater finishes. Close and reopen MagicScript and the Browser
after a successful update to load the active release. Individual catalogue script updates
continue to use the original signed catalogue and Python validator.

Once installed, you can also run:

```bash
~/.local/bin/magicscript-update
```

With a running **systemd user manager**, installation enables a daily
`magicscript-update.timer` (with up to 30 minutes randomized delay). Checks run while your
user manager is running; persistent timers catch up on a missed check after login. If the
user manager is unavailable, installation prints that automatic scheduling is unavailable;
use the update command manually instead.

To install without enabling automatic checks:

```bash
curl -fsSL https://raw.githubusercontent.com/fixtse/magicscript_linux/main/install.sh | bash -s -- --no-auto-update
```

This flag leaves any existing timer unchanged. To disable an already enabled timer:

```bash
systemctl --user disable --now magicscript-update.timer
```

Check the schedule and logs:

```bash
systemctl --user list-timers magicscript-update.timer
journalctl --user -u magicscript-update.service
```

Updates are transactional:

- Downloading, checksum verification, extraction, patching, syntax checks and the upstream
  offline catalogue validator complete before the new engine is activated.
- A complete release is stored separately, then the `current` symlink switches atomically.
  The launcher resolves that release once, so an already open window keeps using its engine.
- If preparation or activation fails, the previous engine link, launcher, updater and managed
  timer files are retained or restored. Failed staged releases are removed. An initial failed
  installation leaves no active engine or launcher.
- Personal scripts, reports, settings and installed assistant skills are never changed by the
  updater. The original first-run seeding still runs when you open MagicScript.
- A lock prevents simultaneous installs. Older successful releases and the original `1.2.3`
  installation are kept; close and reopen MagicScript after an update.

Automatic updates follow **releases supported by this Linux adaptation**, including patch
updates to the same upstream version. They do not blindly install an untested new upstream
release. Maintainers must update `release.json`, its pinned checksum, and compatible patches
before a new upstream version is eligible. A failed download/checksum leaves the current
installation untouched. Power loss or a forcibly killed process cannot execute rollback;
activation uses atomic file/link replacement to reduce that risk.

## What this Linux adaptation changes

- Launches the original Python catalogue window through Resolve's **Scripts → Utility** menu.
- Ports the **original MagicScript Browser** to a standalone Linux Electron window, preserving
  its renderer, styles, catalogue public key, search, installed-state views and catalogue operations.
- Connects the Browser to the same personal scripts folder and Resolve Python validator.
  Signed catalogue and download hash checks remain enabled. Script installation requires
  successful Python validation; installing a script does not execute it.
- Adds a Browser button, a separate Resolve script launcher, a command-line launcher and a
  Linux desktop application entry. The unsupported macOS native plugin binary is excluded.
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
| Engine | `~/.local/share/magicscript-linux/current/` (link to an immutable release) |
| Browser command | `~/.local/bin/magicscript-browser` |
| Browser application entry | `~/.local/share/applications/magicscript-browser.desktop` |
| Resolve menu launcher | `~/.local/share/DaVinciResolve/Fusion/Scripts/Utility/MagicScript.py` |
| Personal MagicScript folder | `~/.local/share/DaVinciResolve/MagicScript/` |
| Editable scripts | `<MagicScript folder>/scripts/<Category>/<id>.py` |
| Guide | `<MagicScript folder>/MAGICSCRIPT.md` |
| Reports and state | `<MagicScript folder>/reports/` and `<MagicScript folder>/state.json` |

## Verification and limitations

Verified on Linux x86_64 with Resolve Studio **21.1.1.10**:

- The original offline validator accepted all **58** bundled catalogue scripts.
- The catalogue window and assistant chooser initialized inside Resolve.
- The standalone Browser loaded the live signed catalogue (62 scripts, 12 categories),
  rendered category cards and search, with Node access disabled in the renderer.
- An isolated signed test catalogue exercised Python-validated script installation,
  installed-state detection, removal, and rejection of invalid signatures and file hashes.
  No tests posted community submissions or ratings.
- Linux paths discovered **125 LUT files** on the test machine.
- Skill installation, repeat installation, conflict preservation, manual ZIP export and success messaging were checked; installation tests used temporary directories.
- Clean installation, repeated update, patch/preparation failure, activation failure, and
  timer-activation rollback were checked. Transaction tests use temporary home directories.

This does not establish that every catalogue script or UI interaction works on every Linux system. Individual catalogue scripts have not all been tested against projects. The Browser runs as a standalone Electron app rather than inside Resolve's unsupported Linux Workflow Integration host. Upstream Ctrl/Shift-click modifier detection has no Linux implementation, so those shortcuts remain limited.

## Troubleshooting

- **Browser process runs without a window:** update once with `~/.local/bin/magicscript-update`, then close any older Browser processes and reopen it. The Linux host now starts through Electron's entry loader rather than relying on Node's `require.main` check.
- **Browser does not start:** run `~/.local/bin/magicscript-browser` in a terminal to see the error. Install a Linux Electron runtime or set `ELECTRON_BIN`. The launcher clears Resolve's private library overrides; it does not disable Electron's sandbox.
- **No MagicScript menu entry:** restart Resolve and confirm the launcher exists at the path above.
- **Chooser does not open or text is clipped after an update:** close and reopen MagicScript so it loads the current code. Opening errors appear in its log.
- **Missing command:** install the named tool using your distribution's package manager. `bsdtar` is provided by libarchive; some distributions name the package `libarchive-tools`.
- **Existing installation:** recognized Linux launchers are upgraded automatically. An unrecognized launcher is preserved and reported as a conflict. Existing assistant skills are not overwritten; move a conflicting skill aside if you want to replace it.
- **Checksum mismatch:** stop and verify the upstream download/version. The package is pinned to 1.2.3; do not bypass verification.

## Uninstall

Disable automatic checks first, if enabled:

```bash
systemctl --user disable --now magicscript-update.timer
```

Then remove the managed installation and timer files:

```bash
rm -f -- "$HOME/.config/systemd/user/magicscript-update.timer" "$HOME/.config/systemd/user/magicscript-update.service"
rm -f -- "$HOME/.local/bin/magicscript-update" "$HOME/.local/bin/magicscript-browser"
rm -f -- "$HOME/.local/share/applications/magicscript-browser.desktop"
rm -f -- "$HOME/.local/share/DaVinciResolve/Fusion/Scripts/Utility/MagicScript Browser.py"
rm -f -- "$HOME/.local/share/DaVinciResolve/Fusion/Scripts/Utility/MagicScript.py"
rm -r -- "$HOME/.local/share/magicscript-linux"
systemctl --user daemon-reload
```

Skip the systemctl commands if your system does not use a systemd user manager.
Your personal scripts, reports and state remain in `~/.local/share/DaVinciResolve/MagicScript/`.
Skills installed through the chooser also remain; remove their `create-magicscript` folders
separately if desired.

## Development checks

```bash
bash -n install.sh
python3 -m unittest discover -s tests -v
```

To develop the TypeScript Electron host (end users do not need this):

```bash
ELECTRON_SKIP_BINARY_DOWNLOAD=1 pnpm install --frozen-lockfile
pnpm build
pnpm test:updates
MAGICSCRIPT_TEST_APP="$HOME/.local/share/magicscript-linux/current" pnpm test:browser
```

Commit `browser/dist/main.js` and `browser/dist/linux-update.js` after rebuilding; the installer copies this generated entry
point beside the original Browser assets from the upstream package. TypeScript test sources
are in `browser/catalogue-test.ts`, `browser/smoke.ts`, and `browser/launch-test.ts`.
The launcher regression test runs the actual installed executable in an isolated home
and verifies that the production window loads. The latter can run in Electron
beside a staged `main.cjs`, with an isolated `MAGICSCRIPT_DIR`, to test the original renderer
against the live catalogue without installing scripts or posting submissions/ratings.

The tests exercise transaction behavior without downloading MagicScript or touching your
real installation. A full installation additionally validates the actual downloaded payload.

## Attribution and upstream package

All credit for **MagicScript and its catalogue** belongs to **MrAlexTech / MrAlexTech Ltd**. Visit the [original MagicScript page](https://magic-toolkit.com/magicscript) for the official product, supported installers and ways to support its creator.

MagicScript is proprietary freeware, not an open-source project. Its original licence and third-party notices are preserved in the installed payload. This Linux adaptation does not change the creator's ownership or licence terms.

- Original package: [MagicScript-Setup-1.2.3.pkg](https://downloads.magic-toolkit.com/magicscript/mac/MagicScript-Setup-1.2.3.pkg)
- Pinned SHA-256: `62e8d3a2bef019fe35fa093f8dae4967ca37daef41931b2719ef2d15e62a0c02`
