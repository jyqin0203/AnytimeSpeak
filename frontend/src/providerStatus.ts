export type SourceState = "llm" | "backend-connected" | "backend-mock" | "local-fallback";

export function sourceFromProvider(provider: string): SourceState {
  if (provider === "llm") return "llm";
  if (provider === "mock") return "backend-mock";
  return "local-fallback";
}

export function sourceLabel(source: SourceState): string {
  if (source === "llm") return "LLM";
  if (source === "backend-connected") return "后端已连接";
  if (source === "backend-mock") return "后端 Mock / Fallback";
  return "前端本地模式";
}

export function providerStatusText(provider: string, fallbackReason?: string | null): string {
  if (provider === "llm") return "本轮来自真实 LLM。";
  if (provider === "mock") return `后端 API 成功，但后端 fallback 到 mock。原因：${fallbackReason ?? "未提供"}`;
  return "前端完全请求不到后端，已使用前端本地模式。";
}

export function providerBadgeText(provider: string): string {
  if (provider === "llm") return "由 LLM 生成";
  if (provider === "mock") return "后端 Mock / Fallback";
  return "前端本地模式";
}
