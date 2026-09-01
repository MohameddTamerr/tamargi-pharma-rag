"use client";

import { useState, useRef, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import ChatMessage, { Message } from "./ChatMessage";
import ChatInput from "./ChatInput";
import ThinkingState from "./ThinkingState";
import AudioPlayer from "../voice/AudioPlayer";
import MedicationPlanModal from "../MedicationPlanModal";
import {
  sendChatMessage,
  submitFeedback,
  fetchConversationMessages,
  generateMedicationPlanPreview,
  fetchUserGeminiKeyStatus,
  UserKeyStatus
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import {
  Stethoscope,
  Pill,
  GitCompare,
  Wind,
  AlertTriangle,
  FileSpreadsheet,
  ShieldCheck,
  Info,
  CheckCircle2,
  Key
} from "lucide-react";

interface ChatProps {
  conversationId?: string;
  onOpenContext?: (contextData: any) => void;
}

export default function Chat(props: ChatProps) {
  return (
    <Suspense fallback={<div className="flex-1 flex items-center justify-center text-slate-400 text-sm">جاري تحميل المحادثة...</div>}>
      <ChatContent {...props} />
    </Suspense>
  );
}

function ChatContent({ conversationId: propConvId, onOpenContext }: ChatProps) {
  const searchParams = useSearchParams();
  const convIdFromUrl = searchParams.get("conv");
  const activeConvId = propConvId || convIdFromUrl || "default_conv";

  const { user, fontSize } = useAuth();
  const userId = user?.id || "";

  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentQuery, setCurrentQuery] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [textToSpeak, setTextToSpeak] = useState("");
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Plan modal states
  const [isPlanModalOpen, setIsPlanModalOpen] = useState(false);
  const [planPreviewData, setPlanPreviewData] = useState<any>(null);
  const [planNotice, setPlanNotice] = useState<string | null>(null);
  const [keyStatus, setKeyStatus] = useState<UserKeyStatus | null>(null);

  useEffect(() => {
    async function checkKey() {
      if (userId) {
        const s = await fetchUserGeminiKeyStatus();
        setKeyStatus(s);
      }
    }
    checkKey();
  }, [userId]);

  // Load conversation messages when activeConvId changes
  useEffect(() => {
    async function loadConv() {
      if (activeConvId && activeConvId !== "default_conv" && userId) {
        try {
          const fetched = await fetchConversationMessages(activeConvId, userId);
          if (fetched && fetched.length > 0) {
            const formatted: Message[] = fetched.map((m: any) => ({
              id: m.id,
              role: m.role,
              content: m.content,
              sources: m.message_sources || [],
              timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            }));
            setMessages(formatted);
            return;
          }
        } catch (e) {
          console.warn("Failed to load conversation messages:", e);
        }
      }
      setMessages([]);
    }
    loadConv();
  }, [activeConvId, userId]);

  // Scoped message auto-scroll: Scrolls ONLY inside the messages container
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSendMessage = useCallback(async (text: string, inputType: "text" | "voice" = "text") => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      inputType,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setCurrentQuery(text);
    setIsLoading(true);

    try {
      const response = await sendChatMessage(text, activeConvId, userId || "guest_user", inputType);

      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: response.answer,
        sources: response.sources,
        video: response.video,
        safety: response.safety,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botMsg]);

      // If condition confirmation was triggered and confirmed in backend, notify profile sync
      if (response.safety?.requires_confirmation === false) {
        window.dispatchEvent(new Event("patient_profile_updated"));
      }

      if (inputType === "voice") {
        setTextToSpeak(response.answer);
        setIsSpeaking(true);
      }
    } catch (err) {
      console.error("Error sending message:", err);
    } finally {
      setIsLoading(false);
    }
  }, [activeConvId, userId]);

  // Listen for custom submit query events from RightPanel FAQ
  useEffect(() => {
    const handleCustomQuery = (e: Event) => {
      const customEvent = e as CustomEvent<{ query: string }>;
      if (customEvent.detail && customEvent.detail.query) {
        handleSendMessage(customEvent.detail.query);
      }
    };
    window.addEventListener("submit_chat_query", handleCustomQuery);
    return () => {
      window.removeEventListener("submit_chat_query", handleCustomQuery);
    };
  }, [handleSendMessage]);

  const handleCreatePlanFromMessage = async (messageId: string) => {
    if (!userId) {
      setPlanNotice("برجاء تسجيل الدخول أولاً لإنشاء خطة دوائية موثقة.");
      setTimeout(() => setPlanNotice(null), 4000);
      return;
    }

    setIsLoading(true);
    setPlanNotice(null);
    try {
      const res = await generateMedicationPlanPreview(userId, activeConvId, messageId);

      if (res.status === "requires_confirmation") {
        const confirmMsg: Message = {
          id: Date.now().toString(),
          role: "assistant",
          content: res.prompt || `عندي مسجل إن عندك ${res.fact_value}، صح؟ (برجاء التأكيد للمتابعة)`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };
        setMessages((prev) => [...prev, confirmMsg]);
        return;
      }

      if (res.status === "insufficient_plan_evidence") {
        setPlanNotice(res.message || "المحادثة الحالية لا تحتوي على معلومات دوائية موثقة كافية لإنشاء خطة للمراجعة.");
        setTimeout(() => setPlanNotice(null), 5000);
        return;
      }

      if (res.status === "ready" && res.plan_preview) {
        setPlanPreviewData(res.plan_preview);
        setIsPlanModalOpen(true);
      } else {
        setPlanNotice("تعذر إنشاء الخطة الدوائية من المحادثة الحالية.");
        setTimeout(() => setPlanNotice(null), 4000);
      }
    } catch (err) {
      console.warn("Failed to generate plan:", err);
      setPlanNotice("حدث خطأ أثناء إعداد الخطة الدوائية.");
      setTimeout(() => setPlanNotice(null), 4000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = (messageId: string, rating: 1 | -1) => {
    if (userId) {
      submitFeedback(messageId, userId, rating);
    }
  };

  const handlePlayAudio = (text: string) => {
    setTextToSpeak(text);
    setIsSpeaking(true);
  };

  const handleStopSpeaking = () => {
    setIsSpeaking(false);
  };

  const getFontSizeClass = () => {
    if (fontSize === "large") return "text-base";
    if (fontSize === "extra-large") return "text-lg";
    return "text-sm";
  };

  const suggestionPrompts = [
    {
      title: "التداخلات الدوائية",
      prompt: "هل هناك تعارض بين الباراسيتامول والإيبوبروفين؟",
      icon: GitCompare,
      badge: "أمان دوائي",
    },
    {
      title: "استخدام البخاخات",
      prompt: "ازاي استخدم جهاز التربوهيلر بطريقة صحيحة؟",
      icon: Wind,
      badge: "فيديو موثق",
    },
    {
      title: "موانع الاستخدام",
      prompt: "ما هي موانع استخدام دواء باراسيتامول؟",
      icon: AlertTriangle,
      badge: "تحذيرات طبية",
    },
    {
      title: "الجرعات والإرشادات",
      prompt: "هل يمكن تناول الباراسيتامول على معدة فارغة؟",
      icon: Pill,
      badge: "إرشادات رسمية",
    },
  ];

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden bg-white dark:bg-slate-900 border-x border-slate-200/80 dark:border-slate-800 relative">
      
      {/* Audio Player Component */}
      <AudioPlayer
        textToSpeak={textToSpeak}
        isSpeaking={isSpeaking}
        onStopSpeaking={handleStopSpeaking}
      />

      {/* Missing BYOK API Key Top Warning Banner */}
      {keyStatus && !keyStatus.has_key && !keyStatus.fallback_allowed && (
        <div className="bg-amber-50 dark:bg-amber-950/70 border-b border-amber-200 dark:border-amber-900/60 p-2.5 px-4 flex items-center justify-between text-xs text-amber-900 dark:text-amber-200 z-20 shrink-0">
          <div className="flex items-center gap-2">
            <Key className="w-4 h-4 text-amber-600 dark:text-amber-400 shrink-0" />
            <span>مطلوب مفتاح Gemini API: يرجى إضافة مفتاحك لتشغيل الإجابات السريرية الذكية.</span>
          </div>
          <Link
            href="/profile#byok-key"
            className="font-bold underline text-teal-700 dark:text-teal-400 hover:text-teal-900 dark:hover:text-teal-300 shrink-0"
          >
            إضافة المفتاح ←
          </Link>
        </div>
      )}

      {/* Plan Generation Notice Toast */}
      {planNotice && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 px-4 py-2.5 rounded-2xl bg-slate-900 text-white text-xs font-bold shadow-xl flex items-center gap-2 animate-fade-in border border-slate-700">
          <Info className="w-4 h-4 text-teal-400 shrink-0" />
          <span>{planNotice}</span>
        </div>
      )}

      {/* Read-Only Medication Plan Modal */}
      {isPlanModalOpen && planPreviewData && (
        <MedicationPlanModal
          isOpen={isPlanModalOpen}
          onClose={() => setIsPlanModalOpen(false)}
          userId={userId}
          previewData={planPreviewData}
        />
      )}

      {/* Independent Messages Container (Scrolls independently, no whole-page scroll) */}
      <div
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6 min-h-0 chat-messages-container"
      >
        {messages.length === 0 && (
          <div className="max-w-3xl mx-auto py-8 space-y-6 animate-fade-in text-center">
            
            <div className="w-16 h-16 rounded-2xl bg-teal-700 text-white flex items-center justify-center mx-auto shadow-sm">
              <Stethoscope className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h2 className="text-xl md:text-2xl font-extrabold text-slate-900 dark:text-slate-100">
                كيف أقدر أساعدك بخصوص أدويتك اليوم؟
              </h2>
              <p className="text-xs md:text-sm text-slate-600 dark:text-slate-400 max-w-xl mx-auto leading-relaxed">
                أنا <span className="font-bold text-teal-800 dark:text-teal-300">Tamargi.ai</span>، مساعدك الطبي والدوائي المعتمد. اسألني عن أي دواء، موانع استخدام، تداخلات دوائية، أو طريقة استخدام أجهزة الاستنشاق.
              </p>
            </div>

            {/* Quick Suggestion Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-right">
              {suggestionPrompts.map((sug, idx) => {
                const Icon = sug.icon;
                return (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(sug.prompt)}
                    className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-400 dark:hover:border-teal-600 hover:shadow-sm transition-all text-right group min-h-[44px] flex flex-col justify-between cursor-pointer"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-8 h-8 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300 flex items-center justify-center group-hover:bg-teal-700 group-hover:text-white transition-colors">
                        <Icon className="w-4 h-4" />
                      </div>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                        {sug.badge}
                      </span>
                    </div>
                    <span className="text-xs md:text-sm font-bold text-slate-800 dark:text-slate-200 group-hover:text-teal-800 dark:group-hover:text-teal-300 transition-colors block">
                      {sug.title}
                    </span>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 line-clamp-1">
                      {sug.prompt}
                    </p>
                  </button>
                );
              })}
            </div>

            {/* Trust Footer Note */}
            <div className="flex items-center justify-center gap-2 pt-4 text-xs text-slate-500">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>جميع الإجابات مستندة حصراً إلى الأدلة الرسمية لهيئة الدواء المصرية</span>
            </div>

          </div>
        )}

        {/* Message Bubble List */}
        {messages.map((msg) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            fontSizeClass={getFontSizeClass()}
            onFeedback={handleFeedback}
            onPlayAudio={handlePlayAudio}
            onStopSpeaking={handleStopSpeaking}
            isSpeaking={isSpeaking}
            onCreatePlan={handleCreatePlanFromMessage}
          />
        ))}

        {/* Thinking Indicator */}
        {isLoading && <ThinkingState query={currentQuery} />}
      </div>

      {/* Anchored Bottom Composer */}
      <div className="w-full flex-shrink-0 p-3 md:p-4 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 shadow-sm z-20 chat-composer no-print">
        <div className="max-w-3xl mx-auto">
          <ChatInput
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
            isSpeaking={isSpeaking}
            onStopSpeaking={handleStopSpeaking}
          />
          
          <div className="flex items-center justify-center gap-2 mt-2 text-[11px] text-slate-500 text-center">
            <Info className="w-3.5 h-3.5 text-teal-600 shrink-0" />
            <span>
              خطة المراجعة الدوائية الاسترشادية لا تُعد بديلاً عن التشخيص أو التوجيه الطبي المباشر.
            </span>
          </div>
        </div>
      </div>

    </div>
  );
}
