# Missing or Unresolved Files / References

## Summary
- Source file copy stage: no missing source files were encountered for the selected chatbot pack set.
- However, there are path-resolution mismatches to note for methodology references.

## Path-resolution note
Some methodology files reference original repository-relative paths such as:
- `outputs/...`
- `DOCS/...`
- `src/...`
- `app/...`

In this chatbot pack, files are organized under themed folders:
- `context_core/...`
- `context_technical/...`
- `dashboards/...`
- `app_or_demo/...`
- `optional_reference/...`

This means path strings in methodology text are semantically correct but may not be literal relative paths inside this pack.

## Why this matters
- For automated path-following tools, raw path strings from methodology docs may not resolve directly.
- For chatbot Q&A grounding, this is low risk because the referenced files are included, just under prefixed pack folders.

## Can the chatbot still answer reliably?
Yes, with `chatbot_context_manifest.csv` used as the file map.

## Substitute strategy applied
No data substitutions were made.
The actual referenced artifacts were included in the pack and mapped by manifest category/priority.
