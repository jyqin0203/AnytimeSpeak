import assert from "node:assert/strict";
import test from "node:test";

import {
  providerBadgeText,
  providerStatusText,
  sourceFromProvider,
  sourceLabel,
} from "../src/providerStatus.ts";

test("non-LLM backend connectivity has a neutral connected label", () => {
  assert.equal(sourceLabel("backend-connected"), "后端已连接");
});

test("provider results keep distinct LLM, backend fallback, and frontend local labels", () => {
  assert.equal(sourceFromProvider("llm"), "llm");
  assert.equal(sourceFromProvider("mock"), "backend-mock");
  assert.equal(sourceFromProvider("local-fallback"), "local-fallback");
  assert.equal(sourceLabel("llm"), "LLM");
  assert.equal(sourceLabel("backend-mock"), "后端 Mock / Fallback");
  assert.equal(sourceLabel("local-fallback"), "前端本地模式");
  assert.equal(providerBadgeText("mock"), "后端 Mock / Fallback");
  assert.match(providerStatusText("mock", "llm_timeout"), /llm_timeout/);
});
