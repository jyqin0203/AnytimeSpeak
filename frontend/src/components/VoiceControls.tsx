import type { useSpeechInput, useSpeechOutput } from "../speech";

type SpeechInputControls = ReturnType<typeof useSpeechInput>;
type SpeechOutputControls = ReturnType<typeof useSpeechOutput>;

type VoiceControlsProps = {
  input: SpeechInputControls;
  output: SpeechOutputControls;
  sampleText: string;
  language: string;
  onLanguageChange: (language: string) => void;
  onToggleListening: () => void;
  isSending: boolean;
  recorderError: string | null;
};

export function VoiceControls({ input, output, sampleText, language, onLanguageChange, onToggleListening, isSending, recorderError }: VoiceControlsProps) {
  const isActive = input.isListening || input.isRestarting;
  const inputStatus = input.isSupported
    ? isActive
      ? "正在听你说话，再点一次会停止并发送"
      : "点击麦克风开始说话"
    : "当前浏览器不支持语音识别";
  const outputStatus = output.isSupported ? (output.isSpeaking ? "对方回复正在自动播放" : "对方回复会自动播放") : "当前浏览器不支持语音朗读";

  return (
    <section className="voice-controls" aria-label="语音练习控制">
      <div className="voice-primary">
        <button
          className={`microphone-button ${isActive ? "recording" : ""}`}
          type="button"
          onClick={onToggleListening}
          disabled={!input.isSupported || isSending}
          aria-pressed={isActive}
          aria-label={isActive ? "停止录音并发送" : "开始麦克风输入"}
        >
          <span className="microphone-icon" aria-hidden="true">
            <span />
          </span>
        </button>
        <div>
          <span>麦克风优先</span>
          <strong className={isActive ? "recording" : ""}>{inputStatus}</strong>
          <p>{isSending ? "正在发送到后端 coaching API..." : outputStatus}</p>
        </div>
      </div>

      <div className="voice-mode-row" aria-label="识别语言">
        <button className={language === "zh-CN" ? "active" : ""} type="button" onClick={() => onLanguageChange("zh-CN")} disabled={isActive}>
          中英混合
        </button>
        <button className={language === "en-US" ? "active" : ""} type="button" onClick={() => onLanguageChange("en-US")} disabled={isActive}>
          English
        </button>
      </div>

      <div className="voice-transcript" aria-live="polite">
        <span>识别结果</span>
        <p>{input.transcript || "点击麦克风后直接说中文、英文或中英夹杂内容；再次点击会停止录音并自动发送。"}</p>
      </div>

      <div className="voice-button-row">
        <button className="secondary-button" type="button" onClick={() => output.speak(sampleText)} disabled={!output.isSupported || output.isSpeaking}>
          重播对方回复
        </button>
        <button className="secondary-button" type="button" onClick={output.stopSpeaking} disabled={!output.isSpeaking}>
          停止播放
        </button>
      </div>

      {input.error && <p className="voice-warning">{input.error.message}</p>}
      {recorderError && <p className="voice-warning">{recorderError}</p>}
      {output.error && <p className="voice-warning">{output.error.message}</p>}
    </section>
  );
}
