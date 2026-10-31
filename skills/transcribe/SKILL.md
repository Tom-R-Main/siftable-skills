---
name: transcribe
description: Transcribe speech from authorized audio or video recordings, optionally with timestamps or speaker labels, and verify uncertain passages against the recording.
license: Apache-2.0
---

# Transcribe recordings

Establish the input files, requested output format, language hints, timestamp needs, and whether speaker labels are requested. Preserve supplied speaker identities; otherwise use neutral labels and mark uncertainty. A speaker label is not verified identity.

Prefer an available transcription connector or project-configured local transcriber. Inspect its supported file sizes, formats, diarization, and chunking controls before sending data. This package does not bundle a provider client, model, or credentials. Using a remote provider must fit the user's existing authorization to transmit the recording and incur its cost.

For long recordings, use supported chunking and retain offsets so segments map back to the source. Keep the original recording intact. Do not fabricate inaudible words or silently collapse overlapping speakers. Distinguish verbatim transcription from requested cleanup, summary, or translation.

Check representative segments and every material uncertain passage against the audio. Verify timestamp alignment and speaker consistency when requested. Treat names, numbers, quotations, and domain terms as likely error points; mark unresolved words rather than guessing.

Use configured opaque credentials. Never print keys, read credential files, or request keys in chat. Missing tools or authentication are capability gaps, and dependency installation follows the user's permissions.

Save outputs in the authorized workspace or user-selected location with stable names. Deliver the transcript and report language, coverage, speaker-label limits, and unresolved passages. Do not publish or send recordings or transcripts to other people without authorization.
