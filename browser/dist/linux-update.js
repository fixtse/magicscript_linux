"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.installedVersion = installedVersion;
exports.runLinuxUpdate = runLinuxUpdate;
const fs = __importStar(require("node:fs"));
const os = __importStar(require("node:os"));
const path = __importStar(require("node:path"));
const node_child_process_1 = require("node:child_process");
function installedVersion(home = os.homedir()) {
    try {
        const source = fs.readFileSync(path.join(home, '.local/share/magicscript-linux/current/MagicScript.py'), 'utf8');
        return /^VERSION\s*=\s*"([^"]+)"/m.exec(source)?.[1] ?? '';
    }
    catch {
        return '';
    }
}
// The updater fetches GitHub's installer and archive on EVERY run. No Linux patch
// implementation or release version is baked into this long-lived Browser action.
async function runLinuxUpdate(home = os.homedir()) {
    const command = path.join(home, '.local/bin/magicscript-update');
    if (!fs.existsSync(command))
        throw new Error('Linux updater is missing. Run the one-line Linux installer once to repair it.');
    return new Promise((resolve, reject) => {
        const environment = { ...process.env };
        for (const name of ['MAGICSCRIPT_APP', 'MAGICSCRIPT_SEED', 'LD_LIBRARY_PATH', 'LD_PRELOAD', 'ELECTRON_RUN_AS_NODE'])
            delete environment[name];
        const child = (0, node_child_process_1.spawn)(command, ['--no-auto-update'], { env: environment, stdio: ['ignore', 'pipe', 'pipe'] });
        let output = '';
        const collect = (chunk) => { output = (output + chunk.toString('utf8')).slice(-24000); };
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
