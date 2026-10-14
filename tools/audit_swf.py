#!/usr/bin/env python3
"""Inventory a compiled SWF without modifying it or attempting decompilation.

Supports uncompressed FWS and zlib-compressed CWS. LZMA-compressed ZWS files
are rejected explicitly rather than being misreported as corrupt.
"""
from __future__ import annotations

import argparse
import collections
import json
import struct
import zlib
from pathlib import Path


TAG_NAMES = {
    0: "End", 1: "ShowFrame", 2: "DefineShape", 6: "DefineBits",
    8: "JPEGTables", 9: "SetBackgroundColor", 11: "DefineText",
    20: "DefineBitsLossless", 21: "DefineBitsJPEG2", 22: "DefineShape2",
    32: "DefineShape3", 33: "DefineText2", 35: "DefineBitsJPEG3",
    36: "DefineBitsLossless2", 37: "DefineEditText", 39: "DefineSprite",
    41: "ProductInfo", 43: "FrameLabel", 56: "ExportAssets",
    65: "ScriptLimits", 69: "FileAttributes", 73: "DefineFontAlignZones",
    74: "CSMTextSettings", 75: " DefineFont3", 76: "SymbolClass",
    77: "Metadata", 78: "DefineScalingGrid", 82: "DoABC",
    83: "DefineShape4", 87: "DefineBinaryData", 88: "DefineFontName",
}


def read_swf(path: Path) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    if len(raw) < 8:
        raise ValueError("File is shorter than the SWF header")
    signature = raw[:3]
    version = raw[3]
    declared_length = struct.unpack_from("<I", raw, 4)[0]
    if signature == b"FWS":
        data = raw
    elif signature == b"CWS":
        try:
            data = b"FWS" + raw[3:8] + zlib.decompress(raw[8:])
        except zlib.error as exc:
            raise ValueError(f"Invalid CWS zlib stream: {exc}") from exc
    elif signature == b"ZWS":
        raise ValueError("ZWS/LZMA SWF is not supported by this inventory tool")
    else:
        raise ValueError(f"Unknown SWF signature: {signature!r}")
    if len(data) != declared_length:
        raise ValueError(
            f"Declared uncompressed length {declared_length} != actual {len(data)}"
        )
    return data, {
        "signature": signature.decode("ascii"),
        "version": version,
        "declared_uncompressed_bytes": declared_length,
        "stored_bytes": len(raw),
    }


