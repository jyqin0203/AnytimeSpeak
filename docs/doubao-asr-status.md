# Doubao ASR 接入状态与调试记录

> 文档目的：记录豆包语音识别接入的当前状态、已验证的信息、未解决的问题，供后续 agent 继续推进。

---

## 当前实现概览

### 已完成的功能（可用）

- **前端 Provider 架构**：`frontend/src/speech/doubaoSpeechProvider.ts` 实现了 `SpeechInputProvider` 接口，可替换浏览器 SpeechRecognition。
- **自动回退**：豆包 WebSocket 连接失败时，`App.tsx` 自动切换回 `browserSpeechInputProvider`（不降级到文字输入）。
- **后端代理端点**：`GET /api/asr/mode` 返回当前 ASR 模式；`WS /ws/asr` 代理音频到豆包服务。
- **环境变量校验**：三个变量（APP_ID、TOKEN、RESOURCE_ID）缺任意一个都会回退到 browser 模式。
- **测试覆盖**：11 个 pytest 测试，全部通过。
- **构建验证**：`npm run build` 通过，TypeScript 无报错。

### 关键文件

| 文件 | 作用 |
|---|---|
| `backend/app/asr_provider.py` | 豆包 ASR 代理逻辑 |
| `backend/tests/test_asr.py` | ASR 单元测试 |
| `frontend/src/speech/doubaoSpeechProvider.ts` | 前端 Provider |
| `frontend/src/App.tsx` | ASR Provider 切换逻辑 |
| `.env.example` | 凭据配置示例 |

---

## 豆包语音 API 调试记录

### 凭据体系（重要）

火山引擎语音服务有**两套完全不同的 API 体系**，凭据来源不同：

#### V2 标准流式语音识别（用户目前订阅的）

- **服务页面**：火山引擎控制台 → 豆包语音 → 应用管理
- **WebSocket URL**：`wss://openspeech.bytedance.com/api/v2/asr`
- **认证方式**：
  - HTTP Header：`Authorization: Bearer;{token}`（注意是分号不是空格）
  - JSON body 中也需包含：`app.appid`、`app.token`、`app.cluster`
- **用户凭据**：
  - `DOUBAO_APP_ID`：10 位数字，如 `5498842689`
  - `DOUBAO_ASR_TOKEN`：32 位 hex 字符串（从应用管理页复制 Token）
- **Cluster 映射**：
  - `volcengine_streaming_common` → resource `volc.streamingasr.common.cn`
  - `volcengine_streaming` → resource `volc.streamingasr.office.cn`
  - 其他 cluster 名称均返回空 resource_id（无效）
- **二进制帧协议**：V2 使用 GZIP 压缩的二进制 WebSocket 帧（**不是 JSON text 帧**）

#### V3 大模型流式语音识别（BigModel）

- **WebSocket URL**：`wss://openspeech.bytedance.com/api/v3/sauc/bigmodel`
- **认证 Headers**（均需正确设置，缺一不可）：
  - `X-Api-App-Key: {app_id}`
  - `X-Api-Access-Key: {token}`（此处的 token 是 V2 App Token 还是 IAM AK 尚不明确）
  - `X-Api-Resource-Id: {resource_id}`（如 `volc.bigasr.sauc.duration`）
  - `X-Api-Connect-Id: {随机UUID}`
- **二进制帧协议**：V3 使用带 GZIP 压缩的二进制帧，格式见下方

---

### 实测错误记录

| 错误 | 原因 | 解决状态 |
|---|---|---|
| `"get resource id empty"` | URL query param 不对，应放 Header | ✅ 已修复 |
| `"resourceId xxx is not allowed"` | 该 resource_id 对此账号没有权限 | ❌ 未解决 |
| `"load grant: requested grant not found in SaaS storage"` | 服务未开通或凭据类型错误 | ❌ 未解决 |
| `"missing Authorization header"` | V2 API 需要 `Authorization: Bearer;{token}` | ✅ 已知 |
| `"requested resource not granted"` | V2 cluster 对应的资源未授权 | ❌ 未解决 |
| WebSocket 1007 with "invalid continuation byte" | 声明了 GZIP 压缩但实际发送未压缩数据 | ✅ 已知原因 |

---

### V2/V3 二进制帧协议（使用 `volcengine-audio` 库）

官方 Python 库 `volcengine-audio`（PyPI 可安装）已实现正确的二进制帧格式：

