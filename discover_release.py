"""Discover the latest upstream installer from MrAlexTech's signed catalogue."""
import base64
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.request import Request, urlopen

ORIGIN = 'https://browser.magic-toolkit.com'


def verify_and_discover(index_bytes, signature, public_key):
    try:
        decoded = base64.b64decode(signature.strip(), validate=True)
    except ValueError as exc:
        raise RuntimeError('Invalid upstream catalogue signature encoding.') from exc
    with tempfile.TemporaryDirectory(prefix='magicscript-signature-') as directory:
        root = Path(directory)
        (root / 'index.json').write_bytes(index_bytes)
        (root / 'index.sig').write_bytes(decoded)
        result = subprocess.run(['openssl', 'pkeyutl', '-verify', '-pubin', '-inkey', str(public_key),
                                 '-rawin', '-in', str(root / 'index.json'), '-sigfile', str(root / 'index.sig')],
                                capture_output=True)
        if result.returncode:
            raise RuntimeError('Upstream catalogue signature did not verify. Existing installation is unchanged.')
    app = json.loads(index_bytes).get('app', {})
    version = app.get('version', '')
    if not isinstance(version, str) or not re.fullmatch(r'\d+(?:\.\d+){1,3}', version):
        raise RuntimeError('The signed catalogue has no valid upstream app version.')
    mac = app.get('installers', {}).get('mac', {})
    expected = f'releases/MagicScript-Setup-{version}.pkg'
    digest = mac.get('sha256', '')
    if mac.get('path') != expected or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
        raise RuntimeError('The signed catalogue has no valid Mac installer and checksum.')
    return {'version': version, 'url': f'{ORIGIN}/{expected}', 'sha256': digest, 'discovered_from': f'{ORIGIN}/index.json'}


def download(url):
    request = Request(url, headers={'User-Agent': 'MagicScriptLinuxUpdater/1'})
    with urlopen(request, timeout=30) as response:
        if not response.url.startswith('https://'):
            raise RuntimeError('Upstream discovery redirected away from HTTPS.')
        return response.read(8 * 1024 * 1024)


def main():
    release = verify_and_discover(download(f'{ORIGIN}/index.json'), download(f'{ORIGIN}/index.sig'),
                                  Path(__file__).resolve().parent / 'upstream/catalogue-public-key.pem')
    Path(sys.argv[1]).write_text(json.dumps(release), encoding='utf-8')
    print(f'Discovered upstream MagicScript {release["version"]} from the verified catalogue.')


if __name__ == '__main__':
    main()
