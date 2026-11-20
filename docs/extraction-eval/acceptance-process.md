# Development acceptance decisions

The D-011 proposal in `eval/config/acceptance.json` preserves the required
complete schema/span validity rates. Quality thresholds remain unset pending
development measurements and named team decisions. The initial quality entries
cover entity F1, topic recall and answer risk and can be extended by agreement.

Run `python -m notelens_eval.acceptance --config CONFIG --measurement MEASUREMENT`.
A measurement supplies `version`, matching `acceptance_version`, positive integer
`sample_count`, and a `metrics` object using the criterion names. Rates must be
between zero and one. A quality threshold requires `decision_by` and
`decision_record` fields on its criterion.

Missing measurements or decisions yield pending status. A measured threshold
violation yields failed status. Only complete passing criteria yield passed
status and exit code zero. The evaluator reads inputs without updating them.
The configuration is a proposal awaiting quality decisions and measured evidence.
