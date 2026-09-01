"use client";

import { useState } from "react";
import { ArrowRight, Paperclip, Info } from "lucide-react";
import VoiceButton from "../voice/VoiceButton";

interface ChatInputProps {
  onSendMessage: (text: string, inputType?: "text" | "voice") => void;
  isLoading: boolean;
  isSpeaking: boolean;
  onStopSpeaking: () => void;
}

export default function ChatInput({ onSendMessage, isLoading, isSpeaking, onStopSpeaking }: ChatInputProps) {
  const [text, setText] = useState("");

  const suggestedChips = [
    "ازاي استخدم بخاخ الربو؟",
    "طريقة استخدام قلم الانسولين",
    "ما الفرق بين الباراستامول والإيبوبروفين؟",
    "هل هذا الدواء آمن للحامل؟",
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim() || isLoading) return;
    onSendMessage(text.trim(), "text");
    setText("");
  };

  const handleVoiceTranscribed = (transcript: string) => {
    if (transcript && !isLoading) {
      onSendMessage(transcript, "voice");
    }
  };

  return (
    <div className="space-y-2.5 w-full max-w-3xl mx-auto">
      
      {/* Suggested Question Chips */}
      <div className="flex items-center justify-center gap-2 overflow-x-auto pb-0.5 scrollbar-none text-xs">
        {suggestedChips.map((chip, idx) => (
          <button
            key={idx}
            onClick={() => onSendMessage(chip, "text")}
            disabled={isLoading}
            className="px-4 py-1.5 rounded-full bg-white dark:bg-slate-900 hover:bg-blue-50 dark:hover:bg-slate-800 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-slate-800 font-semibold transition-colors shadow-xs shrink-0 text-xs"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Main Input Form Bar */}
      <form
        onSubmit={handleSubmit}
        className="flex items-center gap-2 p-1.5 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-md focus-within:border-blue-500 transition-all"
      >
        <VoiceButton
          onTranscribed={handleVoiceTranscribed}
          isSpeaking={isSpeaking}
          onStopSpeaking={onStopSpeaking}
        />

        <button
          type="button"
          className="p-2 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          title="إرفاق ملف"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="اكتب سؤالك هنا أو تحدث بالصوت..."
          disabled={isLoading}
          className="flex-1 bg-transparent border-none outline-none text-slate-800 dark:text-slate-100 placeholder-slate-400 text-xs px-2"
        />

        <button
          type="submit"
          disabled={!text.trim() || isLoading}
          className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${
            text.trim() && !isLoading
              ? "bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/30"
              : "bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
          }`}
        >
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {/* Medical Disclaimer Caption */}
      <div className="flex items-center justify-center gap-1.5 text-[10px] text-slate-400 font-medium text-center">
        <Info className="w-3 h-3 text-slate-400" />
        <span>تنبيه: المعلومات المقدمة لا تغني عن استشارة الطبيب المختص</span>
      </div>

    </div>
  );
}