```python
from volcengine_audio.stt import VolcengineAsrFunctionsV2, VolcengineAsrFunctionsV3

# V2 init 帧（无 sequence，GZIP 压缩）
frame = bytes(VolcengineAsrFunctionsV2.full_client_request(params, compression=True))

# V3 init 帧（有 sequence，GZIP 压缩）
frame = bytes(VolcengineAsrFunctionsV3.generate_asr_full_client_request(seq=1, request_params=params, compression=True))

# V3 音频帧
audio_frame = bytes(VolcengineAsrFunctionsV3.generate_asr_audio_only_request(seq=2, audio=pcm_bytes))

# V3 结束帧（空音频 + 负 sequence）
end_frame = bytes(VolcengineAsrFunctionsV3.generate_asr_audio_only_request(seq=3, audio=b''))

# 解析 V3 响应
result = VolcengineAsrFunctionsV3.parse_response(binary_data)
# result 包含: is_last_package, sequence, message (dict with results)
```

V3 响应 JSON 结构（GZIP 解压后）：
```json
{
  "result": [
    {
      "text": "识别文字",
      "definite": true,
      "utterances": [...]
    }
  ]
}
```

`definite=true` 表示最终结果，`definite=false` 表示中间结果（partial）。

---

### 未解决的核心问题

#### 问题 1：用户使用 V2 标准流式 ASR，但代码实现的是 V3 BigModel

用户在豆包语音控制台订阅的是 **流式语音识别**（V2），对应：
- `DOUBAO_RESOURCE_ID=volc.streamingasr.common.cn`（而非 `volc.seedasr.sauc.duration`）
- 需要 cluster=`volcengine_streaming_common`

但 V2 cluster `volcengine_streaming_common` 也返回 403，可能原因：
1. 服务已开通但未绑定到当前 APP（5498842689）
2. 计费账户余额问题
3. 服务需要单独在控制台激活某个功能

#### 问题 2：Ark 平台语音识别（可能更简单的方案）

用户提到在 `https://console.volcengine.com/ark/region:ark+cn-beijing/tts/speechRecognition` 控制台页面看到了一个更简单的接入方式（用 Ark API Key）。

**该接口尚未调研清楚**，可能是：
- `wss://ark.cn-beijing.volces.com/api/v3/audio/realtime`（类似 OpenAI Realtime API）
- 使用与 LLM 相同的 Ark API Key（`Authorization: Bearer {api_key}`）
- 需要从控制台获取 model_id（类似 `ep-xxxx` 格式）

这可能是最简单的接入方案，**建议优先调研**。

---

## 当前 .env 配置

用户的 `.env` 当前内容（key 已脱敏）：

```
ASR_PROVIDER_MODE=doubao
DOUBAO_APP_ID=5498842689          # V2 应用 ID
DOUBAO_ASR_TOKEN=***（32字符）     # V2 App Token（从应用管理复制）
DOUBAO_RESOURCE_ID=volc.seedasr.sauc.duration  # 需要确认！可能应为 volc.streamingasr.common.cn
```

---

## 后续 Agent 建议的工作顺序

### 优先级 1：调研 Ark 平台语音识别接口

1. 让用户访问 `https://console.volcengine.com/ark/region:ark+cn-beijing/tts/speechRecognition`
2. 截图或粘贴页面上的 API 示例代码（Python/curl 示例、WebSocket URL、Model ID）
3. 根据文档重新实现后端代理（可能只需简单的 Bearer token + WebSocket）

### 优先级 2：修复 V2 标准流式 ASR（如果 Ark 方案不可行）

1. 确认用户已在控制台激活 `volcengine_streaming_common` 对应的服务
2. 将后端代理改用 `volcengine-audio` 库的 V2 实现：
   - 正确的 GZIP 二进制帧
   - `Authorization: Bearer;{token}` + JSON body 含 `app.token`
   - cluster=`volcengine_streaming_common`
3. 更新 `.env.example` 去掉 `DOUBAO_RESOURCE_ID`（V2 不用）

### 优先级 3：V3 BigModel（最复杂）

需确认用户是否已开通大模型流式识别服务，并提供对应凭据。

---

## 参考资源

- 官方 Python 库：`pip install volcengine-audio`（包含正确的二进制帧实现）
- 官方文档：https://www.volcengine.com/docs/6561/1354869（需浏览器，JS 渲染）
- 鉴权说明：https://www.volcengine.com/docs/6561/1105162
- Ark 控制台语音识别：https://console.volcengine.com/ark/region:ark+cn-beijing/tts/speechRecognition
