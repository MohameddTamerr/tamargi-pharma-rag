"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Heart,
  CheckCircle2,
  Pill,
  Activity,
  ClipboardList,
  HelpCircle,
  RefreshCw,
  AlertCircle,
  ChevronLeft,
  QrCode
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { fetchPatientProfile, PatientProfileData } from "@/lib/api";
import { SUGGESTED_QUESTIONS } from "@/lib/faq-config";

interface RightPanelProps {
  onSelectQuestion?: (question: string) => void;
}

export default function RightPanel({ onSelectQuestion }: RightPanelProps) {
  const { user } = useAuth();
  const router = useRouter();
  const userId = user?.id;

  const [profile, setProfile] = useState<PatientProfileData | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [hasError, setHasError] = useState<boolean>(false);

  const loadProfile = useCallback(async () => {
    if (!userId) {
      setProfile(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setHasError(false);
    try {
      const data = await fetchPatientProfile(userId);
      setProfile(data);
    } catch (err) {
      console.warn("Failed to load health summary profile:", err);
      setHasError(true);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadProfile();

    const handleProfileUpdate = () => {
      loadProfile();
    };

    window.addEventListener("patient_profile_updated", handleProfileUpdate);
    return () => {
      window.removeEventListener("patient_profile_updated", handleProfileUpdate);
    };
  }, [loadProfile]);

  // Format compact lists
  const activeAllergies = (profile?.allergies || []).filter((a) => a.active);
  const activeMeds = (profile?.medications || []).filter((m) => m.active);
  const activeConditions = (profile?.conditions || []).filter((c) => c.active);

  const formatSummaryList = (items: string[], emptyText: string) => {
    if (!items || items.length === 0) return emptyText;
    if (items.length === 1) return items[0];
    return `${items[0]} +${items.length - 1}`;
  };

  const allergyDisplay = formatSummaryList(
    activeAllergies.map((a) => a.allergen),
    "لا توجد حساسية مسجلة"
  );
  const medsDisplay = formatSummaryList(
    activeMeds.map((m) => m.generic_name || m.brand_name || ""),
    "لا توجد أدوية حالية مسجلة"
  );
  const conditionsDisplay = formatSummaryList(
    activeConditions.map((c) => c.condition_name),
    "لا توجد حالات مزمنة مسجلة"
  );

  return (
    <aside className="w-[300px] p-4 space-y-4 hidden lg:flex flex-col flex-shrink-0 h-full overflow-y-auto border-r border-slate-200/80 dark:border-slate-800 bg-[#f3f6fa] dark:bg-slate-950">
      
      {/* 1. Real Health Summary Card */}
      <div className="p-4 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-slate-800 dark:text-slate-100 font-bold text-sm">
            <Heart className="w-4 h-4 text-teal-600" />
            <span>ملخصك الصحي</span>
          </div>
          <Link
            href="/profile"
            className="text-xs text-slate-400 hover:text-teal-700 transition-colors font-medium flex items-center gap-0.5"
          >
            <span>عرض الكل</span>
            <ChevronLeft className="w-3 h-3" />
          </Link>
        </div>

        {isLoading ? (
          <div className="py-4 text-center space-y-2">
            <div className="w-5 h-5 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-[11px] text-slate-500">جارٍ تحميل ملخصك الصحي...</p>
          </div>
        ) : hasError ? (
          <div className="p-3 rounded-2xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-center space-y-2">
            <p className="text-xs text-rose-700 dark:text-rose-300 font-medium">
              تعذر تحميل ملخصك الصحي
            </p>
            <button
              onClick={loadProfile}
              className="px-3 py-1 rounded-full bg-rose-100 dark:bg-rose-900 text-rose-800 dark:text-rose-200 text-xs font-semibold hover:bg-rose-200 transition-colors flex items-center justify-center gap-1 mx-auto"
            >
              <RefreshCw className="w-3 h-3" />
              <span>إعادة المحاولة</span>
            </button>
          </div>
        ) : (
          <div className="space-y-2 text-xs">
            {/* Allergies */}
            <div className="flex items-center justify-between p-2.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <span className="text-slate-600 dark:text-slate-400 font-medium">الحساسية</span>
              <span className={`flex items-center gap-1 font-bold ${
                activeAllergies.length > 0
                  ? "text-rose-600 dark:text-rose-400"
                  : "text-slate-500 dark:text-slate-400 font-normal"
              }`}>
                {activeAllergies.length > 0 && <AlertCircle className="w-3.5 h-3.5" />}
                {allergyDisplay}
              </span>
            </div>

            {/* Current Meds */}
            <div className="flex items-center justify-between p-2.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400 font-medium">
                <Pill className="w-3.5 h-3.5 text-teal-600" /> الأدوية الحالية
              </span>
              <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-semibold ${
                activeMeds.length > 0
                  ? "bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-300"
                  : "text-slate-500 dark:text-slate-400 font-normal"
              }`}>
                {medsDisplay}
              </span>
            </div>

            {/* Chronic Conditions */}
            <div className="flex items-center justify-between p-2.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800">
              <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400 font-medium">
                <Activity className="w-3.5 h-3.5 text-amber-500" /> الحالات المزمنة
              </span>
              <span className={`font-bold ${
                activeConditions.length > 0
                  ? "text-slate-800 dark:text-slate-200"
                  : "text-slate-500 dark:text-slate-400 font-normal"
              }`}>
                {conditionsDisplay}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 2. Truthful Pharmacist Plan Preparation Card */}
      <div className="p-4 rounded-3xl bg-[#eef7f5] dark:bg-teal-950/40 border border-teal-200/80 dark:border-teal-800/50 shadow-xs space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div>
            <h4 className="text-xs font-extrabold text-slate-900 dark:text-slate-100">
              جهّز خطتك لمراجعة الصيدلي
            </h4>
            <p className="text-[11px] text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">
              أنشئ خطة دوائية موثقة من محادثتك لمشاركتها بأمان مع الصيدلي عبر رمز QR
            </p>
          </div>
          <div className="w-9 h-9 rounded-2xl bg-white dark:bg-slate-800 text-teal-700 dark:text-teal-400 flex items-center justify-center shadow-xs shrink-0">
            <QrCode className="w-5 h-5" />
          </div>
        </div>

        <Link
          href="/plans"
          className="w-full py-2.5 px-4 rounded-full bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs shadow-md shadow-teal-700/20 transition-all flex items-center justify-center gap-1.5"
        >
          <ClipboardList className="w-3.5 h-3.5" />
          <span>استعراض الخطط الدوائية</span>
        </Link>
      </div>

      {/* 3. Centralized FAQ / Suggested Questions Card */}
      <div className="p-4 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs space-y-2.5">
        <div className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800 dark:text-slate-100">
          <HelpCircle className="w-3.5 h-3.5 text-teal-600" />
          <h4>أكثر الأسئلة شيوعاً</h4>
        </div>

        <div className="space-y-1.5">
          {SUGGESTED_QUESTIONS.map((faq) => (
            <button
              key={faq.id}
              onClick={() => onSelectQuestion && onSelectQuestion(faq.question)}
              className="w-full text-right p-2.5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 hover:bg-teal-50 dark:hover:bg-slate-800 border border-slate-100 dark:border-slate-800 text-xs text-slate-700 dark:text-slate-300 font-medium transition-colors flex items-center justify-between gap-2 group cursor-pointer"
            >
              <span className="line-clamp-2 leading-relaxed group-hover:text-teal-800 dark:group-hover:text-teal-300 transition-colors">
                {faq.question}
              </span>
              <ChevronLeft className="w-3.5 h-3.5 text-slate-400 group-hover:text-teal-700 shrink-0 transition-transform group-hover:-translate-x-0.5" />
            </button>
          ))}
        </div>
      </div>

    </aside>
  );
}
