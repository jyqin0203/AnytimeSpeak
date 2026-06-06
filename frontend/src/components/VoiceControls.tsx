import type { useSpeechInput, useSpeechOutput } from "../speech";

type SpeechInputControls = ReturnType<typeof useSpeechInput>;
type SpeechOutputControls = ReturnType<typeof useSpeechOutput>;

type VoiceControlsProps = {
  input: SpeechInputControls;
  output: SpeechOutputControls;
  sampleText: string;
};

export function VoiceControls({ input, output, sampleText }: VoiceControlsProps) {
  const inputStatus = input.isSupported ? (input.isListening ? "正在聆听英文回答" : "可使用麦克风输入") : "当前浏览器不支持语音识别";
  const outputStatus = output.isSupported ? (output.isSpeaking ? "AI 回复朗读中" : "可朗读 AI 回复") : "当前浏览器不支持语音朗读";

  return (
    <section className="voice-controls" aria-label="语音练习控制">
      <div className="voice-status-grid">
        <div>
          <span>语音输入</span>
          <strong className={input.isListening ? "recording" : ""}>{inputStatus}</strong>
        </div>
        <div>
          <span>语音朗读</span>
          <strong>{outputStatus}</strong>
        </div>
      </div>

      <div className="voice-button-row">
        <button className="secondary-button" type="button" onClick={input.startListening} disabled={!input.isSupported || input.isListening}>
          {input.isSupported ? (input.isListening ? "正在聆听" : "开始说话") : "语音不可用"}
        </button>
        <button className="secondary-button" type="button" onClick={input.stopListening} disabled={!input.isListening}>
          停止录音
        </button>
        <button className="secondary-button" type="button" onClick={input.resetTranscript} disabled={!input.transcript}>
          清空识别
        </button>
      </div>

      <div className="voice-transcript" aria-live="polite">
        <span>识别结果</span>
        <p>{input.transcript || "点击“开始说话”后，识别出的英文会显示在这里，并自动填入输入框。你仍然可以手动修改后再发送。"}</p>
      </div>

      <div className="voice-button-row">
        <button className="secondary-button" type="button" onClick={() => output.speak(sampleText)} disabled={!output.isSupported || output.isSpeaking}>
          朗读示例文本
        </button>
        <button className="secondary-button" type="button" onClick={output.stopSpeaking} disabled={!output.isSpeaking}>
          停止朗读
        </button>
      </div>

      {input.error && <p className="voice-warning">{input.error.message}</p>}
      {output.error && <p className="voice-warning">{output.error.message}</p>}
    </section>
  );
}
