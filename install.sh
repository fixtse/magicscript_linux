#!/usr/bin/env bash
set -euo pipefail
for tool in python3 patch bsdtar curl sha256sum readlink; do
    command -v "$tool" >/dev/null || { echo "Missing required command: $tool. Install it with your distribution's package manager." >&2; exit 1; }
done
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
url=https://downloads.magic-toolkit.com/magicscript/mac/MagicScript-Setup-1.2.3.pkg
curl -fL "$url" -o "$work/setup.pkg"
echo '62e8d3a2bef019fe35fa093f8dae4967ca37daef41931b2719ef2d15e62a0c02  '"$work/setup.pkg" | sha256sum -c -
mkdir "$work/pkg" "$work/payload"
bsdtar -xf "$work/setup.pkg" -C "$work/pkg"
bsdtar -xf "$work/pkg/MagicScript-core.pkg/Payload" -C "$work/payload"
python3 "$(dirname "$(readlink -f "$0")")/install.py" "$work/payload/Library/Application Support/MagicScript/1.2.3"
