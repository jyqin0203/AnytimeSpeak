# feat: add Doubao BigModel Streaming ASR

## Feature Description

Adds Doubao (Volcano Engine / ByteDance) BigModel Streaming ASR as an optional speech recognition provider for the practice chat loop.

The feature keeps the MVP demo stable:

- Default mode remains browser speech recognition / text input.
- Real Doubao ASR is enabled only when `.env` is configured.
- Missing credentials fall back to browser mode.
- The frontend streams microphone audio to the backend and receives real-time `partial` / `final` transcript events.

## Implementation Approach

### Backend

- Added `backend/app/asr_provider.py` provider logic for Doubao BigModel ASR V3.
- Uses `volcengine-audio` to generate and parse the required binary WebSocket frames.
- Supports new Volcano Engine console auth via `DOUBAO_API_KEY` + `DOUBAO_RESOURCE_ID`.
- Keeps legacy console auth support via `DOUBAO_APP_ID` + `DOUBAO_ASR_TOKEN` + `DOUBAO_RESOURCE_ID`.
- Defaults to the recommended async endpoint:

```text
wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async
```

- Adds `GET /api/asr/mode` so the frontend can detect whether Doubao is configured.
- Adds `WebSocket /ws/asr` to relay PCM audio from the browser to Doubao and relay transcripts back.
- Handles Doubao response shapes where transcript text is under `message.result.text` and finality is under `utterances[].definite`.

### Frontend

- Adds `frontend/src/speech/doubaoSpeechProvider.ts` implementing the existing `SpeechInputProvider` interface.
- Captures microphone audio as PCM 16-bit, 16 kHz, mono.
- Sends audio chunks as binary frames to `/ws/asr`.
- Sends `{"type":"end"}` on stop and keeps the WebSocket open long enough to receive final transcripts.
- Treats Doubao transcripts as provider-owned full text, avoiding repeated concatenation in the input box.
- Falls back to browser speech recognition if Doubao reports an error.

### Configuration

New console:

```env
ASR_PROVIDER_MODE=doubao
DOUBAO_API_KEY=your-new-console-app-key
DOUBAO_RESOURCE_ID=volc.seedasr.sauc.duration
DOUBAO_ASR_URL=wss://openspeech.bytedance.com/api/v3/sauc/bigmodel_async
DOUBAO_RESULT_TYPE=full
```

Legacy console:

```env
ASR_PROVIDER_MODE=doubao
DOUBAO_APP_ID=your-app-id
DOUBAO_ASR_TOKEN=your-access-token
DOUBAO_RESOURCE_ID=volc.bigasr.sauc.duration
```

## Test Method

Automated checks:

```bash
pytest backend\tests
cd frontend
npm run build
```

Manual / integration checks:

- Verified `/api/asr/mode` returns `doubao` when `.env` has valid Doubao config.
- Verified direct Doubao WebSocket initialization succeeds with the configured API key and resource ID.
- Verified a 200 ms PCM audio packet is accepted by Doubao.
- Verified a full WAV speech sample sent through local `/ws/asr` returns streaming `partial` events and a final transcript:

```text
Hello, this is a speaking test for anytime speak. I want to practice English conversation today.
```

## Third-Party Libraries, APIs, and AI-Generated Code

- `volcengine-audio==0.2.4` for Doubao ASR V3 binary frame generation and parsing.
- `websockets==14.1` for backend outbound WebSocket connections.
- Volcano Engine Doubao BigModel Streaming ASR API.
- Browser Web Audio API for microphone capture.
- Code produced with AI assistance in the local Codex workflow.
