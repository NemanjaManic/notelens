# B-005 D-005 saved-response replay

The opt-in Windows profile runs the pinned D-005 service on authenticated
loopback with two saved provider responses. The launcher strips provider
configuration and runs the service with a loopback-only network guard. The
replay accepts only the reviewed synthetic document and its recorded question.
It binds saved document IDs to the app-issued ID and preserves the canonical
digest, claims, and exact citation spans. The app labels the replay.

Use the [Windows setup](deployment.md) for the platform. Fetch the reviewed
service commit and prepare a separate clean checkout at
`c7d0797a86061c643b0f23e6d56f8caa9e7a6813`. Use the private
`D005-reviewed-synthetic-service-handoff-v3.zip` supplied by Milica. From the
built platform checkout, set `$reviewedD` and `$privateBundle` to the two paths.

```powershell
uv sync --locked --directory (Join-Path $reviewedD 'services/extraction') --python $platformPython --no-dev
if ($LASTEXITCODE -ne 0) { throw 'Reviewed D-005 setup failed.' }

& $platformPython -B scripts/project/check_d005_replay.py $reviewedD $privateBundle
if ($LASTEXITCODE -ne 0) { throw 'Saved D-005 app replay failed.' }
```

For interactive inspection, start the local stack with the replay flag. Submit
the synthetic text from `notelens_extraction.demo.TEXT` in the reviewed
checkout and ask **Does the patient report cough?** in the document route.

```powershell
& $platformPython -B scripts/project/start_mock.py --d005-replay $reviewedD $privateBundle
```

Run `check_d005_app.py` separately against the pinned `e61140d` mock
handoff for the partial-answer gap, insufficient evidence and out-of-scope
states. The saved provider answer covers one sufficient question. See the
[B-005 acceptance record](integration-status.md#accepted-d-005-saved-response-evidence)
for the replay scope and separate provider-backed verification.
