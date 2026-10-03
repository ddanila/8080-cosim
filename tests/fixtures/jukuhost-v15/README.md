# Hermetic Juku host V15 fixtures

These artifacts let the V15 tests in the native Linux gate run in a clean checkout;
CI must not depend on an untracked sibling `cpm-plus-juku` worktree.

They are copied byte-for-byte from the `prebuilt/` directory of
`ddanila/cpm-plus-juku` commit
`7e0d92bc1299d97deef315fc65d0c035fe8e6a47`. `SHA256SUMS` pins their exact
identity, and `sync/jukuhost_linux_check.sh` verifies it before running the tests.

`tests/jukuhost_v15_delayed_pty_test.py` and
`tests/jukuhost_stock_v15_cosim_test.py` use these fixtures by default. Set
`CPM_PLUS_JUKU_ROOT` to exercise another checkout's `out/` artifacts in those
tests. The gate still checks the pinned fixture hashes even with that override.
Other host cosim tests select their own artifacts; this directory does not
replace every dependency on a sibling checkout.