def parse_tags(data: bytes) -> dict:
    # RECT starts at byte 8. Its first five bits contain Nbits.
    if len(data) < 12:
        raise ValueError("SWF is too short to contain a frame header")
    nbits = data[8] >> 3
    rect_bytes = (5 + 4 * nbits + 7) // 8
    pos = 8 + rect_bytes
    if pos + 4 > len(data):
        raise ValueError("Truncated SWF frame header")
    frame_rate_raw, frame_count = struct.unpack_from("<HH", data, pos)
    pos += 4
    counts: collections.Counter[int] = collections.Counter()
    abc_blocks = []
    exported_symbols = []
    symbol_classes = []
    labels = []
    ended = False

    while pos < len(data):
        if pos + 2 > len(data):
            raise ValueError("Truncated SWF tag header")
        header = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        code, length = header >> 6, header & 0x3F
        if length == 0x3F:
            if pos + 4 > len(data):
                raise ValueError("Truncated long SWF tag length")
            length = struct.unpack_from("<I", data, pos)[0]
            pos += 4
        end = pos + length
        if end > len(data):
            raise ValueError(f"Tag {code} extends beyond end of file")
        payload = data[pos:end]
        pos = end
        counts[code] += 1

        if code == 82 and length >= 5:  # DoABC
            flags = struct.unpack_from("<I", payload, 0)[0]
            nul = payload.find(b"\0", 4)
            name = payload[4:nul].decode("utf-8", "replace") if nul >= 0 else ""
            abc_blocks.append({
                "name": name, "flags": flags,
                "abc_bytes_including_header": length,
            })
        elif code in (56, 76) and length >= 2:  # ExportAssets / SymbolClass
            count = struct.unpack_from("<H", payload, 0)[0]
            cursor = 2
            for _ in range(min(count, 100000)):
                if cursor + 2 > len(payload):
                    break
                character_id = struct.unpack_from("<H", payload, cursor)[0]
                cursor += 2
                nul = payload.find(b"\0", cursor)
                if nul < 0:
                    break
                name = payload[cursor:nul].decode("utf-8", "replace")
                cursor = nul + 1
                item = {"character_id": character_id, "name": name}
                (exported_symbols if code == 56 else symbol_classes).append(item)
        elif code == 43 and payload:
            labels.append(payload.split(b"\0", 1)[0].decode("utf-8", "replace"))
        if code == 0:
            ended = True
            break

    return {
        "frame_size_rect_bytes": rect_bytes,
        "frame_rate": round(frame_rate_raw / 256, 3),
        "frame_count": frame_count,
        "tag_counts": [
            {"code": code, "name": TAG_NAMES.get(code, "Unknown"), "count": count}
            for code, count in counts.most_common()
        ],
        "abc_blocks": abc_blocks,
        "abc_bytes_total": sum(item["abc_bytes_including_header"] for item in abc_blocks),
        "exported_symbol_count": len(exported_symbols),
        "exported_symbols_sample": exported_symbols[:100],
        "symbol_class_count": len(symbol_classes),
        "symbol_classes_sample": symbol_classes[:100],
        "frame_labels": labels[:100],
        "end_tag_seen": ended,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("swf", type=Path)
    parser.add_argument("--out", type=Path, default=Path("build/swf-audit"))
    args = parser.parse_args()
    if not args.swf.is_file():
        parser.error(f"SWF not found: {args.swf}")
    try:
        data, header = read_swf(args.swf)
        report = {"file": args.swf.name, "header": header, **parse_tags(data)}
    except ValueError as exc:
        parser.error(str(exc))
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "inventory.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Compiled SWF inventory", "",
        f"- File: `{report['file']}`",
        f"- SWF version: {header['version']}",
        f"- Compression: {header['signature']}",
        f"- Uncompressed size: {header['declared_uncompressed_bytes']:,} bytes",
        f"- Frame rate: {report['frame_rate']}",
        f"- Frame count: {report['frame_count']}",
        f"- DoABC blocks: {len(report['abc_blocks'])}",
        f"- ABC payload bytes: {report['abc_bytes_total']:,}",
        f"- Exported symbols: {report['exported_symbol_count']}",
        f"- SymbolClass entries: {report['symbol_class_count']}",
        f"- End tag found: {report['end_tag_seen']}", "",
        "## Tag counts", "",
        "| Tag | Name | Count |", "|---:|---|---:|",
    ]
    lines.extend(
        f"| {item['code']} | {item['name'].strip()} | {item['count']} |"
        for item in report["tag_counts"]
    )
    lines.extend(["", "## ABC blocks", ""])
    lines.extend(
        f"- `{item['name'] or '(unnamed)'}`: {item['abc_bytes_including_header']:,} bytes"
        for item in report["abc_blocks"]
    )
    lines.extend([
        "", "## Limitations", "",
        "This is structural inventory only. It does not decompile ActionScript,",
        "reconstruct original source, prove runtime compatibility, or patch the SWF.",
        "A compiled SWF can contain bytecode and symbols while still lacking the",
        "authoring project and native-extension source. Keep proprietary SWFs out of Git.",
    ])
    (args.out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {args.out / 'report.md'}")
    print(f"Wrote {args.out / 'inventory.json'}")
    print(f"SWF v{header['version']}: {report['frame_count']} frames, "
          f"{len(report['abc_blocks'])} ABC blocks, "
          f"{report['exported_symbol_count']} exported symbols")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
