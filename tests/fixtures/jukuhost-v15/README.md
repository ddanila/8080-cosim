# Hermetic Juku host V15 fixtures

These artifacts let the always-on native-host tests run in a clean checkout;
CI must not depend on an untracked sibling `cpm-plus-juku` worktree.

They are copied byte-for-byte from the `prebuilt/` directory of
`ddanila/cpm-plus-juku` commit
`7e0d92bc1299d97deef315fc65d0c035fe8e6a47`. `SHA256SUMS` pins their exact
identity, and the native-host gate verifies it before running the tests.

Set `CPM_PLUS_JUKU_ROOT` explicitly to exercise another checkout's `out/`
artifacts during development. Without that override, tests always use these
pinned fixtures.
