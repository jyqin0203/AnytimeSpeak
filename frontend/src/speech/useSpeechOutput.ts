import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { browserSpeechOutputProvider } from "./browserSpeechProvider";
import type { SpeechOutputHandle, SpeechOutputOptions, SpeechOutputProvider, SpeechOutputState } from "./types";

type UseSpeechOutputOptions = SpeechOutputOptions & {
  provider?: SpeechOutputProvider;
};

export function useSpeechOutput({
  provider = browserSpeechOutputProvider,
  lang = "en-US",
  rate = 0.95,
  pitch = 1,
  volume = 1,
}: UseSpeechOutputOptions = {}) {
  const [state, setState] = useState<SpeechOutputState>(() => ({
    isSpeaking: false,
    isSupported: provider.getSupport(),
    error: null,
  }));
  const handleRef = useRef<SpeechOutputHandle | null>(null);

  const stopSpeaking = useCallback(() => {
    handleRef.current?.stop();
    provider.stop();
    handleRef.current = null;
    setState((current) => ({ ...current, isSpeaking: false }));
  }, [provider]);

  const speak = useCallback(
    (text: string, overrideOptions: SpeechOutputOptions = {}) => {
      const cleanText = text.trim();
      if (!cleanText) return;

      if (!provider.getSupport()) {
        setState({
          isSpeaking: false,
          isSupported: false,
          error: {
            code: "not-supported",
            message: "当前浏览器不支持语音朗读。",
            providerId: provider.id,
          },
        });
        return;
      }

      stopSpeaking();
      setState({ isSpeaking: false, isSupported: true, error: null });
      handleRef.current = provider.speak(
        cleanText,
        { lang, rate, pitch, volume, ...overrideOptions },
        {
          onStart: () => setState((current) => ({ ...current, isSpeaking: true, error: null })),
          onEnd: () => setState((current) => ({ ...current, isSpeaking: false })),
          onError: (error) => setState((current) => ({ ...current, isSpeaking: false, error })),
        },
      );
    },
    [lang, pitch, provider, rate, stopSpeaking, volume],
  );

  useEffect(() => stopSpeaking, [stopSpeaking]);

  return useMemo(
    () => ({
      ...state,
      speak,
      stopSpeaking,
    }),
    [speak, state, stopSpeaking],
  );
}
