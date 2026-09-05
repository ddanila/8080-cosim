#!/usr/bin/env python3
"""Build an experimental original/peak-normalized DOOM JPS v1 listening disk."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
FIRMWARE = ROOT / 'spinoffs/jukupoly/firmware'
sys.path.insert(0, str(FIRMWARE))
import build_doom_library as library
import build_jukupoly as compiler


def normalize(payload: bytes) -> tuple[bytes, dict]:
    """Scale held-tone nibbles and PCM by one gain; leave timing/pointers intact.

    This intentionally accepts only the flat, held-envelope v1 output used by
    the baseline DOOM converter. It does not normalize the OR-mixed waveform.
    """
    def require(ok: bool, message: str) -> None:
        if not ok:
            raise ValueError(message)

    def word(offset: int) -> int:
        require(0 <= offset <= len(payload) - 2, 'word outside JPS')
        return int.from_bytes(payload[offset:offset + 2], 'little')

    require(len(payload) >= 16 and payload[:4] == b'JPS\x01', 'requires JPS v1')
    require(word(4) == len(payload) and payload[7] == 0, 'invalid size/capability')
    require(payload[14:16] == b'\0\0', 'reserved header bytes')
    frame_samples = payload[6]
    require(64 <= frame_samples <= 255, 'invalid frame size')
    rows = word(10) - 0x1800
    silence = word(12) - 0x1800
    require(16 <= rows < silence <= len(payload) - frame_samples, 'invalid row bounds')
    require(not any(payload[silence:silence + frame_samples]), 'nonzero silence')
    tones: set[int] = set()
    pcm: set[int] = set()
    descriptors: set[int] = set()
    position = rows
    while True:
        require(position + 2 <= silence, 'unterminated rows')
        duration, flags = payload[position:position + 2]
        position += 2
        if flags == 0x80:
            require(duration == 0 and position == silence, 'invalid end marker')
            break
        require(duration > 0 and flags & ~0x1f == 0, 'unsupported row flags')
        for bit in (1, 2, 4):
            if flags & bit:
                require(position + 2 <= silence, 'truncated tone')
                step = word(position)
                position += 2
                if step:
                    require(position + 2 <= silence, 'truncated tone levels')
                    require(payload[position] == 255 and
                            payload[position + 1] >> 4 == 2,
                            'only held baseline tones are supported')
                    require(payload[position + 1] & 15 != 0, 'zero tone volume')
                    tones.add(position + 1)
                    position += 2
        if flags & 8:
            position += 2
        if flags & 16:
            require(position + 2 <= silence, 'truncated drum pointer')
            descriptors.add(word(position) - 0x1800)
            position += 2
        require(position <= silence, 'row exceeds extent')
    descriptor_bytes: set[int] = set()
    for descriptor in descriptors:
        require(silence + frame_samples <= descriptor <= len(payload) - 3,
                'invalid drum descriptor')
        descriptor_bytes.update(range(descriptor, descriptor + 3))
        start = word(descriptor) - 0x1800
        length = payload[descriptor + 2] * frame_samples
        require(length > 0 and start >= silence + frame_samples and
                start + length <= len(payload), 'invalid PCM extent')
        pcm.update(range(start, start + length))
    require(not pcm & descriptor_bytes, 'PCM overlaps descriptors')
    require(all(payload[offset] <= 15 for offset in pcm), 'PCM exceeds nibble')
    tone_peak = max((payload[offset] & 15 for offset in tones), default=0)
    pcm_peak = max((payload[offset] for offset in pcm), default=0)
    peak = max(tone_peak, pcm_peak)
    result = bytearray(payload)
    if peak:
        # Nearest integer, half upward. Zero stays zero; peak becomes 15.
        scale = lambda level: (30 * level + peak) // (2 * peak)
        for offset in tones:
            result[offset] = (payload[offset] & 0xf0) | scale(payload[offset] & 15)
        for offset in pcm:
            result[offset] = scale(payload[offset])
    return bytes(result), {
        'tone_peak': tone_peak, 'pcm_peak': pcm_peak, 'component_peak': peak,
        'gain': 15 / peak if peak else 1,
        'changed_bytes': sum(a != b for a, b in zip(payload, result)),
        'original_sha256': hashlib.sha256(payload).hexdigest(),
        'normalized_sha256': hashlib.sha256(result).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((args.library / 'catalog.json').read_text())['tracks']
    selected = (2, 6, 13)
    report, records, files = [], [], []
    for original_track in selected:
        track = catalog[original_track - 1]
        original = (args.library / 'songs' / track['filename']).read_bytes()
        if hashlib.sha256(original).hexdigest() != track['payload_sha256']:
            raise ValueError(f"catalog hash mismatch: {track['filename']}")
        normalized, stats = normalize(original)
        assert normalize(normalized)[0] == normalized
        report.append({'track': original_track, 'title': track['title'], **stats})
        for label, data in [('original', original), ('normalized', normalized)]:
            number = len(records) + 1
            song = output / f'D1T{number:02}.JPS'
            song.write_bytes(data)
            files.append(song)
            title = track['title'].replace("'", '') + ' ' + label
            minutes, seconds = divmod(round(track['duration_seconds']), 60)
            records.append(f"track{number:02}: db 1,{number},{minutes},{seconds},'{title}','$'")
    # A separate six-entry shell; the playback engine is unchanged.
    for source in FIRMWARE.glob('*.inc'):
        shutil.copyfile(source, output / source.name)
    player_source = output / 'jukupoly-player-0100.asm'
    shutil.copyfile(FIRMWARE / player_source.name, player_source)
    shell = output / 'jukupoly-library-shell.inc'
    text = shell.read_text()
    text = text.replace('TRACK_COUNT     equ     44', 'TRACK_COUNT     equ     6')
    text = text.replace('JukuPoly DOOM library', 'JukuPoly normalization A/B')
    text = text.replace('44 tracks - DOOM + DOOM II - 2:13:28', '3 original / normalized pairs')
    text = text.replace('01-44', '01-06').replace('through 44', 'through 06')
    text = text.replace('Catalog page (L shows the next 11 tracks):', 'Choose original or normalized:')
    text = text[:text.index('track_pointers:')] + 'track_pointers:\n        dw ' + ','.join(f'track{i:02}' for i in range(1, 7)) + '\n' + '\n'.join(records) + '\n'
    shell.write_text(text)
    player = output / 'JUKEBOX.COM'
    subprocess.run([str(compiler.executable()), '--nmnv', '--zmac', '-8',
                    '-P2=1', '-P4=1', f'-I{output}', '-o', str(output / 'player.cim'),
                    str(player_source)], check=True)
    player.write_bytes((output / 'player.cim').read_bytes())
    if player.stat().st_size >= compiler.SONG_LOAD_ADDRESS - 0x100:
        raise ValueError('trial player overlaps the song load address')
    logical = output / 'logical.cpm'
    library.cpm_run(['mkfs.cpm', '-f', library.DISK_FORMAT, str(logical)])
    for path in [player, *files]:
        library.cpm_run(['cpmcp', '-f', library.DISK_FORMAT, str(logical),
                         str(path), '0:' + path.name])
    disk = output / 'normalization-ab.cpm'
    library.logical_to_native(logical, disk)
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'disk': str(disk), 'tracks': report}, indent=2))


if __name__ == '__main__':
    main()
