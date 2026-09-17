# API notes

All `/api/*` routes except authentication and health require `Authorization: Bearer <JWT>`. Uploads accept PDF/PNG/JPG/JPEG. The generated structured extraction is source-derived and Q&A returns source excerpts; absent facts return exactly `Not mentioned in the notice.`
