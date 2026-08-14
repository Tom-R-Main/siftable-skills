# Backend contract

Implement a backend as a local command that reads one JSON object from standard input and writes one JSON object to standard output. Keep logs on standard error.

## Request

```json
{
  "query": "How are worktree candidates classified?",
  "collection": "engineering-notes",
  "limit": 10
}
```

`query` is a non-empty string. `collection` is a string or `null`. `limit` is an integer from 1 through 100.

## Response

```json
{
  "results": [
    {
      "source": "filesystem-notes.md",
      "locator": "lines 120-145",
      "passage": "A candidate is safe_now only when evidence is complete.",
      "score": 0.87,
      "image_path": null,
      "collection": "engineering-notes",
      "metadata": {"retrieval": "hybrid"}
    }
  ]
}
```

Each result requires non-empty string values for `source`, `locator`, and `passage`. `score` must be a finite number when present. `image_path` must be a string or `null`. `metadata` must be an object. `collection` must be a string or `null`.

The wrapper preserves only these fields, rejects malformed results, and truncates the array to the requested limit. The score has backend-specific meaning and must not be interpreted as a calibrated probability.

## Command execution

`LOCAL_CORPUS_COMMAND` is parsed as an argument vector, not evaluated by a shell. Quote paths with spaces using ordinary shell-style quoting inside the variable. Shell pipelines and redirections are intentionally unsupported; place that logic in a reviewed backend script instead.

The wrapper does not load credentials, start databases, search directories, or access the network. Those behaviors belong to the user-configured backend and remain subject to the host agent's authorization rules.
