# Replica package geometry readiness

Fabrication package: `fab/gerbers`
Status: **NOT READY**

Package geometry cannot be measured until the required exports exist.
Regenerate the fabrication package from the reviewed board, then run:

```sh
python3 kicad/report_replica_package_geometry.py
```

## Missing or empty inputs

- `fab/gerbers/juku_routed-job.gbrjob`
- `fab/gerbers/juku_routed-Edge_Cuts.gm1`
- `fab/gerbers/juku_routed.drl`

Expected dimensions and drill counts remain configured in the generator;
they are acceptance criteria, not measurements of the current package.
