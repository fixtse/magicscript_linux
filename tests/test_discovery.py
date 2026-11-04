"""Verify release discovery against signed test metadata, without network access."""
import base64
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from discover_release import verify_and_discover


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.key = self.root / 'key.pem'
        self.public = self.root / 'public.pem'
        subprocess.run(['openssl', 'genpkey', '-algorithm', 'ED25519', '-out', str(self.key)], check=True, capture_output=True)
        subprocess.run(['openssl', 'pkey', '-in', str(self.key), '-pubout', '-out', str(self.public)], check=True, capture_output=True)

    def signed(self, version='9.2.0', installer_path=None):
        payload = json.dumps({'app': {'version': version, 'installers': {'mac': {
            'path': installer_path or f'releases/MagicScript-Setup-{version}.pkg', 'sha256': 'a' * 64,
        }}}}).encode()
        document = self.root / 'index.json'
        document.write_bytes(payload)
        signature = self.root / 'index.sig'
        subprocess.run(['openssl', 'pkeyutl', '-sign', '-inkey', str(self.key), '-rawin', '-in', str(document), '-out', str(signature)], check=True, capture_output=True)
        return payload, base64.b64encode(signature.read_bytes())

    def test_discovers_a_version_not_present_in_repository_manifest(self):
        payload, signature = self.signed()
        result = verify_and_discover(payload, signature, self.public)
        self.assertEqual(result['version'], '9.2.0')
        self.assertEqual(result['sha256'], 'a' * 64)
        self.assertEqual(result['url'], 'https://browser.magic-toolkit.com/releases/MagicScript-Setup-9.2.0.pkg')

    def test_tampered_metadata_is_rejected(self):
        payload, signature = self.signed()
        with self.assertRaisesRegex(RuntimeError, 'signature'):
            verify_and_discover(payload.replace(b'9.2.0', b'9.3.0'), signature, self.public)

    def test_unsigned_or_malformed_signature_is_rejected(self):
        payload, _ = self.signed()
        with self.assertRaises(RuntimeError):
            verify_and_discover(payload, b'not a valid signature', self.public)

    def test_even_signed_unsafe_paths_are_rejected(self):
        payload, signature = self.signed(installer_path='../untrusted.pkg')
        with self.assertRaisesRegex(RuntimeError, 'installer'):
            verify_and_discover(payload, signature, self.public)


if __name__ == '__main__':
    unittest.main()
