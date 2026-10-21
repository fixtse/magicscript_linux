// Tests the actual installed launcher, not an imported startBrowser() function.
import { spawn } from 'node:child_process';
import * as path from 'node:path';
import * as fs from 'node:fs';

async function main(): Promise<void> {
    const home = process.env.MAGICSCRIPT_LAUNCH_TEST_HOME;
    if (!home) throw new Error('Set MAGICSCRIPT_LAUNCH_TEST_HOME to an isolated installed test home.');
    const command = path.join(home, '.local/bin/magicscript-browser');
    if (!fs.existsSync(command)) throw new Error('Test launcher is missing.');
    const environment = { ...process.env, HOME: home, XDG_CONFIG_HOME: path.join(home, '.config') };
    delete (environment as NodeJS.ProcessEnv).ELECTRON_RUN_AS_NODE;
    delete (environment as NodeJS.ProcessEnv).MAGICSCRIPT_BROWSER_TEST;
    const child = spawn(command, ['--disable-gpu', '--ozone-platform=x11'], { env: environment, stdio: ['ignore', 'pipe', 'pipe'] });
    let output = '';
    await new Promise<void>((resolve, reject) => {
        const timer = setTimeout(() => { child.kill('SIGTERM'); reject(new Error(`No production Browser window was loaded:\n${output}`)); }, 15000);
        child.stdout.on('data', (chunk) => {
            output += chunk;
            if (output.includes('MagicScript Browser ready.')) {
                clearTimeout(timer);
                child.kill('SIGTERM');
                resolve();
            }
        });
        child.stderr.on('data', (chunk) => { output += chunk; });
        child.once('error', (error) => { clearTimeout(timer); reject(error); });
        child.once('close', () => {
            clearTimeout(timer);
            if (!output.includes('MagicScript Browser ready.')) reject(new Error(`Browser exited without opening its window:\n${output}`));
        });
    });
    console.log('PASS: actual installed launcher created and loaded the production Browser window.');
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
