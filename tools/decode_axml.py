#!/usr/bin/env python3
"""Decode the metadata subset needed from Android's compiled binary XML (AXML).

Standard-library only. Extracts string-pool names and start-element attributes;
not a replacement for aapt/apktool and intentionally does not rewrite manifests.
"""
from __future__ import annotations
import argparse, json, struct, zipfile
from pathlib import Path

NO_INDEX = 0xFFFFFFFF
TYPE_STRING = 0x03
TYPE_INT_DEC = 0x10
TYPE_INT_HEX = 0x11
TYPE_INT_BOOLEAN = 0x12

def parse_axml(data: bytes) -> dict:
    if len(data) < 8 or struct.unpack_from('<H', data, 0)[0] != 0x0003:
        raise ValueError('Not Android compiled XML (AXML)')
    strings: list[str] = []
    elements: list[dict] = []
    pos = 8
    while pos + 8 <= len(data):
        ctype, header_size, chunk_size = struct.unpack_from('<HHI', data, pos)
        if chunk_size < 8 or pos + chunk_size > len(data):
            raise ValueError(f'Invalid chunk at offset {pos}')
        if ctype == 0x0001:
            string_count, _, flags, strings_start, _ = struct.unpack_from('<IIIII', data, pos + 8)
            offsets = [struct.unpack_from('<I', data, pos + header_size + 4*i)[0] for i in range(string_count)]
            utf8 = bool(flags & 0x100)
            def len8(p: int) -> tuple[int, int]:
                n = data[p]
                if n & 0x80:
                    return ((n & 0x7f) << 8) | data[p+1], p+2
                return n, p+1
            for off in offsets:
                p = pos + strings_start + off
                if utf8:
                    _, p = len8(p)
                    n, p = len8(p)
                    s = data[p:p+n].decode('utf-8', 'replace')
                else:
                    n = struct.unpack_from('<H', data, p)[0]; p += 2
                    if n & 0x8000:
                        n = ((n & 0x7fff) << 16) | struct.unpack_from('<H', data, p)[0]; p += 2
                    s = data[p:p+n*2].decode('utf-16', 'replace').lstrip('\ufeff\ufffe')
                strings.append(s)
        elif ctype == 0x0102:
            line = struct.unpack_from('<I', data, pos + 8)[0]
            name_idx = struct.unpack_from('<I', data, pos + 20)[0]
            attr_start, attr_size, attr_count = struct.unpack_from('<HHH', data, pos + 24)
            name = strings[name_idx] if name_idx < len(strings) else f'<string:{name_idx}>'
            attrs = {}
            p = pos + 16 + attr_start
            for _ in range(attr_count):
                _, attr_name_idx, raw_idx = struct.unpack_from('<III', data, p)
                value_type = data[p + 15]
                value_data = struct.unpack_from('<I', data, p + 16)[0]
                key = strings[attr_name_idx] if attr_name_idx < len(strings) else f'<string:{attr_name_idx}>'
                raw = strings[raw_idx] if raw_idx != NO_INDEX and raw_idx < len(strings) else None
                if value_type == TYPE_STRING:
                    value = strings[value_data] if value_data < len(strings) else raw
                elif value_type == TYPE_INT_BOOLEAN:
                    value = bool(value_data)
                elif value_type == TYPE_INT_DEC:
                    value = value_data
                elif value_type == TYPE_INT_HEX:
                    value = hex(value_data)
                else:
                    value = raw if raw is not None else value_data
                attrs[key] = value
                p += attr_size
            elements.append({'tag': name, 'line': line, 'attributes': attrs})
        pos += chunk_size
    root = next((e for e in elements if e['tag'] == 'manifest'), {})
    app = next((e for e in elements if e['tag'] == 'application'), {})
    sdk = next((e for e in elements if e['tag'] == 'uses-sdk'), {})
    return {
        'package': root.get('attributes', {}).get('package'),
        'version_code': root.get('attributes', {}).get('versionCode'),
        'version_name': root.get('attributes', {}).get('versionName'),
        'min_sdk': sdk.get('attributes', {}).get('minSdkVersion'),
        'target_sdk': sdk.get('attributes', {}).get('targetSdkVersion'),
        'application': app.get('attributes', {}),
        'activities': [e['attributes'] for e in elements if e['tag'] == 'activity'],
        'permissions': [e['attributes'].get('name') for e in elements if e['tag'] == 'uses-permission'],
        'metadata': [e['attributes'] for e in elements if e['tag'] == 'meta-data'],
        'element_count': len(elements),
        'note': 'Read-only metadata extraction; does not modify or re-sign the APK.'
    }

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('apk', type=Path)
    ap.add_argument('--out', type=Path, help='Write JSON to this file (prints to stdout otherwise)')
    args = ap.parse_args()
    with zipfile.ZipFile(args.apk) as zf:
        result = parse_axml(zf.read('AndroidManifest.xml'))
    output = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding='utf-8')
    else:
        print(output, end='')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
