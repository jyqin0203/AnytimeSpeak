# Backend Connected Status Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show `后端已连接` after successful non-LLM API calls without changing provider-backed status labels.

**Architecture:** Keep provider mapping in the frontend. Add one frontend-only source state for successful connectivity calls, while preserving the existing `llm`, `mock`, and local fallback mappings for coaching results.

**Tech Stack:** React, TypeScript, Vite, Node test runner

---

### Task 1: Extract And Test Source Status Mapping

**Files:**
- Create: `frontend/src/providerStatus.ts`
- Create: `frontend/tests/providerStatus.test.ts`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/package.json`

- [ ] **Step 1: Write a failing Node test**

Test that `backend-connected` maps to `后端已连接`, while `llm`, `mock`, and
local fallback retain their existing labels.

- [ ] **Step 2: Run the test and verify it fails**

Run: `npm run test:provider-status`

Expected: FAIL because the status module does not exist.

- [ ] **Step 3: Implement the minimal status module**

Export the source type, provider mapping, banner label, provider status text,
and badge label from `frontend/src/providerStatus.ts`.

- [ ] **Step 4: Use `backend-connected` for scenario/session success**

Replace the two `setSource("backend-mock")` calls that follow successful
`/api/scenarios` and `/api/sessions` requests with
`setSource("backend-connected")`.

- [ ] **Step 5: Verify**

Run:

```powershell
npm run test:provider-status
npm run build
```

Expected: both commands exit successfully.
