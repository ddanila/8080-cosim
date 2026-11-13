# Two writable disk images

`--drive-b FILE` retains its read-only default. Add `--drive-b-writable` to
persist B: through its independent `FILE.jhj` crash journal. `--writable`
continues to affect A: only. Duplicate requests do not repeat transactions.
Both writable journals recover before service starts; invalid journals stop
startup. The protocol and capability byte layout remain unchanged.

Kaypro permits B: in raw native800 order, matching A: and its BIOS. Juku B:
keeps its historical native-image track conversion, with either permission.
Configuration-file B: entries remain read-only; this release enables writable
B: explicitly through the CLI. The Kaypro launcher creates independent session
copies and binds both source identities and permissions to session metadata.

POSIX images are locked shared for read-only access, exclusively for writable
access. A second writer, including through a hard-link alias, cannot open the
same media. The host rejects identical A:/B: path strings.

`tests/jukuhost_two_writable_test.py` covers A:/B: writes, duplicate requests,
recovery of both journals, read-only B: and raw Kaypro track ordering.
