import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import { spawn } from 'node:child_process';

export type LinuxUpdateResult = Readonly<{ version: string; output: string }>;

export function installedVersion(home = os.homedir()): string {
    try {
        const source = fs.readFileSync(path.join(home, '.local/share/magicscript-linux/current/MagicScript.py'), 'utf8');
        return /^VERSION\s*=\s*"([^"]+)"/m.exec(source)?.[1] ?? '';
    } catch {
        return '';
    }
}

// The updater fetches GitHub's installer and archive on EVERY run. No Linux patch
// implementation or release version is baked into this long-lived Browser action.
export async function runLinuxUpdate(home = os.homedir()): Promise<LinuxUpdateResult> {
    const command = path.join(home, '.local/bin/magicscript-update');
    if (!fs.existsSync(command)) throw new Error('Linux updater is missing. Run the one-line Linux installer once to repair it.');
    return new Promise((resolve, reject) => {
        const environment = { ...process.env };
        for (const name of ['MAGICSCRIPT_APP', 'MAGICSCRIPT_SEED', 'LD_LIBRARY_PATH', 'LD_PRELOAD', 'ELECTRON_RUN_AS_NODE']) delete environment[name];
        const child = spawn(command, ['--no-auto-update'], { env: environment, stdio: ['ignore', 'pipe', 'pipe'] });
        let output = '';
        const collect = (chunk: Buffer): void => { output = (output + chunk.toString('utf8')).slice(-24000); };
        child.stdout.on('data', collect);
        child.stderr.on('data', collect);
        child.once('error', (error) => reject(new Error(`Could not start the Linux updater: ${error.message}`)));
        child.once('close', (code, signal) => {
            if (code !== 0) {
                reject(new Error(`Linux update failed${signal ? ` (${signal})` : ''}. The updater retains or rolls back the previous installation.\n${output.trim()}`));
                return;
            }
            resolve({ version: installedVersion(home), output: output.trim() });
        });
    });
}
