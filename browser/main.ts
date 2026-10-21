// Linux host for MrAlexTech's original MagicScript Browser renderer and catalogue.
import { app, BrowserWindow, ipcMain, shell, dialog } from 'electron';
import * as path from 'node:path';
import * as fs from 'node:fs';
import { pathToFileURL } from 'node:url';
import { installedVersion, runLinuxUpdate, type LinuxUpdateResult } from './linux-update';

type Catalogue = {
    userDir(): string;
    fetchCatalogue(): Promise<unknown>;
    installScript(id: string): Promise<unknown>;
    uninstallScript(id: string): Promise<unknown>;
    precheckScript(id: string): unknown;
    submitScript(id: string, form: Record<string, unknown>, client: { resolve: string }): Promise<unknown>;
    fetchRatings(): Promise<unknown>;
    rateScript(id: string, stars: number): Promise<unknown>;
};
const catalogue: Catalogue = require('./catalogue.js');
const entry = path.join(__dirname, 'index.html');
let window: BrowserWindow | null = null;
let pendingUpdate: Promise<LinuxUpdateResult> | null = null;

function scriptId(value: unknown): string {
    if (typeof value !== 'string' || !/^[\w-]{1,64}$/.test(value)) throw new Error('Invalid script id.');
    return value;
}

function localPath(value: unknown): string {
    if (typeof value !== 'string') throw new Error('Invalid file path.');
    const root = fs.realpathSync(catalogue.userDir());
    const candidate = fs.realpathSync(value);
    const relative = path.relative(root, candidate);
    if (relative.startsWith('..') || path.isAbsolute(relative)) throw new Error('File is outside your MagicScript folder.');
    return candidate;
}

function registerHandlers(): void {
    const handlers: Record<string, (...args: unknown[]) => unknown> = {
        fetch: async () => {
            const result = await catalogue.fetchCatalogue() as { app?: Record<string, unknown> };
            return { ...result, app: { ...result.app, platform: 'linux', installed: installedVersion(), update: false } };
        },
        install: (id) => catalogue.installScript(scriptId(id)),
        uninstall: (id) => catalogue.uninstallScript(scriptId(id)),
        precheck: (id) => catalogue.precheckScript(scriptId(id)),
        submit: (id, form) => {
            if (!form || typeof form !== 'object' || Array.isArray(form)) throw new Error('Invalid submission form.');
            return catalogue.submitScript(scriptId(id), form as Record<string, unknown>, { resolve: '' });
        },
        ratings: () => catalogue.fetchRatings(),
        rate: (id, stars) => {
            if (typeof stars !== 'number' || !Number.isInteger(stars) || stars < 1 || stars > 5) throw new Error('Choose 1 to 5 stars.');
            return catalogue.rateScript(scriptId(id), stars);
        },
        // Linux updates are managed by the transactional updater, not a Mac/Windows download.
        downloadInstaller: () => {
            pendingUpdate ??= runLinuxUpdate().finally(() => { pendingUpdate = null; });
            return pendingUpdate;
        },
        showFile: (file) => { shell.showItemInFolder(localPath(file)); return true; },
        reveal: async () => {
            const dir = path.join(catalogue.userDir(), 'scripts');
            fs.mkdirSync(dir, { recursive: true });
            const error = await shell.openPath(dir);
            if (error) throw new Error(error);
            return dir;
        },
        openExternal: async (url) => {
            if (typeof url !== 'string' || new URL(url).protocol !== 'https:') throw new Error('Only HTTPS links are supported.');
            await shell.openExternal(url);
            return true;
        },
    };
    for (const [name, handle] of Object.entries(handlers)) {
        ipcMain.handle(`catalogue:${name}`, async (event, ...args: unknown[]) => {
            if (!window || event.sender !== window.webContents || event.senderFrame?.url !== pathToFileURL(entry).href) {
                throw new Error('Unknown Browser page.');
            }
            try {
                return await handle(...args);
            } catch (error) {
                console.error(`MagicScript Browser ${name} failed:`, error);
                throw error;
            }
        });
    }
}

export async function startBrowser(): Promise<BrowserWindow> {
    await app.whenReady();
    app.name = 'MagicScript Browser';
    fs.mkdirSync(catalogue.userDir(), { recursive: true });
    registerHandlers();
    window = new BrowserWindow({
        width: 1120, height: 820, minWidth: 760, minHeight: 540,
        backgroundColor: '#212126', title: 'MagicScript Browser — Linux',
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            contextIsolation: true, sandbox: true, nodeIntegration: false,
        },
    });
    window.on('close', (event) => {
        if (!pendingUpdate) return;
        event.preventDefault();
        void dialog.showMessageBox(window!, { type: 'info', message: 'MagicScript is updating.', detail: 'Please wait for the update result before closing the Browser.' });
    });
    window.setMenu(null);
    window.webContents.setWindowOpenHandler(() => ({ action: 'deny' }));
    window.webContents.on('will-navigate', (event) => event.preventDefault());
    window.webContents.session.setPermissionRequestHandler((_contents, _permission, callback) => callback(false));
    window.webContents.on('render-process-gone', (_event, details) => console.error('Browser renderer exited:', details));
    await window.loadFile(entry);
    console.log('MagicScript Browser ready.');
    return window;
}

// Electron loads the entry with its own module loader; require.main is not reliable.
if (process.env.MAGICSCRIPT_BROWSER_TEST !== '1') {
    if (!app.requestSingleInstanceLock()) {
        app.quit();
    } else {
        app.on('second-instance', () => { if (window?.isMinimized()) window.restore(); window?.show(); window?.focus(); });
        app.on('window-all-closed', () => app.quit());
        startBrowser().catch((error) => {
            console.error('Could not open MagicScript Browser:', error);
            app.exit(1);
        });
    }
}
