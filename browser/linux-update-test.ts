import test from 'node:test';
import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { installedVersion, runLinuxUpdate } from './linux-update';

test('the update action runs the updater anew, reads the active version, and surfaces failure', async () => {
    const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ms-linux-update-'));
    try {
        const root = path.join(home, '.local/share/magicscript-linux/current');
        const bin = path.join(home, '.local/bin');
        fs.mkdirSync(root, { recursive: true });
        fs.mkdirSync(bin, { recursive: true });
        fs.writeFileSync(path.join(root, 'MagicScript.py'), 'VERSION = "1.2.3"\n');
        const remote = path.join(home, 'latest-version');
        fs.writeFileSync(remote, '1.2.4');
        fs.writeFileSync(path.join(bin, 'magicscript-update'), `#!/usr/bin/env python3
from pathlib import Path
import sys
home = Path(${JSON.stringify(home)})
assert sys.argv[1:] == ["--no-auto-update"]
version = (home / "latest-version").read_text()
if version == "fail":
    print("simulated patch failure; previous installation restored")
    sys.exit(1)
(home / ".local/share/magicscript-linux/current/MagicScript.py").write_text('VERSION = "' + version + '"\\n')
print("Applied latest GitHub modifications")
`, { mode: 0o755 });
        assert.equal(installedVersion(home), '1.2.3');
        assert.equal((await runLinuxUpdate(home)).version, '1.2.4');
        // The same already-installed action must see a later updater result.
        fs.writeFileSync(remote, '1.2.5');
        assert.equal((await runLinuxUpdate(home)).version, '1.2.5');
        fs.writeFileSync(remote, 'fail');
        await assert.rejects(runLinuxUpdate(home), /simulated patch failure/);
        assert.equal(installedVersion(home), '1.2.5');
    } finally {
        fs.rmSync(home, { recursive: true, force: true });
    }
});

test('a missing updater gives an actionable error', async () => {
    const home = fs.mkdtempSync(path.join(os.tmpdir(), 'ms-missing-updater-'));
    try { await assert.rejects(runLinuxUpdate(home), /one-line Linux installer/); }
    finally { fs.rmSync(home, { recursive: true, force: true }); }
});
