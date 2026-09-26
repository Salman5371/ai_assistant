# Final project audit - 2026-09-26

Scope: current application source, dependency manifests, tests, documentation,
local model inventory, generated files, and credential-pattern scans. No features
were added. Existing uncommitted work from earlier tasks was preserved.

## Verified fixes in this audit

| Files | Verified problem and fix |
| --- | --- |
| `requirements.txt` | Replaced `opencv-python==4.13.0.92` with `opencv-contrib-python==4.13.0.92`. MediaPipe requires the latter; declaring both installs overlapping `cv2` files. |
| `evaluation/latency.py` | Invalid run/warmup counts and existing output files are rejected before decoding audio or loading models. A probe confirmed the old invalid-run path still invoked model loading. |
| `assistant/models.py`, `assistant/pipeline.py`, `streamlit_app.py` | Expected UI restrictions now reach the user rather than becoming a generic command-processing error. |
| `audio_intelligence/recorder.py` | Rejects invalid sample rates and oversized PCM payload declarations before reading samples. Shared WAV payload limit is 128 MiB; stricter consumer limits remain. |
| `audio_intelligence/audio_event_classifier.py` | Corrected a stale module description claiming models were never downloaded, despite its lazy pretrained backend. |
| `tests/test_final_audit.py` | Added three microphone-free regression tests for the verified fixes. |
| `README.md` | Corrected OpenCV installation guidance and documented the WAV limit and unusable old environment. |
| `FINAL_AUDIT.md` | This report. |

No other project dependencies were added. The isolated `.venv-visualization`
environment was populated with the existing declared base/UI/Whisper/emotion/event
runtimes so real imports could be tested. Ruff was installed there as an audit-only
tool; it was not added to application requirements.

## Verification

- Baseline: 98 tests passed.
- Final: **101 tests passed, 0 failed, 0 skipped**, including Streamlit AppTest and PNG rendering checks.
- **42 project modules imported successfully**, without launching hardware or downloading weights.
- Real imports passed for SpeechRecognition, pyttsx3, OpenCV, MediaPipe, sounddevice,
  Wikipedia, NumPy, Matplotlib, Streamlit, Torch, Transformers and faster-whisper.
- Actual Transformers AST feature extraction on synthetic audio succeeded with
  shape `(1, 1024, 128)`. This is an integration check, not an accuracy benchmark.
- All three existing OpenCV DNN networks loaded successfully; no camera opened.
- All seven expected vision model files exist. The hand task file was inventoried,
  but no MediaPipe hand inference was run.
- Pinned AST config, feature-extractor config and safetensors URLs returned HTTP 200
  using header-only requests. Audio-model weights were not downloaded for this audit.
- `pip check`: no broken requirements in the tested environment.
- 56 Python files parsed successfully; `git diff --check` passed.
- Ruff undefined-name/redefinition/unbound-local/unused-local checks passed
  (`F821,F822,F823,F811,F841`). F401 reports intentional service-registry imports and
  compatibility re-exports; these were reviewed and retained, not blindly deleted.
- Credential-pattern scans found no matching files in the working tree or 21 Git
  revisions. This is a bounded pattern scan, not a guarantee that no secret exists.
- No unexpected temporary files or secret-named configuration files were found.
  Generated sample plots and the audit test log remain in ignored directories.
- SQLite files/sidecars, secrets configuration, logs, models and plots are ignored.
  Legacy memory and notes remain locally and are no longer tracked in the current
  index; prior commits may still contain them.

## Tested environment

Python 3.12, NumPy 2.4.4, OpenCV contrib 4.13.0.92, MediaPipe 0.10.35,
SpeechRecognition 3.16.1, sounddevice 0.5.5, pyttsx3 2.99, Streamlit 1.64.0,
Matplotlib 3.11.2, Torch 2.14.0+cpu, Transformers 4.57.6, faster-whisper 1.2.1.
This records the audit environment, not a new dependency lockfile.

Non-fatal warnings: the sandbox blocked Matplotlib's user-home font-cache write;
Streamlit AppTest reported bare-context warnings; upstream AST's NumPy extractor
warned about empty Mel filters with its default settings. The checks completed.
Pretrained feature settings were not altered to silence an upstream warning.

## Run commands (PowerShell, project root)

```powershell
$py = ".\.venv-visualization\Scripts\python.exe"
& $py main.py
& $py -m streamlit run streamlit_app.py
& $py -B -m unittest discover -s tests -v
& $py -m pip check
& $py -m evaluation.latency --help
```

For a fresh machine, follow the Python 3.12 environment and optional dependency
instructions in README.md. Do not reuse the old `.venv-1` here: launching its
interpreter returned Access denied. It was left intact rather than deleting the
user's environment. Test output is in ignored `logs/final-audit-tests.txt`.

## Manual verification and intentional limits

- Verify microphone permissions/devices, browser recording, speaker output/voice
  choice, camera capture, and gesture handedness on the target machine.
- Verify first-use audio-model downloads and actual Whisper/emotion/event inference
  with authorized audio. No model accuracy, F1, WER or inference benchmark is claimed.
- Test browser/app/folder launch on your installation. Power commands were mocked;
  exercise them only when a real shutdown/restart is intended.
- The UI remains localhost-only, single-user and synchronous. Native camera windows
  are terminal-only; chat is rule-based, with no LLM/API integration.
- The file organizer is a documented standalone helper, and injected model adapters
  are compatibility APIs. They are intentionally retained rather than treated as
  dead code or connected as new features.
- `clear memory` removes active SQLite rows, not the retained migration backup or
  historical Git content. Local storage is not encrypted.
