import type {
  SpeechInputCallbacks,
  SpeechInputOptions,
  SpeechInputProvider,
  SpeechOutputCallbacks,
  SpeechOutputOptions,
  SpeechOutputProvider,
  SpeechProviderError,
  SpeechProviderErrorCode,
  SpeechRecognitionResult,
} from "./types";

type NativeSpeechRecognitionConstructor = new () => NativeSpeechRecognition;

type NativeSpeechRecognitionAlternative = {
  transcript: string;
  confidence: number;
};

type NativeSpeechRecognitionResult = {
  isFinal: boolean;
  length: number;
  item: (index: number) => NativeSpeechRecognitionAlternative;
  [index: number]: NativeSpeechRecognitionAlternative;
};

type NativeSpeechRecognitionEvent = Event & {
  resultIndex: number;
  results: {
    length: number;
    item: (index: number) => NativeSpeechRecognitionResult;
    [index: number]: NativeSpeechRecognitionResult;
  };
};

type NativeSpeechRecognitionErrorEvent = Event & {
  error?: string;
  message?: string;
};

type NativeSpeechRecognition = EventTarget & {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onresult: ((event: NativeSpeechRecognitionEvent) => void) | null;
  onerror: ((event: NativeSpeechRecognitionErrorEvent) => void) | null;
};

type SpeechWindow = Window &
  typeof globalThis & {
    SpeechRecognition?: NativeSpeechRecognitionConstructor;
    webkitSpeechRecognition?: NativeSpeechRecognitionConstructor;
  };

const inputProviderId = "browser-speech-recognition";
const outputProviderId = "browser-speech-synthesis";

function getSpeechWindow(): SpeechWindow | null {
  return typeof window === "undefined" ? null : (window as SpeechWindow);
}

function getRecognitionConstructor(): NativeSpeechRecognitionConstructor | null {
  const speechWindow = getSpeechWindow();
  return speechWindow?.SpeechRecognition ?? speechWindow?.webkitSpeechRecognition ?? null;
}

function mapInputError(event: NativeSpeechRecognitionErrorEvent): SpeechProviderError {
  const codeByNativeError: Record<string, SpeechProviderErrorCode> = {
    "not-allowed": "permission-denied",
    "service-not-allowed": "permission-denied",
    network: "network",
    aborted: "aborted",
  };
  const nativeCode = event.error ?? "unknown";
  return {
    code: codeByNativeError[nativeCode] ?? "unknown",
    message: event.message || `语音识别失败：${nativeCode}`,
    providerId: inputProviderId,
    cause: event,
  };
}

export const browserSpeechInputProvider: SpeechInputProvider = {
  id: inputProviderId,
  getSupport: () => Boolean(getRecognitionConstructor()),
  createSession: (options: SpeechInputOptions, callbacks: SpeechInputCallbacks) => {
    const Recognition = getRecognitionConstructor();

    if (!Recognition) {
      return {
        start: () =>
          callbacks.onError?.({
            code: "not-supported",
            message: "当前浏览器不支持语音识别，请继续使用文本输入。",
            providerId: inputProviderId,
          }),
        stop: () => undefined,
        abort: () => undefined,
        dispose: () => undefined,
      };
    }

    const recognition = new Recognition();
    const lang = options.lang ?? "en-US";

    recognition.lang = lang;
    recognition.continuous = options.continuous ?? false;
    recognition.interimResults = options.interimResults ?? true;

    recognition.onstart = () => callbacks.onStart?.();
    recognition.onend = () => callbacks.onEnd?.();
    recognition.onerror = (event) => callbacks.onError?.(mapInputError(event));
    recognition.onresult = (event) => {
      let finalTranscript = "";
      let interimTranscript = "";
      let confidence: number | undefined;
      let isFinal = false;

      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const nativeResult = event.results[index] ?? event.results.item(index);
        const alternative = nativeResult[0] ?? nativeResult.item(0);
        const text = alternative?.transcript ?? "";

        if (nativeResult.isFinal) {
          finalTranscript += text;
          isFinal = true;
          confidence = alternative?.confidence;
        } else {
          interimTranscript += text;
        }
      }

      const result: SpeechRecognitionResult = {
        transcript: `${finalTranscript}${interimTranscript}`.trim(),
        finalTranscript: finalTranscript.trim(),
        interimTranscript: interimTranscript.trim(),
        confidence,
        isFinal,
        language: lang,
        providerId: inputProviderId,
        raw: event,
      };

      callbacks.onResult?.(result);
    };

    return {
      start: () => recognition.start(),
      stop: () => recognition.stop(),
      abort: () => recognition.abort(),
      dispose: () => {
        recognition.onstart = null;
        recognition.onend = null;
        recognition.onerror = null;
        recognition.onresult = null;
      },
    };
  },
};

export const browserSpeechOutputProvider: SpeechOutputProvider = {
  id: outputProviderId,
  getSupport: () => {
    const speechWindow = getSpeechWindow();
    return Boolean(speechWindow?.speechSynthesis && speechWindow.SpeechSynthesisUtterance);
  },
  speak: (text: string, options: SpeechOutputOptions, callbacks: SpeechOutputCallbacks) => {
    const speechWindow = getSpeechWindow();

    if (!speechWindow?.speechSynthesis || !speechWindow.SpeechSynthesisUtterance) {
      callbacks.onError?.({
        code: "not-supported",
        message: "当前浏览器不支持语音朗读。",
        providerId: outputProviderId,
      });
      return { stop: () => undefined };
    }

    speechWindow.speechSynthesis.cancel();

    const utterance = new speechWindow.SpeechSynthesisUtterance(text);
    utterance.lang = options.lang ?? "en-US";
    utterance.rate = options.rate ?? 0.95;
    utterance.pitch = options.pitch ?? 1;
    utterance.volume = options.volume ?? 1;
    utterance.onstart = () => callbacks.onStart?.();
    utterance.onend = () => callbacks.onEnd?.();
    utterance.onerror = (event) =>
      callbacks.onError?.({
        code: "synthesis-failed",
        message: "语音朗读失败，请继续阅读文本回复。",
        providerId: outputProviderId,
        cause: event,
      });

    speechWindow.speechSynthesis.speak(utterance);

    return {
      stop: () => speechWindow.speechSynthesis.cancel(),
    };
  },
  stop: () => {
    const speechWindow = getSpeechWindow();
    speechWindow?.speechSynthesis?.cancel();
  },
};
