/**
 * Doubao (ByteDance) Streaming ASR provider.
 *
 * Implements SpeechInputProvider by opening a WebSocket to the backend /ws/asr
 * endpoint, capturing microphone audio as PCM 16-bit 16kHz via Web Audio API,
 * and relaying real-time transcription results (partial and final) from Doubao.
 *
 * Fallback: if the WebSocket connection fails the caller receives an onError
 * callback with code "network", which lets the parent component fall back to
 * browser SpeechRecognition or text input.
 */

import type {
  SpeechInputCallbacks,
  SpeechInputOptions,
  SpeechInputProvider,
  SpeechRecognitionResult,
} from "./types";

const PROVIDER_ID = "doubao-asr";
const PCM_SAMPLE_RATE = 16000;
const SCRIPT_PROCESSOR_BUFFER_SIZE = 4096;

function getBackendWsUrl(path: string): string {
  // Derive WebSocket URL from the Vite API base URL env var.
  // VITE_API_BASE_URL is e.g. "http://127.0.0.1:8000"; replace scheme with ws/wss.
  const rawBase = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";
  const base = rawBase.trim().replace(/\/$/, "") || "http://127.0.0.1:8000";
  const wsBase = base.replace(/^https:\/\//, "wss://").replace(/^http:\/\//, "ws://");
  return `${wsBase}${path}`;
}

function float32ToInt16(samples: Float32Array): ArrayBuffer {
  const buffer = new ArrayBuffer(samples.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < samples.length; i++) {
    const clamped = Math.max(-1, Math.min(1, samples[i]!));
    view.setInt16(i * 2, Math.round(clamped * 32767), true);
  }
  return buffer;
}

export const doubaoSpeechProvider: SpeechInputProvider = {
  id: PROVIDER_ID,

  getSupport: () =>
    typeof WebSocket !== "undefined" &&
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices !== "undefined" &&
    typeof AudioContext !== "undefined",

  createSession: (options: SpeechInputOptions, callbacks: SpeechInputCallbacks) => {
    let ws: WebSocket | null = null;
    let audioContext: AudioContext | null = null;
    // ScriptProcessorNode is deprecated but widely supported in all demo browsers.
    // eslint-disable-next-line deprecation/deprecation
    let processor: ScriptProcessorNode | null = null;
    let sourceNode: MediaStreamAudioSourceNode | null = null;
    let stream: MediaStream | null = null;
    let disposed = false;
    let endSent = false;
    let finalAccum = "";
    let ended = false;

    const notifyEnd = () => {
      if (ended) return;
      ended = true;
      callbacks.onEnd?.();
    };

    const cleanupAudio = () => {
      try {
        processor?.disconnect();
        sourceNode?.disconnect();
        audioContext?.close();
      } catch {
        // ignore
      }
      processor = null;
      sourceNode = null;
      audioContext = null;
      stream?.getTracks().forEach((t) => t.stop());
      stream = null;
    };

    const sendEnd = () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        try {
          if (!endSent) {
            ws.send(JSON.stringify({ type: "end" }));
            endSent = true;
          }
        } catch {
          // ignore
        }
      }
    };

    const cleanupWs = () => {
      sendEnd();
      ws?.close();
      ws = null;
    };

    const cleanup = () => {
      cleanupAudio();
      cleanupWs();
    };

    const setupAudioCapture = (mediaStream: MediaStream) => {
      stream = mediaStream;
      audioContext = new AudioContext({ sampleRate: PCM_SAMPLE_RATE });
      sourceNode = audioContext.createMediaStreamSource(mediaStream);
      // eslint-disable-next-line deprecation/deprecation
      processor = audioContext.createScriptProcessor(SCRIPT_PROCESSOR_BUFFER_SIZE, 1, 1);

      processor.onaudioprocess = (event: AudioProcessingEvent) => {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        const float32 = event.inputBuffer.getChannelData(0);
        const pcmBuffer = float32ToInt16(float32);
        ws.send(pcmBuffer);
      };

      sourceNode.connect(processor);
      // Connect to destination to keep processor alive (required by Web Audio spec)
      processor.connect(audioContext.destination);
    };

    const initSession = async () => {
      // Step 1: request microphone access
      let mediaStream: MediaStream;
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            sampleRate: PCM_SAMPLE_RATE,
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
          },
        });
      } catch (err) {
        if (disposed) return;
        const isDenied =
          err instanceof DOMException &&
          (err.name === "NotAllowedError" || err.name === "PermissionDeniedError");
        callbacks.onError?.({
          code: isDenied ? "permission-denied" : "network",
          message: isDenied
            ? "麦克风权限被拒绝，请使用文本输入。"
            : "无法访问麦克风，请使用文本输入。",
          providerId: PROVIDER_ID,
          cause: err,
        });
        return;
      }

      if (disposed) {
        mediaStream.getTracks().forEach((t) => t.stop());
        return;
      }

      // Step 2: open WebSocket to backend ASR relay
      const wsUrl = getBackendWsUrl("/ws/asr");
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        if (disposed) {
          cleanupWs();
          return;
        }
        // Send config then start audio capture immediately so the mic button
        // enters recording state without waiting for the Doubao "ready" signal.
        ws!.send(JSON.stringify({ type: "config", lang: options.lang ?? "zh-CN" }));
        setupAudioCapture(mediaStream);
        callbacks.onStart?.();
      };

      ws.onmessage = (event: MessageEvent<string>) => {
        if (disposed) return;
        let data: { type: string; transcript?: string; code?: string; message?: string };
        try {
          data = JSON.parse(event.data) as typeof data;
        } catch {
          return;
        }

        if (data.type === "ready") {
          // Backend confirmed Doubao connection — already in listening state.
          return;
        }

        if (data.type === "error") {
          cleanupAudio();
          cleanupWs();
          callbacks.onError?.({
            code: "network",
            message: data.message ?? "语音识别失败，请使用文本输入。",
            providerId: PROVIDER_ID,
          });
          return;
        }

        const text = (data.transcript ?? "").trim();
        if (!text) return;

        const isFinal = data.type === "final";

        if (isFinal) {
          finalAccum = mergeTranscript(finalAccum, text);
        }

        const displayTranscript = isFinal ? finalAccum : mergeTranscript(finalAccum, text);

        const result: SpeechRecognitionResult = {
          transcript: displayTranscript,
          finalTranscript: isFinal ? text : finalAccum,
          interimTranscript: isFinal ? "" : text,
          isFinal,
          language: options.lang ?? "zh-CN",
          providerId: PROVIDER_ID,
        };

        callbacks.onResult?.(result);
      };

      ws.onerror = () => {
        if (disposed) return;
        cleanupAudio();
        callbacks.onError?.({
          code: "network",
          message: "语音识别服务暂时不可用，请使用文本输入或切换到浏览器语音识别。",
          providerId: PROVIDER_ID,
        });
      };

      ws.onclose = () => {
        cleanupAudio();
        notifyEnd();
      };
    };

    return {
      start: () => {
        disposed = false;
        ended = false;
        endSent = false;
        finalAccum = "";
        void initSession();
      },
      stop: () => {
        disposed = true;
        cleanupAudio();
        cleanupWs();
        notifyEnd();
      },
      abort: () => {
        disposed = true;
        cleanup();
      },
      dispose: () => {
        disposed = true;
        cleanup();
      },
    };
  },
};

function mergeTranscript(current: string, incoming: string): string {
  const left = current.trim();
  const right = incoming.trim();
  if (!left) return right;
  if (!right) return left;
  if (left === right || left.endsWith(right)) return left;
  if (right.startsWith(left)) return right;

  const maxOverlap = Math.min(left.length, right.length);
  for (let size = maxOverlap; size > 0; size -= 1) {
    if (left.slice(-size) === right.slice(0, size)) {
      return `${left}${right.slice(size)}`.trim();
    }
  }
  return `${left} ${right}`.trim();
}
