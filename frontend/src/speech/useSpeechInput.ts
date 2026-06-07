import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { browserSpeechInputProvider } from "./browserSpeechProvider";
import type { SpeechInputProvider, SpeechInputSession, SpeechInputState, SpeechRecognitionResult } from "./types";

type UseSpeechInputOptions = {
  provider?: SpeechInputProvider;
  lang?: string;
  interimResults?: boolean;
  continuous?: boolean;
  onTranscriptChange?: (transcript: string, result: SpeechRecognitionResult) => void;
};

export function useSpeechInput({
  provider = browserSpeechInputProvider,
  lang = "en-US",
  interimResults = true,
  continuous = false,
  onTranscriptChange,
}: UseSpeechInputOptions = {}) {
  const [state, setState] = useState<SpeechInputState>(() => ({
    transcript: "",
    finalTranscript: "",
    interimTranscript: "",
    isListening: false,
    isRestarting: false,
    isSupported: provider.getSupport(),
    error: null,
  }));
  const sessionRef = useRef<SpeechInputSession | null>(null);
  const finalTranscriptRef = useRef("");
  const shouldListenRef = useRef(false);
  const onTranscriptChangeRef = useRef(onTranscriptChange);

  useEffect(() => {
    onTranscriptChangeRef.current = onTranscriptChange;
  }, [onTranscriptChange]);

  const disposeSession = useCallback(() => {
    sessionRef.current?.dispose();
    sessionRef.current = null;
  }, []);

  useEffect(() => {
    shouldListenRef.current = false;
    disposeSession();
    finalTranscriptRef.current = "";
    setState((current) => ({
      ...current,
      transcript: "",
      finalTranscript: "",
      interimTranscript: "",
      isListening: false,
      isRestarting: false,
      isSupported: provider.getSupport(),
      error: null,
    }));
  }, [disposeSession, provider]);

  const resetTranscript = useCallback(() => {
    finalTranscriptRef.current = "";
    setState((current) => ({
      ...current,
      transcript: "",
      finalTranscript: "",
      interimTranscript: "",
      error: null,
    }));
  }, []);

  const startListening = useCallback(() => {
    if (!provider.getSupport()) {
      setState((current) => ({
        ...current,
        isSupported: false,
        isListening: false,
        isRestarting: false,
        error: {
          code: "not-supported",
          message: "当前浏览器不支持语音识别，请继续使用文本输入。",
          providerId: provider.id,
        },
      }));
      return;
    }

    shouldListenRef.current = true;
    disposeSession();
    setState((current) => ({ ...current, isSupported: true, error: null }));

    const session = provider.createSession(
      { lang, interimResults, continuous },
      {
        onStart: () => setState((current) => ({ ...current, isListening: true, isRestarting: false, error: null })),
        onEnd: () => {
          setState((current) => ({ ...current, isListening: false, isRestarting: shouldListenRef.current }));
          if (shouldListenRef.current) {
            window.setTimeout(() => {
              if (shouldListenRef.current) {
                try {
                  session.start();
                } catch {
                  shouldListenRef.current = false;
                  setState((current) => ({ ...current, isRestarting: false }));
                }
              }
            }, 250);
          }
        },
        onError: (error) => {
          shouldListenRef.current = false;
          setState((current) => ({ ...current, isListening: false, isRestarting: false, error }));
        },
        onResult: (result) => {
          if (result.providerId === "doubao-asr") {
            const nextTranscript = result.transcript.trim();
            const nextFinalTranscript = result.isFinal ? nextTranscript : result.finalTranscript.trim();
            finalTranscriptRef.current = nextFinalTranscript;
            setState((current) => ({
              ...current,
              transcript: nextTranscript,
              finalTranscript: nextFinalTranscript,
              interimTranscript: result.interimTranscript,
              error: null,
            }));
            onTranscriptChangeRef.current?.(nextTranscript, {
              ...result,
              transcript: nextTranscript,
              finalTranscript: nextFinalTranscript,
            });
            return;
          }

          const nextFinalTranscript = result.finalTranscript
            ? `${finalTranscriptRef.current} ${result.finalTranscript}`.trim()
            : finalTranscriptRef.current;
          const nextTranscript = `${nextFinalTranscript} ${result.interimTranscript}`.trim();

          if (result.finalTranscript) {
            finalTranscriptRef.current = nextFinalTranscript;
          }

          setState((current) => ({
            ...current,
            transcript: nextTranscript,
            finalTranscript: nextFinalTranscript,
            interimTranscript: result.interimTranscript,
            error: null,
          }));
          onTranscriptChangeRef.current?.(nextTranscript, {
            ...result,
            transcript: nextTranscript,
            finalTranscript: nextFinalTranscript,
          });
        },
      },
    );

    sessionRef.current = session;

    try {
      session.start();
    } catch (cause) {
      shouldListenRef.current = false;
      setState((current) => ({
        ...current,
        isListening: false,
        isRestarting: false,
        error: {
          code: "unknown",
          message: "语音识别启动失败，请继续使用文本输入。",
          providerId: provider.id,
          cause,
        },
      }));
    }
  }, [continuous, disposeSession, interimResults, lang, provider]);

  const stopListening = useCallback(() => {
    try {
      shouldListenRef.current = false;
      sessionRef.current?.stop();
      sessionRef.current = null;
      setState((current) => ({ ...current, isListening: false, isRestarting: false }));
    } catch (cause) {
      setState((current) => ({
        ...current,
        isListening: false,
        isRestarting: false,
        error: {
          code: "unknown",
          message: "语音识别停止失败。",
          providerId: provider.id,
          cause,
        },
      }));
    }
  }, [provider.id]);

  useEffect(
    () => () => {
      shouldListenRef.current = false;
      disposeSession();
    },
    [disposeSession],
  );

  return useMemo(
    () => ({
      ...state,
      startListening,
      stopListening,
      resetTranscript,
    }),
    [resetTranscript, startListening, state, stopListening],
  );
}
