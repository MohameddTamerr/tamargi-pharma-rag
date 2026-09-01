"use client";

import { useState, useEffect, useRef } from "react";
import { Volume2, VolumeX, Square } from "lucide-react";

interface AudioPlayerProps {
  textToSpeak?: string;
  isSpeaking: boolean;
  onStopSpeaking: () => void;
}

export default function AudioPlayer({ textToSpeak, isSpeaking, onStopSpeaking }: AudioPlayerProps) {
  const [isMuted, setIsMuted] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      synthRef.current = window.speechSynthesis;

      const loadVoices = () => {
        if (synthRef.current) {
          const voices = synthRef.current.getVoices();
          setAvailableVoices(voices);
        }
      };

      loadVoices();
      if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = loadVoices;
      }
    }
  }, []);

  useEffect(() => {
    if (!isSpeaking || !textToSpeak || !synthRef.current) return;

    // Stop existing playback
    synthRef.current.cancel();

    if (isMuted) return;

    // Clean text: remove citation badges [E1], markdown bullets, bold markers, and code blocks
    let cleanText = textToSpeak
      .replace(/\[E\d+\]/g, "")
      .replace(/[*_~`#]/g, "")
      .replace(/•/g, "")
      .trim();

    if (!cleanText) return;

    const isArabic = /[\u0600-\u06FF]/.test(cleanText);
    const utterance = new SpeechSynthesisUtterance(cleanText);

    // Pick best available matching voice
    if (availableVoices.length > 0) {
      if (isArabic) {
        const arVoice = availableVoices.find(
          (v) => v.lang.startsWith("ar") || v.name.toLowerCase().includes("arabic") || v.name.toLowerCase().includes("salma") || v.name.toLowerCase().includes("shakir")
        );
        if (arVoice) utterance.voice = arVoice;
        utterance.lang = arVoice ? arVoice.lang : "ar-EG";
      } else {
        const enVoice = availableVoices.find(
          (v) => (v.lang === "en-US" || v.lang.startsWith("en")) && !v.name.includes("Zira")
        );
        if (enVoice) utterance.voice = enVoice;
        utterance.lang = enVoice ? enVoice.lang : "en-US";
      }
    } else {
      utterance.lang = isArabic ? "ar-EG" : "en-US";
    }

    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    utterance.onend = () => {
      onStopSpeaking();
    };

    utterance.onerror = () => {
      onStopSpeaking();
    };

    synthRef.current.speak(utterance);

    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, [isSpeaking, textToSpeak, isMuted, availableVoices, onStopSpeaking]);

  if (!isSpeaking) return null;

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2 rounded-2xl bg-slate-900 border border-emerald-500/40 text-emerald-300 text-xs shadow-lg animate-fade-in my-2">
      <div className="flex items-center gap-2">
        <Volume2 className="w-4 h-4 animate-bounce text-emerald-400" />
        <span className="font-semibold text-slate-100">تمرجي يجيب صوتياً...</span>
      </div>

      <div className="flex items-center gap-1.5">
        <button
          type="button"
          onClick={() => setIsMuted(!isMuted)}
          className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          title={isMuted ? "إلغاء كتم الصوت" : "كتم الصوت"}
        >
          {isMuted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
        </button>

        <button
          type="button"
          onClick={() => {
            if (synthRef.current) synthRef.current.cancel();
            onStopSpeaking();
          }}
          className="p-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 transition-colors"
          title="إيقاف التحدث (Stop)"
        >
          <Square className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
