"use client";

import { useState } from "react";
import Link from "next/link";
import {
  ThumbsUp,
  ThumbsDown,
  Copy,
  Info,
  Volume2,
  Mic,
  BookOpen,
  Stethoscope,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  FilePlus,
  Check,
  AlertTriangle,
  FileText
} from "lucide-react";
import SourceCard from "./SourceCard";
import VideoCard from "../video/VideoCard";
import { SourceItem, VideoItem, SafetyResult } from "@/lib/api";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  inputType?: "text" | "voice";
  sources?: SourceItem[];
  video?: VideoItem | null;
  safety?: SafetyResult | null;
  timestamp?: string;
  drugPills?: string[];
  medicalNote?: string;
}

interface ChatMessageProps {
  message: Message;
  fontSizeClass?: string;
  onFeedback?: (messageId: string, rating: 1 | -1) => void;
  onPlayAudio?: (text: string) => void;
  onStopSpeaking?: () => void;
  isSpeaking?: boolean;
  onCreatePlan?: (messageId: string) => void;
}

export default function ChatMessage({
  message,
  fontSizeClass = "text-sm",
  onFeedback,
  onPlayAudio,
  onStopSpeaking,
  isSpeaking,
  onCreatePlan,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const [feedbackSent, setFeedbackSent] = useState<1 | -1 | null>(null);
  const [copied, setCopied] = useState(false);
  const [showXAI, setShowXAI] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const handleFeedback = (rating: 1 | -1) => {
    setFeedbackSent(rating);
    if (onFeedback) onFeedback(message.id, rating);
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "contraindicated":
        return (
          <span className="px-2.5 py-1 rounded-lg bg-rose-100 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border border-rose-300 dark:border-rose-800 text-xs font-bold flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>ممنوع (Contraindicated)</span>
          </span>
        );
      case "warning":
        return (
          <span className="px-2.5 py-1 rounded-lg bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 border border-amber-300 dark:border-amber-800 text-xs font-bold flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>تحذير طبي (Warning)</span>
          </span>
        );
      case "caution":
        return (
          <span className="px-2.5 py-1 rounded-lg bg-yellow-100 dark:bg-yellow-950 text-yellow-800 dark:text-yellow-300 border border-yellow-300 dark:border-yellow-800 text-xs font-bold flex items-center gap-1">
            <Info className="w-3.5 h-3.5" />
            <span>يتطلب حذراً (Caution)</span>
          </span>
        );
      case "insufficient_evidence":
        return (
          <span className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 text-xs font-bold flex items-center gap-1">
            <Info className="w-3.5 h-3.5" />
            <span>أدلة غير كافية (Insufficient Evidence)</span>
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-lg bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800 text-xs font-bold flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>آمن وفق الأدلة (Safe)</span>
          </span>
        );
    }
  };

  return (
    <div className={`flex gap-3 my-4 ${isUser ? "justify-start" : "justify-start"}`}>
      
      {/* Bot Icon Avatar for Assistant */}
      {!isUser && (
        <div className="w-10 h-10 rounded-2xl bg-teal-700 text-white flex items-center justify-center shrink-0 shadow-xs mt-1">
          <Stethoscope className="w-5 h-5" />
        </div>
      )}

      <div className={`max-w-2xl w-full space-y-3 ${isUser ? "mr-auto" : "ml-auto"}`}>
        
        {/* User Message Bubble */}
        {isUser ? (
          <div className="p-4 md:p-5 rounded-2xl bg-teal-50 dark:bg-teal-950/80 border border-teal-200 dark:border-teal-900 text-slate-900 dark:text-slate-100 rounded-tr-none shadow-xs space-y-1">
            {message.inputType === "voice" && (
              <div className="flex items-center gap-1.5 text-xs text-teal-700 dark:text-teal-400 font-bold mb-1">
                <Mic className="w-4 h-4 animate-pulse" />
                <span>استفسار صوتي</span>
              </div>
            )}
            <p className={`whitespace-pre-wrap leading-relaxed ${fontSizeClass}`}>{message.content}</p>
            <div className="flex items-center justify-end gap-1 text-[11px] text-slate-400 font-mono pt-1">
              <span>{message.timestamp || "الآن"}</span>
            </div>
          </div>
        ) : (
          /* Assistant Message Bubble Card */
          <div className="p-5 md:p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100 leading-relaxed shadow-xs space-y-4">
            
            {/* Assistant Text Content with Elderly-Friendly Scaling */}
            <div className={`whitespace-pre-wrap leading-relaxed text-slate-800 dark:text-slate-100 ${fontSizeClass}`}>
              {message.content}
            </div>

            {/* Optional Verified Instructional Video Card */}
            {message.video && (
              <div className="pt-2">
                <VideoCard video={message.video} />
              </div>
            )}

            {/* Explainable AI (XAI) Safety Engine Breakdown Card */}
            {message.safety && (
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/70 border border-slate-200 dark:border-slate-700 space-y-3">
                <button
                  onClick={() => setShowXAI(!showXAI)}
                  className="w-full flex items-center justify-between text-xs font-bold text-slate-800 dark:text-slate-200 hover:text-teal-700 dark:hover:text-teal-400 transition-colors min-h-[44px]"
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-teal-700 dark:text-teal-400 shrink-0" />
                    <span>لماذا هذه الإجابة؟ (Safety Explanation)</span>
                    {getStatusBadge(message.safety.overall_status)}
                  </div>
                  {showXAI ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
                </button>

                {showXAI && (
                  <div className="space-y-3 pt-3 border-t border-slate-200 dark:border-slate-700 text-xs text-slate-700 dark:text-slate-300">
                    <div className="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
                      <p className="font-semibold text-slate-800 dark:text-slate-200 leading-relaxed">
                        {message.safety.summary}
                      </p>
                    </div>

                    {message.safety.xai?.patient_factors_used && message.safety.xai.patient_factors_used.length > 0 && (
                      <div className="space-y-1.5">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                          العوامل الصحية المستخدمة من ملفك:
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {message.safety.xai.patient_factors_used.map((factor, idx) => (
                            <span key={idx} className="px-2.5 py-1 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-800 dark:text-slate-200 font-medium">
                              {factor}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {message.safety.checks && message.safety.checks.length > 0 && (
                      <div className="space-y-2">
                        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
                          فحوصات الأمان التفصيلية:
                        </span>
                        <div className="space-y-1.5">
                          {message.safety.checks.map((chk, idx) => (
                            <div key={idx} className="p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 space-y-1">
                              <div className="flex items-center gap-2">
                                <span className="w-2 h-2 rounded-full bg-teal-600 shrink-0" />
                                <span className="font-bold text-slate-800 dark:text-slate-200">{chk.patient_factor}</span>
                              </div>
                              <p className="text-slate-600 dark:text-slate-300 mr-4">{chk.reason}</p>
                              {chk.evidence && chk.evidence.length > 0 && (
                                <div className="mt-1.5 mr-4 text-[11px] text-teal-800 dark:text-teal-300 font-mono bg-teal-50 dark:bg-teal-950/40 p-2 rounded-lg border border-teal-200 dark:border-teal-900">
                                  📄 المصدر: {chk.evidence[0].source} (صفحة {chk.evidence[0].page})
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Medical Caution Callout Box */}
            <div className="p-3.5 rounded-2xl bg-teal-50/60 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-900 text-slate-700 dark:text-slate-300 text-xs leading-relaxed flex items-start gap-2.5">
              <Info className="w-4 h-4 text-teal-700 dark:text-teal-400 shrink-0 mt-0.5" />
              <div>
                {message.medicalNote ||
                  "إذا استمرت الأعراض أو كان هناك أي استفسار دوائي معقد، يُفضل دائماً استشارة الطبيب أو الصيدلي المختص."}
              </div>
            </div>

            {/* RAG Evidence Sources Accordion */}
            {message.sources && message.sources.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                <div className="flex items-center gap-1.5 text-xs font-bold text-teal-800 dark:text-teal-300">
                  <BookOpen className="w-4 h-4" />
                  <span>الأدلة والمصادر المعتمدة ({message.sources.length})</span>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {message.sources.map((src, idx) => (
                    <SourceCard key={idx} source={src} />
                  ))}
                </div>
              </div>
            )}

            {/* Action Bar: Create Plan + Copy + Audio + Feedback (44px min targets) */}
            <div className="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              
              {/* Structured Medication Plan Action Button */}
              {onCreatePlan ? (
                <button
                  onClick={() => onCreatePlan(message.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-800 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900 border border-teal-200 dark:border-teal-800 text-xs font-bold transition-colors min-h-[44px] cursor-pointer"
                >
                  <FilePlus className="w-4 h-4 text-teal-700 dark:text-teal-400" />
                  <span>إنشاء خطة دوائية للمراجعة</span>
                </button>
              ) : (
                <Link
                  href="/plans"
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-800 dark:text-teal-300 hover:bg-teal-100 dark:hover:bg-teal-900 border border-teal-200 dark:border-teal-800 text-xs font-bold transition-colors min-h-[44px]"
                >
                  <FilePlus className="w-4 h-4 text-teal-700 dark:text-teal-400" />
                  <span>إنشاء خطة دوائية للمراجعة</span>
                </Link>
              )}

              <div className="flex items-center gap-1">
                {/* Audio Read-Aloud */}
                {onPlayAudio && (
                  <button
                    onClick={() => (isSpeaking ? onStopSpeaking?.() : onPlayAudio(message.content))}
                    className="p-2 rounded-xl text-slate-500 hover:text-teal-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                    title="قراءة صوتية"
                    aria-label="قراءة صوتية"
                  >
                    <Volume2 className={`w-4 h-4 ${isSpeaking ? "text-teal-600 animate-pulse" : ""}`} />
                  </button>
                )}

                {/* Copy Text */}
                <button
                  onClick={handleCopy}
                  className="p-2 rounded-xl text-slate-500 hover:text-teal-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                  title="نسخ النص"
                  aria-label="نسخ النص"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                </button>

                {/* Thumbs Up / Down Feedback */}
                <button
                  onClick={() => handleFeedback(1)}
                  className={`p-2 rounded-xl transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center ${
                    feedbackSent === 1
                      ? "text-teal-700 bg-teal-50 dark:bg-teal-950"
                      : "text-slate-500 hover:text-teal-700 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                  title="إجابة مفيدة"
                  aria-label="إجابة مفيدة"
                >
                  <ThumbsUp className="w-4 h-4" />
                </button>

                <button
                  onClick={() => handleFeedback(-1)}
                  className={`p-2 rounded-xl transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center ${
                    feedbackSent === -1
                      ? "text-rose-600 bg-rose-50 dark:bg-rose-950"
                      : "text-slate-500 hover:text-rose-600 hover:bg-slate-100 dark:hover:bg-slate-800"
                  }`}
                  title="إجابة غير مفيدة"
                  aria-label="إجابة غير مفيدة"
                >
                  <ThumbsDown className="w-4 h-4" />
                </button>
              </div>

            </div>

          </div>
        )}

      </div>

    </div>
  );
}
