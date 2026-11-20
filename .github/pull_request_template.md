Describe the concrete change, its owner boundaries and actual verification.
Replace every placeholder below; a declaration is not reviewer approval.
Use exactly one `notelens-scope` block with exact paths, including both ends of
renames/copies. No globs or implicit cross-owner authorization are accepted.

```notelens-scope
{
  "format": "notelens-scope-v1",
  "member": "REPLACE_WITH_A_B_C_OR_D",
  "task": "REPLACE_WITH_TASK_ALIAS",
  "paths": ["replace/with/exact/path"]
}
```

- Actual commands, environments and outcomes:
- Affected owners and real review evidence (agent review versus human approval):
- Remaining dependencies, limits and pending gates:

Keep frozen contracts unchanged unless a separately approved versioned change
explicitly covers them. Coordinated imports need B/affected-owner review and exact
scope; do not self-authorize with a field in this declaration.

F-011/F-014 remain pending unless their distinct completion gates are actually met.
See `docs/team/f-010-review-routing.md` for first-install and policy-change handling.
