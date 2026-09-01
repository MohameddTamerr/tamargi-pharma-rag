"use client";

import { useState, useRef, useEffect } from "react";
import { Mic, Square, Loader2, Check, X, Globe, AlertCircle } from "lucide-react";
import VoiceVisualizer from "./VoiceVisualizer";
import { transcribeAudio } from "@/lib/api";

interface VoiceButtonProps {
  onTranscribed: (transcript: string, detectedLanguage?: string) => void;
  isSpeaking: boolean;
  onStopSpeaking: () => void;
}

type LanguageMode = "auto" | "ar" | "en";

export default function VoiceButton({ onTranscribed, isSpeaking, onStopSpeaking }: VoiceButtonProps) {
  const [isListening, setIsListening] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [detectedLang, setDetectedLang] = useState<string | null>(null);
  const [langMode, setLangMode] = useState<LanguageMode>("auto");
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [audioLevel, setAudioLevel] = useState(0.5);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Clean up on unmount
  useEffect(() => {
    return () => {
      stopMediaTracks();
      if (timerRef.current) clearInterval(timerRef.current);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    };
  }, []);

  const stopMediaTracks = () => {
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
      audioStreamRef.current = null;
    }
  };

  const startListening = async () => {
    if (isSpeaking) {
      onStopSpeaking();
    }
    setErrorMessage(null);
    setDetectedLang(null);
    setRecordingSeconds(0);

    try {
      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error("متصفحك لا يدعم تسجيل الصوت المباشر.");
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      audioStreamRef.current = stream;

      // Setup Web Audio API Analyzer for sound levels
      try {
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        if (AudioContextClass) {
          const ctx = new AudioContextClass();
          const analyser = ctx.createAnalyser();
          analyser.fftSize = 64;
          const source = ctx.createMediaStreamSource(stream);
          source.connect(analyser);

          audioContextRef.current = ctx;
          analyserRef.current = analyser;

          const updateVolume = () => {
            if (!analyserRef.current) return;
            const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
            analyserRef.current.getByteFrequencyData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
              sum += dataArray[i];
            }
            const avg = sum / dataArray.length;
            setAudioLevel(Math.min(1, Math.max(0.1, avg / 128)));
            animFrameRef.current = requestAnimationFrame(updateVolume);
          };
          updateVolume();
        }
      } catch (audioCtxErr) {
        console.warn("AudioContext analyzer not available:", audioCtxErr);
      }

      // Pick best supported mimeType
      const mimeTypes = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/mp4",
        "audio/wav",
      ];
      let selectedMime = "";
      for (const m of mimeTypes) {
        if (MediaRecorder.isTypeSupported(m)) {
          selectedMime = m;
          break;
        }
      }

      const mediaRecorder = new MediaRecorder(stream, selectedMime ? { mimeType: selectedMime } : undefined);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsListening(false);
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
        if (timerRef.current) clearInterval(timerRef.current);

        const recordedBlob = new Blob(chunksRef.current, {
          type: selectedMime || "audio/webm",
        });

        stopMediaTracks();

        if (recordedBlob.size < 500) {
          setErrorMessage("التسجيل قصير جداً، يرجى المحاولة مرة أخرى.");
          setTimeout(() => setErrorMessage(null), 3000);
          return;
        }

        // Process audio with Backend Gemini Multimodal STT
        await processAudioTranscription(recordedBlob);
      };

      mediaRecorder.start(250); // Collect slice every 250ms
      setIsListening(true);

      // Start elapsed timer
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => {
          if (prev >= 60) {
            stopListening();
            return 60;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err: any) {
      console.warn("Microphone access error:", err);
      // Fallback to Web Speech API if getUserMedia fails
      tryWebSpeechFallback();
    }
  };

  const stopListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
    } else {
      setIsListening(false);
      stopMediaTracks();
    }
  };

  const cancelListening = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.ondataavailable = null;
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }
    stopMediaTracks();
    if (timerRef.current) clearInterval(timerRef.current);
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    setIsListening(false);
    setIsTranscribing(false);
    setRecordingSeconds(0);
  };

  const processAudioTranscription = async (blob: Blob) => {
    setIsTranscribing(true);
    try {
      const result = await transcribeAudio(blob);

      if (result && result.success && result.transcript) {
        setDetectedLang(result.language_label || result.language);
        onTranscribed(result.transcript, result.language);
      } else {
        // Fallback: If backend STT returned empty or offline, try Web Speech API
        console.warn("Backend STT returned empty, trying browser Web Speech fallback...");
        setErrorMessage("لم نتمكن من التقاط الصوت بوضوح، يرجى إعادة المحاولة.");
        setTimeout(() => setErrorMessage(null), 3500);
      }
    } catch (err: any) {
      console.error("Transcription error:", err);
      setErrorMessage("حدث خطأ أثناء تفريغ الصوت.");
      setTimeout(() => setErrorMessage(null), 3500);
    } finally {
      setIsTranscribing(false);
    }
  };

  const tryWebSpeechFallback = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setErrorMessage("تعذر الوصول إلى الميكروفون أو خدمة التعرف على الصوت.");
      setTimeout(() => setErrorMessage(null), 3500);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = langMode === "en" ? "en-US" : "ar-EG";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          onTranscribed(transcript);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn("Web Speech error:", event.error);
        setIsListening(false);
        setErrorMessage("تعذر التعرف على الصوت.");
        setTimeout(() => setErrorMessage(null), 3000);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch (err) {
      setIsListening(false);
      setErrorMessage("تعذر بدء التعرف على الصوت.");
      setTimeout(() => setErrorMessage(null), 3000);
    }
  };

  const formatTimer = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const toggleLanguageMode = () => {
    const nextMode: Record<LanguageMode, LanguageMode> = {
      auto: "ar",
      ar: "en",
      en: "auto",
    };
    setLangMode(nextMode[langMode]);
  };

  return (
    <div className="relative flex items-center gap-1.5">
      
      {/* Active Recording Floating Controls Bar */}
      {isListening && (
        <div className="absolute right-0 bottom-12 z-30 flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/95 border border-rose-500/50 shadow-xl backdrop-blur-md text-white animate-fade-in text-xs">
          
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
            <span className="font-mono text-rose-300 font-bold">{formatTimer(recordingSeconds)}</span>
          </div>

          <VoiceVisualizer isListening={isListening} audioLevel={audioLevel} />

          {/* Cancel Button */}
          <button
            type="button"
            onClick={cancelListening}
            className="p-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
            title="إلغاء التسجيل"
          >
            <X className="w-3.5 h-3.5" />
          </button>

          {/* Confirm / Stop & Send Button */}
          <button
            type="button"
            onClick={stopListening}
            className="p-1 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white transition-colors"
            title="إنهاء والتفريغ"
          >
            <Check className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Transcribing Status Floating Pill */}
      {isTranscribing && (
        <div className="absolute right-0 bottom-12 z-30 flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-900/95 border border-blue-500/40 shadow-xl backdrop-blur-md text-blue-300 text-xs animate-fade-in">
          <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
          <span>جاري فهم الصوت وتحديد اللغة...</span>
        </div>
      )}

      {/* Error Message Toast */}
      {errorMessage && (
        <div className="absolute right-0 bottom-12 z-30 flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-rose-950/95 border border-rose-600 text-rose-200 text-xs shadow-xl backdrop-blur-md animate-fade-in">
          <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Smart Language Toggle Button */}
      <button
        type="button"
        onClick={toggleLanguageMode}
        disabled={isListening || isTranscribing}
        className="p-1.5 rounded-full text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-[10px] flex items-center gap-1 font-semibold"
        title={
          langMode === "auto"
            ? "التعرف الذكي التلقائي (عربي / English)"
            : langMode === "ar"
            ? "تثبيت اللغة: العربية"
            : "تثبيت اللغة: English"
        }
      >
        <Globe className="w-3.5 h-3.5 text-slate-400" />
        <span className="uppercase text-[9px]">
          {langMode === "auto" ? "Auto" : langMode}
        </span>
      </button>

      {/* Main Microphone Button */}
      <button
        type="button"
        onClick={isListening ? stopListening : startListening}
        disabled={isTranscribing}
        className={`w-9 h-9 rounded-full flex items-center justify-center transition-all ${
          isListening
            ? "bg-rose-500 text-white animate-pulse shadow-md shadow-rose-500/40"
            : isTranscribing
            ? "bg-amber-500 text-slate-950 cursor-wait shadow-md"
            : "bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-600/25"
        }`}
        title={
          isListening
            ? "إيقاف التسجيل وإنهاء السؤال"
            : isTranscribing
            ? "جاري معالجة الصوت..."
            : "تسجيل صوتي مع التعرف التلقائي على اللغة (عربي / English)"
        }
      >
        {isListening ? (
          <Square className="w-3.5 h-3.5 fill-current" />
        ) : isTranscribing ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Mic className="w-4 h-4" />
        )}
      </button>

    </div>
  );
}
