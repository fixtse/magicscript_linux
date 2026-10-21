// Run with system Electron after copying this compiled test beside an installed main.cjs.
import { app } from 'electron';
import * as fs from 'node:fs';
import * as path from 'node:path';
import assert from 'node:assert/strict';

async function main(): Promise<void> {
    const { startBrowser } = require('./main.cjs');
    const window = await startBrowser();
    const page = window.webContents;
    const result = await page.executeJavaScript(`(async () => {
        const catalogue = await window.catalogueAPI.fetch();
        return { scripts: catalogue.scripts.length, categories: catalogue.categories.length,
                 app_dir: catalogue.app_dir, user_dir: catalogue.user_dir,
                 nodeAvailable: typeof require !== 'undefined' };
    })()`);
    assert(result.scripts > 0);
    assert(result.categories > 0);
    assert.equal(result.nodeAvailable, false);
    console.log('LIVE_CATALOGUE', JSON.stringify(result));
    // Let the original renderer finish its independent initial catalogue request.
    for (let attempt = 0; attempt < 100; attempt++) {
        if (await page.executeJavaScript(`document.querySelectorAll('.card').length > 0`)) break;
        await new Promise((resolve) => setTimeout(resolve, 100));
    }
    const home = await page.executeJavaScript(`({ cards: document.querySelectorAll('.card').length, status: document.querySelector('#status').textContent })`);
    assert(home.cards > 0, JSON.stringify(home));
    await page.executeJavaScript(`document.querySelector('#showIncluded').click(); document.querySelector('#search').value = 'timeline'; document.querySelector('#search').dispatchEvent(new Event('input'));`);
    const search = await page.executeJavaScript(`({ rows: document.querySelectorAll('article').length, text: document.querySelector('#list').textContent })`);
    assert(search.rows > 0);
    const png = await window.capturePage();
    const output = process.env.MAGICSCRIPT_SCREENSHOT || path.join(app.getPath('temp'), 'magicscript-browser-linux.png');
    fs.writeFileSync(output, png.toPNG());
    console.log('PASS: original renderer, category cards, search, sandboxed IPC and live signed catalogue.', output);
    window.destroy();
    app.quit();
}
main().catch((error) => { console.error(error); app.exit(1); });
