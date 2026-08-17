# Juku machine profiles

Status date: 2026-08-18

These machine-readable records separate inventory identity, deployed state,
qualified behavior, and unresolved investigations. A finding is local to the
named board unless an explicit cross-board experiment says otherwise. Unknown
values are recorded as `null`; they must not be inferred from a board number.

`machine-profile.schema.json` defines the checked format. Run:

```sh
python3 tests/machine_profiles_test.py
```

The deployment table in [`../machine-deployment-status.md`](../machine-deployment-status.md)
is the human-readable summary. Detailed captures and diagnoses remain in the
evidence files named by each profile.
