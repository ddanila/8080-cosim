# Juku machine profiles

Each record has its own evidence update date. These machine-readable records separate inventory identity, deployed state,
qualified behavior, and unresolved investigations. A finding is local to the
named board unless an explicit cross-board experiment says otherwise. Unknown
values are recorded as `null`; they must not be inferred from a board number.

`machine-profile.schema.json` defines the intended format. The repository test
checks the four-board inventory, selected identity and firmware fields, dates,
evidence-file existence, and the retained CS00015/CS00024 boundaries. It does
not apply the full JSON Schema or repeat physical qualification. Run:

```sh
python3 tests/machine_profiles_test.py
```

The deployment table in [`../machine-deployment-status.md`](../machine-deployment-status.md)
is the human-readable summary. Detailed captures and diagnoses remain in the
evidence files named by each profile.
