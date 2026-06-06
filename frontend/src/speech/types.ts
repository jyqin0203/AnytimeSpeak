export type SpeechProviderErrorCode =
  | "not-supported"
  | "permission-denied"
  | "network"
  | "aborted"
  | "synthesis-failed"
  | "unknown";

export type SpeechProviderError = {
  code: SpeechProviderErrorCode;
  message: string;
  providerId?: string;
  cause?: unknown;
};

export type SpeechRecognitionResult = {
  transcript: string;
  finalTranscript: string;
  interimTranscript: string;
  confidence?: number;
  isFinal: boolean;
  language: string;
  providerId: string;
  raw?: unknown;
};

export type SpeechInputState = {
  transcript: string;
  finalTranscript: string;
  interimTranscript: string;
  isListening: boolean;
  isSupported: boolean;
  error: SpeechProviderError | null;
};

export type SpeechInputOptions = {
  lang?: string;
  interimResults?: boolean;
  continuous?: boolean;
};

export type SpeechInputCallbacks = {
  onResult?: (result: SpeechRecognitionResult) => void;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: SpeechProviderError) => void;
};

export type SpeechInputSession = {
  start: () => void;
  stop: () => void;
  abort?: () => void;
  dispose: () => void;
};

export type SpeechInputProvider = {
  id: string;
  getSupport: () => boolean;
  // Cloud ASR providers can implement this same session contract without changing practice page code.
  createSession: (options: SpeechInputOptions, callbacks: SpeechInputCallbacks) => SpeechInputSession;
};

export type SpeechOutputState = {
  isSpeaking: boolean;
  isSupported: boolean;
  error: SpeechProviderError | null;
};

export type SpeechOutputOptions = {
  lang?: string;
  rate?: number;
  pitch?: number;
  volume?: number;
};

export type SpeechOutputCallbacks = {
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: SpeechProviderError) => void;
};

export type SpeechOutputHandle = {
  stop: () => void;
};

export type SpeechOutputProvider = {
  id: string;
  getSupport: () => boolean;
  // Cloud TTS providers can replace browser synthesis behind this interface.
  speak: (text: string, options: SpeechOutputOptions, callbacks: SpeechOutputCallbacks) => SpeechOutputHandle;
  stop: () => void;
};

export type PronunciationAssessmentResult = {
  overallScore: number;
  accuracyScore?: number;
  fluencyScore?: number;
  completenessScore?: number;
  words?: Array<{
    text: string;
    score?: number;
    errorType?: string;
  }>;
};

export type PronunciationAssessmentProvider = {
  id: string;
  getSupport: () => boolean;
  // Reserved for later pronunciation assessment services that score recorded speech against reference text.
  assess: (audio: Blob, referenceText: string, options?: { lang?: string }) => Promise<PronunciationAssessmentResult>;
};
