#!/usr/bin/env python3
"""Opt-in CRC corruption must preserve the cached retry and all other replies."""
import os
import pty
import subprocess
import tempfile
import tty
from pathlib import Path
from jukuhost_linux_pty_test import HOST, ROOT, request, read_exact, wait_log


def crc16(data):
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xa001 if crc & 1 else 0)
    return crc


def main():
    with tempfile.TemporaryDirectory() as temp:
        out = Path(temp)
        volume = out/'disk.img'
        pattern = bytes(range(128))
        volume.write_bytes(pattern*6400)
        master, slave = pty.openpty()
        tty.setraw(master); tty.setraw(slave)
        host = subprocess.Popen([str(HOST), '--machine', 'robotron1715', '--resume-disk',
            '--serial', os.ttyname(slave), '--volume', str(volume),
            '--test-corrupt-read-reply-once', '--log', str(out/'host.log')],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        try:
            wait_log(host, 'serving A:')
            frame = request(0x14, 9, 0, 159, 40)
            os.write(master, frame)
            corrupted = read_exact(master, 139)
            assert crc16(corrupted[:-2]) != int.from_bytes(corrupted[-2:], 'big')
            os.write(master, frame)
            retry = read_exact(master, 139)
            assert crc16(retry[:-2]) == int.from_bytes(retry[-2:], 'big'), (corrupted.hex(), retry.hex())
            assert retry[9:-2] == pattern
            assert corrupted[:-1] == retry[:-1] and corrupted[-1] ^ retry[-1] == 1
            os.write(master, request(0x14, 10, 0, 159, 40))
            following = read_exact(master, 139)
            assert crc16(following[:-2]) == int.from_bytes(following[-2:], 'big')
        finally:
            host.terminate(); host.wait(timeout=5)
            host.stdout.close()
            os.close(master); os.close(slave)
        log = (out/'host.log').read_text()
        assert log.count('injected=1') == 1 and log.count('duplicate-valid-reply=1') == 1
        assert volume.read_bytes() == pattern*6400
        rejected = subprocess.run([str(HOST), '--test-corrupt-read-reply-once',
            '--serial', '/not-a-device', '--volume', str(volume), '--resume-disk'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        assert rejected.returncode == 2
    print('ROBOTRON-FAULT-TEST: PASS (one bad CRC, valid cached retry, raw 800 KiB A:)')


if __name__ == '__main__': main()
