#!/usr/bin/env bash
set -euo pipefail
for tool in python3 patch bsdtar curl sha256sum tar; do
    command -v "$tool" >/dev/null || { echo "Missing required command: $tool. Install it with your distribution's package manager." >&2; exit 1; }
done
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
# Support both a checkout and curl | bash without requiring git.
source_dir=''
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
    candidate=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
    if [[ -f "$candidate/install.py" && -f "$candidate/release.json" ]]; then
        source_dir=$candidate
    fi
fi
if [[ -z "$source_dir" ]]; then
    curl --fail --location --retry 3 https://codeload.github.com/fixtse/magicscript_linux/tar.gz/refs/heads/main -o "$work/installer.tar.gz"
    tar -xzf "$work/installer.tar.gz" -C "$work"
    source_dir="$work/magicscript_linux-main"
fi
readarray -t release < <(python3 - "$source_dir/release.json" <<'PY'
import json, sys
from urllib.parse import urlparse
r = json.load(open(sys.argv[1], encoding='utf-8'))
assert urlparse(r['url']).scheme == 'https'
assert len(r['sha256']) == 64 and all(c in '0123456789abcdef' for c in r['sha256'])
print(r['url'])
print(r['sha256'])
print(r['version'])
PY
)
[[ ${#release[@]} -eq 3 ]] || { echo 'Invalid release manifest.' >&2; exit 1; }
curl --fail --location --retry 3 "${release[0]}" -o "$work/setup.pkg"
echo "${release[1]}  $work/setup.pkg" | sha256sum -c -
mkdir "$work/pkg" "$work/payload"
bsdtar -xf "$work/setup.pkg" -C "$work/pkg"
bsdtar -xf "$work/pkg/MagicScript-core.pkg/Payload" -C "$work/payload"
python3 "$source_dir/install.py" "$work/payload/Library/Application Support/MagicScript/${release[2]}" "$@"
