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
exports.startBrowser = startBrowser;
// Linux host for MrAlexTech's original MagicScript Browser renderer and catalogue.
const electron_1 = require("electron");
const path = __importStar(require("node:path"));
const fs = __importStar(require("node:fs"));
const node_url_1 = require("node:url");
const linux_update_1 = require("./linux-update");
const catalogue = require('./catalogue.js');
const entry = path.join(__dirname, 'index.html');
let window = null;
let pendingUpdate = null;
function scriptId(value) {
    if (typeof value !== 'string' || !/^[\w-]{1,64}$/.test(value))
        throw new Error('Invalid script id.');
    return value;
}
function localPath(value) {
    if (typeof value !== 'string')
        throw new Error('Invalid file path.');
    const root = fs.realpathSync(catalogue.userDir());
    const candidate = fs.realpathSync(value);
    const relative = path.relative(root, candidate);
    if (relative.startsWith('..') || path.isAbsolute(relative))
        throw new Error('File is outside your MagicScript folder.');
    return candidate;
}
function registerHandlers() {
    const handlers = {
        fetch: async () => {
            const result = await catalogue.fetchCatalogue();
            return { ...result, app: { ...result.app, platform: 'linux', installed: (0, linux_update_1.installedVersion)(), update: false } };
        },
        install: (id) => catalogue.installScript(scriptId(id)),
        uninstall: (id) => catalogue.uninstallScript(scriptId(id)),
        precheck: (id) => catalogue.precheckScript(scriptId(id)),
        submit: (id, form) => {
            if (!form || typeof form !== 'object' || Array.isArray(form))
                throw new Error('Invalid submission form.');
            return catalogue.submitScript(scriptId(id), form, { resolve: '' });
        },
        ratings: () => catalogue.fetchRatings(),
        rate: (id, stars) => {
            if (typeof stars !== 'number' || !Number.isInteger(stars) || stars < 1 || stars > 5)
                throw new Error('Choose 1 to 5 stars.');
            return catalogue.rateScript(scriptId(id), stars);
        },
        // Linux updates are managed by the transactional updater, not a Mac/Windows download.
        downloadInstaller: () => {
            pendingUpdate ??= (0, linux_update_1.runLinuxUpdate)().finally(() => { pendingUpdate = null; });
            return pendingUpdate;
        },
        showFile: (file) => { electron_1.shell.showItemInFolder(localPath(file)); return true; },
        reveal: async () => {
            const dir = path.join(catalogue.userDir(), 'scripts');
            fs.mkdirSync(dir, { recursive: true });
            const error = await electron_1.shell.openPath(dir);
            if (error)
                throw new Error(error);
            return dir;
        },
        openExternal: async (url) => {
            if (typeof url !== 'string' || new URL(url).protocol !== 'https:')
                throw new Error('Only HTTPS links are supported.');
            await electron_1.shell.openExternal(url);
            return true;
        },
    };
    for (const [name, handle] of Object.entries(handlers)) {
        electron_1.ipcMain.handle(`catalogue:${name}`, async (event, ...args) => {
            if (!window || event.sender !== window.webContents || event.senderFrame?.url !== (0, node_url_1.pathToFileURL)(entry).href) {
                throw new Error('Unknown Browser page.');
            }
            try {
                return await handle(...args);
            }
            catch (error) {
                console.error(`MagicScript Browser ${name} failed:`, error);
                throw error;
            }
        });
    }
}
async function startBrowser() {
    await electron_1.app.whenReady();
    electron_1.app.name = 'MagicScript Browser';
    fs.mkdirSync(catalogue.userDir(), { recursive: true });
    registerHandlers();
    window = new electron_1.BrowserWindow({
        width: 1120, height: 820, minWidth: 760, minHeight: 540,
        backgroundColor: '#212126', title: 'MagicScript Browser — Linux',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true, sandbox: true, nodeIntegration: false,
        },
    });
    window.on('close', (event) => {
        if (!pendingUpdate)
            return;
        event.preventDefault();
        void electron_1.dialog.showMessageBox(window, { type: 'info', message: 'MagicScript is updating.', detail: 'Please wait for the update result before closing the Browser.' });
    });
    window.setMenu(null);
    window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    window.webContents.on('will-navigate', (event) => event.preventDefault());
    window.webContents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
    window.webContents.on('render-process-gone', (_event, details) => console.error('Browser renderer exited:', details));
    await window.loadFile(entry);
    return window;
}
if (require.main === module) {
    if (!electron_1.app.requestSingleInstanceLock()) {
        electron_1.app.quit();
    }
    else {
        electron_1.app.on('second-instance', () => { window?.show(); window?.focus(); });
        electron_1.app.on('window-all-closed', () => electron_1.app.quit());
        startBrowser().catch((error) => {
            console.error('Could not open MagicScript Browser:', error);
            electron_1.app.exit(1);
        });
    }
}
