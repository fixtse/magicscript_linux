import assert from 'node:assert/strict';
import * as fs from 'node:fs';
import * as os from 'node:os';
import * as path from 'node:path';
import * as http from 'node:http';
import * as crypto from 'node:crypto';

async function main(): Promise<void> {
    const app = process.env.MAGICSCRIPT_TEST_APP;
    if (!app) throw new Error('Set MAGICSCRIPT_TEST_APP to a staged engine folder.');
    const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'ms-browser-catalogue-'));
    const originalEnvironment = { ...process.env };
    const copy = path.join(temp, 'browser');
    fs.cpSync(path.join(app, 'browser'), copy, { recursive: true });
    const { publicKey, privateKey } = crypto.generateKeyPairSync('ed25519');
    fs.writeFileSync(path.join(copy, 'public_key.pem'), publicKey.export({ type: 'spki', format: 'pem' }));
    const source = Buffer.from('MANIFEST = {"id": "linux_fixture", "name": "Linux fixture", "category": "Reports", "description": "Check the Linux Browser.", "needs": None, "variables": []}\ndef run(ctx):\n    return "No project changes"\n');
    const index = Buffer.from(JSON.stringify({ version: '1', categories: [{ name: 'Reports' }], scripts: [{
        id: 'linux_fixture', name: 'Linux fixture', category: 'Reports', version: '1.0',
        sha256: crypto.createHash('sha256').update(source).digest('hex'), path: 'scripts/linux_fixture.py',
    }] }));
    let badSignature = false;
    let badPayload = false;
    const server = http.createServer((req, res) => {
        if (req.url === '/index.json') return void res.end(index);
        if (req.url === '/index.sig') return void res.end(badSignature ? Buffer.alloc(64).toString('base64') : crypto.sign(null, index, privateKey).toString('base64'));
        if (req.url === '/scripts/linux_fixture.py') return void res.end(badPayload ? 'tampered' : source);
        res.writeHead(404); res.end();
    });
    await new Promise<void>((resolve) => server.listen(0, '127.0.0.1', resolve));
    try {
        const address = server.address();
        assert(address && typeof address !== 'string');
        process.env.MAGICSCRIPT_CATALOGUE_URL = `http://127.0.0.1:${address.port}`;
        process.env.MAGICSCRIPT_DIR = path.join(temp, 'kit');
        process.env.MAGICSCRIPT_APP = app;
        const catalogue = require(path.join(copy, 'catalogue.js'));
        let result = await catalogue.fetchCatalogue();
        assert.equal(result.scripts[0].state, '');
        const installed = await catalogue.installScript('linux_fixture');
        assert.equal(installed.validated, 'python');
        assert.equal(fs.readFileSync(installed.file, 'utf8'), source.toString());
        result = await catalogue.fetchCatalogue();
        assert.equal(result.scripts[0].state, 'installed');
        badPayload = true;
        await assert.rejects(catalogue.installScript('linux_fixture'), /signed catalogue hash/);
        assert.equal(fs.readFileSync(installed.file, 'utf8'), source.toString());
        badPayload = false;
        badSignature = true;
        await assert.rejects(catalogue.fetchCatalogue(), /signature/);
        badSignature = false;
        await catalogue.fetchCatalogue();
        await catalogue.uninstallScript('linux_fixture');
        assert(!fs.existsSync(installed.file));
        console.log('PASS: signed catalogue, Python validation, install, installed state, tamper rejection and removal in an isolated folder.');
    } finally {
        process.env = originalEnvironment;
        server.close();
        fs.rmSync(temp, { recursive: true, force: true });
    }
}
main().catch((error) => { console.error(error); process.exitCode = 1; });
