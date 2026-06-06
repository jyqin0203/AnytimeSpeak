import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { VoiceRecorderState, VoiceRecording } from "./types";

function getSupportedMimeType() {
  if (typeof MediaRecorder === "undefined") return "";
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  return candidates.find((candidate) => MediaRecorder.isTypeSupported(candidate)) ?? "";
}

export function useVoiceRecorder() {
  const [state, setState] = useState<VoiceRecorderState>(() => ({
    isRecording: false,
    isSupported: typeof navigator !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia) && typeof MediaRecorder !== "undefined",
    error: null,
  }));
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const startedAtRef = useRef<number | null>(null);

  const stopTracks = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  const startRecording = useCallback(async () => {
    if (!state.isSupported) {
      setState((current) => ({
        ...current,
        error: {
          code: "not-supported",
          message: "当前浏览器不支持录音回放，将只能朗读识别文本。",
          providerId: "browser-media-recorder",
        },
      }));
      return false;
    }

    try {
      chunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = getSupportedMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);

      streamRef.current = stream;
      recorderRef.current = recorder;
      startedAtRef.current = Date.now();
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };
      recorder.onerror = (event) => {
        setState((current) => ({
          ...current,
          isRecording: false,
          error: {
            code: "unknown",
            message: "录音失败，将只能朗读识别文本。",
            providerId: "browser-media-recorder",
            cause: event,
          },
        }));
        stopTracks();
      };

      recorder.start();
      setState((current) => ({ ...current, isRecording: true, error: null }));
      return true;
    } catch (cause) {
      setState((current) => ({
        ...current,
        isRecording: false,
        error: {
          code: "permission-denied",
          message: "无法访问麦克风录音，将只能朗读识别文本。",
          providerId: "browser-media-recorder",
          cause,
        },
      }));
      stopTracks();
      return false;
    }
  }, [state.isSupported, stopTracks]);

  const stopRecording = useCallback(async (): Promise<VoiceRecording | null> => {
    const recorder = recorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      stopTracks();
      setState((current) => ({ ...current, isRecording: false }));
      return null;
    }

    return new Promise((resolve) => {
      recorder.onstop = () => {
        const mimeType = recorder.mimeType || getSupportedMimeType() || "audio/webm";
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const durationMs = startedAtRef.current ? Date.now() - startedAtRef.current : undefined;

        recorderRef.current = null;
        chunksRef.current = [];
        startedAtRef.current = null;
        stopTracks();
        setState((current) => ({ ...current, isRecording: false }));
        resolve(blob.size > 0 ? { blob, url: URL.createObjectURL(blob), mimeType, durationMs } : null);
      };
      recorder.stop();
    });
  }, [stopTracks]);

  useEffect(
    () => () => {
      if (recorderRef.current?.state === "recording") {
        recorderRef.current.stop();
      }
      stopTracks();
    },
    [stopTracks],
  );

  return useMemo(() => ({ ...state, startRecording, stopRecording }), [startRecording, state, stopRecording]);
}
