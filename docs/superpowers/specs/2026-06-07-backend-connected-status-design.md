# Backend Connected Status Design

## Goal

Stop labeling successful scenario-list and session-start API calls as
`后端 Mock / Fallback`, because those endpoints do not call an LLM.

## Design

Add a frontend-only `backend-connected` source state. Use it after
`/api/scenarios` and `/api/sessions` succeed. Display `后端已连接`.

Provider-backed endpoints keep their existing mapping:

- `provider=llm` -> `LLM`
- `provider=mock` -> `后端 Mock / Fallback`
- frontend request failure -> `前端本地模式`

No backend API contract, provider value, or fallback behavior changes.

## Verification

Test the source labels and provider mapping, then run the frontend production
build and verify the running page is served successfully.
