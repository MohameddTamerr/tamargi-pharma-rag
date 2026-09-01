"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  X,
  ShieldCheck,
  AlertTriangle,
  Info,
  Pill,
  User,
  Activity,
  Heart,
  QrCode,
  CheckCircle2,
  FileText,
  ExternalLink,
  BookOpen,
  ArrowRight
} from "lucide-react";
import { createMedicationPlan, MedicationPlan } from "@/lib/api";

interface MedicationPlanModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  previewData: any;
  onPlanSaved?: (savedPlan: MedicationPlan) => void;
}

export default function MedicationPlanModal({
  isOpen,
  onClose,
  userId,
  previewData,
  onPlanSaved,
}: MedicationPlanModalProps) {
  const [isSaving, setIsSaving] = useState(false);
  const [savedPlan, setSavedPlan] = useState<MedicationPlan | null>(null);

  if (!isOpen || !previewData) return null;

  const {
    title,
    conversation_id,
    patient_info,
    confirmed_factors,
    medications = [],
    safety_summary,
    evidence_provenance = []
  } = previewData;

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const planPayload = {
        user_id: userId,
        conversation_id,
        title: title || "خطة دوائية للمراجعة الطبية",
        patient_info: patient_info || {},
        confirmed_factors: confirmed_factors || {},
        medications: medications || [],
        safety_summary: safety_summary || {},
        evidence_provenance: evidence_provenance || [],
        notes: "تم إنشاء هذه الخطة تلقائياً من محادثة موثقة مع مساعد تمرجي الذكي ومخصصة للمراجعة الصيدلية."
      };

      const result = await createMedicationPlan(planPayload);
      if (result) {
        setSavedPlan(result);
        if (onPlanSaved) onPlanSaved(result);
      }
    } catch (err) {
      console.error("Failed to save plan:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const getSafetyBadge = (status?: string) => {
    switch (status) {
      case "contraindicated":
        return (
          <span className="px-3 py-1 rounded-full bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-200 border border-rose-300 dark:border-rose-800 text-xs font-bold flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-rose-600" />
            <span>تعارض دوائي — يحتاج مراجعة مهنية</span>
          </span>
        );
      case "warning":
        return (
          <span className="px-3 py-1 rounded-full bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-800 text-xs font-bold flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            <span>تحذير طبي — يتطلب إشرافاً</span>
          </span>
        );
      case "caution":
        return (
          <span className="px-3 py-1 rounded-full bg-yellow-100 dark:bg-yellow-950/80 text-yellow-800 dark:text-yellow-200 border border-yellow-300 dark:border-yellow-800 text-xs font-bold flex items-center gap-1.5">
            <Info className="w-4 h-4 text-yellow-600" />
            <span>ملاحظة أمان — يتطلب حذراً</span>
          </span>
        );
      case "safe_no_known_issue":
        return (
          <span className="px-3 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-800 text-xs font-bold flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>آمن وفق القواعد المعتمدة</span>
          </span>
        );
      default:
        return (
          <span className="px-3 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 text-xs font-bold flex items-center gap-1.5">
            <Info className="w-4 h-4 text-slate-500" />
            <span>الأدلة غير كافية لإصدار حكم أمان شخصي</span>
          </span>
        );
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
      <div className="relative w-full max-w-2xl max-h-[90vh] flex flex-col rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden my-auto text-right">
        
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-950/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-extrabold text-slate-900 dark:text-slate-100 text-base">
                {savedPlan ? "تم حفظ الخطة الدوائية بنجاح" : "معاينة الخطة الدوائية للمراجعة"}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {savedPlan ? "رمز QR جاهز لمشاركته مع الصيدلي" : "مستخرجة تلقائياً من محادثتك وأدلة هيئة الدواء المصرية"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {savedPlan ? (
            /* Saved Success State with QR */
            <div className="text-center space-y-6 py-4">
              <div className="w-16 h-16 rounded-full bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-10 h-10" />
              </div>

              <div className="space-y-1">
                <h4 className="font-bold text-slate-900 dark:text-slate-100 text-lg">
                  {savedPlan.title}
                </h4>
                <p className="text-xs text-slate-500">
                  رقم الخطة المرجعي: <span className="font-mono">{savedPlan.id.slice(0, 16)}</span>
                </p>
              </div>

              {/* QR Container */}
              <div className="p-6 rounded-3xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 max-w-xs mx-auto space-y-3">
                <div className="w-44 h-44 bg-white p-2 rounded-2xl mx-auto flex items-center justify-center shadow-xs border border-slate-200">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(
                      `${typeof window !== "undefined" ? window.location.origin : ""}/verify-plan/${savedPlan.verification_token}`
                    )}`}
                    alt="Plan QR Verification Token"
                    className="w-full h-full object-contain"
                  />
                </div>
                <p className="text-[11px] text-slate-500">
                  وجّه كاميرا الهاتف أو جهاز الصيدلي لمسح الرمز واستعراض الخطة الموثقة
                </p>
              </div>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                <Link
                  href={`/verify-plan/${savedPlan.verification_token}`}
                  target="_blank"
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs flex items-center justify-center gap-2 shadow-md transition-colors"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>فتح صفحة الصيدلي الموثقة</span>
                </Link>
                <Link
                  href="/plans"
                  className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 font-bold text-xs flex items-center justify-center gap-2 transition-colors"
                >
                  <span>استعراض كل الخطط</span>
                  <ArrowRight className="w-4 h-4 rotate-180" />
                </Link>
              </div>
            </div>
          ) : (
            /* Read-Only Preview Content */
            <>
              {/* 1. Patient Demographics from Profile */}
              <div className="p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-300">
                    <User className="w-4 h-4 text-teal-600" />
                    <span>بيانات المريض (من الملف الشخصي)</span>
                  </div>
                  <Link
                    href="/profile"
                    className="text-[11px] text-teal-700 dark:text-teal-400 hover:underline"
                  >
                    تحديث الملف الشخصي
                  </Link>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                  <div className="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block text-[10px]">العمر</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">
                      {patient_info?.age ? `${patient_info.age} سنة` : "غير مسجل"}
                    </span>
                  </div>
                  <div className="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block text-[10px]">النوع</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">
                      {patient_info?.sex === "female" ? "أنثى" : (patient_info?.sex === "male" ? "ذكر" : "غير مسجل")}
                    </span>
                  </div>
                  <div className="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block text-[10px]">الوزن</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">
                      {patient_info?.weight_kg ? `${patient_info.weight_kg} كجم` : "غير مسجل"}
                    </span>
                  </div>
                  <div className="p-2 rounded-xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800">
                    <span className="text-slate-400 block text-[10px]">الطول</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">
                      {patient_info?.height_cm ? `${patient_info.height_cm} سم` : "غير مسجل"}
                    </span>
                  </div>
                </div>
              </div>

              {/* 2. Relevant Medical Factors */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 space-y-1.5">
                  <span className="text-slate-500 font-medium flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-amber-500" /> الحالات المؤكدة
                  </span>
                  <p className="font-bold text-slate-800 dark:text-slate-200">
                    {confirmed_factors?.conditions?.length > 0
                      ? confirmed_factors.conditions.join("، ")
                      : "لا توجد حالات مزمنة مسجلة"}
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 space-y-1.5">
                  <span className="text-slate-500 font-medium flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-500" /> الحساسية
                  </span>
                  <p className="font-bold text-slate-800 dark:text-slate-200">
                    {confirmed_factors?.allergies?.length > 0
                      ? confirmed_factors.allergies.join("، ")
                      : "لا توجد حساسية مسجلة"}
                  </p>
                </div>

                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/80 dark:border-slate-800 space-y-1.5">
                  <span className="text-slate-500 font-medium flex items-center gap-1.5">
                    <Pill className="w-3.5 h-3.5 text-teal-600" /> الأدوية الحالية
                  </span>
                  <p className="font-bold text-slate-800 dark:text-slate-200">
                    {confirmed_factors?.medications?.length > 0
                      ? confirmed_factors.medications.join("، ")
                      : "لا توجد أدوية حالية مسجلة"}
                  </p>
                </div>
              </div>

              {/* 3. Structured Candidate Medications */}
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-200">
                  <Pill className="w-4 h-4 text-teal-600" />
                  <span>الأدوية محل المراجعة</span>
                </div>

                {medications.map((med: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <h5 className="text-base font-extrabold text-slate-900 dark:text-slate-100">
                          {med.generic_name}
                          {med.brand_name && (
                            <span className="text-xs font-normal text-slate-500 mr-2">
                              ({med.brand_name})
                            </span>
                          )}
                        </h5>
                        <p className="text-xs text-slate-500 mt-0.5">
                          التركيز: <span className="font-semibold text-slate-700 dark:text-slate-300">{med.strength}</span> | الشكل: <span className="font-semibold text-slate-700 dark:text-slate-300">{med.dosage_form}</span> | طريقة التناول: <span className="font-semibold text-slate-700 dark:text-slate-300">{med.route}</span>
                        </p>
                      </div>

                      {getSafetyBadge(med.safety_status)}
                    </div>

                    {/* Instructions */}
                    <div className="p-2.5 rounded-xl bg-slate-50 dark:bg-slate-800/50 text-xs text-slate-700 dark:text-slate-300 border border-slate-100 dark:border-slate-800">
                      <span className="text-slate-400 block text-[10px] font-semibold mb-0.5">تعليمات الاستخدام المقترحة</span>
                      <p className="leading-relaxed">{med.instructions}</p>
                    </div>

                    {/* Evidence Provenance */}
                    {med.evidence_citations && med.evidence_citations.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[11px] font-bold text-slate-500 flex items-center gap-1">
                          <BookOpen className="w-3.5 h-3.5 text-teal-600" />
                          <span>سند الدليل الطبي (هيئة الدواء المصرية):</span>
                        </span>
                        <div className="space-y-1">
                          {med.evidence_citations.map((ev: any, evIdx: number) => (
                            <div
                              key={evIdx}
                              className="p-2 rounded-xl bg-teal-50/50 dark:bg-teal-950/20 border border-teal-100 dark:border-teal-900/40 text-[11px] text-teal-900 dark:text-teal-200"
                            >
                              <div className="font-bold flex items-center justify-between">
                                <span>{ev.source}</span>
                                <span className="text-[10px] font-mono bg-teal-100 dark:bg-teal-900/60 px-1.5 py-0.5 rounded">ص {ev.page}</span>
                              </div>
                              {ev.excerpt && (
                                <p className="text-[10px] text-teal-800/80 dark:text-teal-300/80 mt-1 line-clamp-2 italic">
                                  &ldquo;{ev.excerpt}&rdquo;
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {/* Disclaimer */}
              <div className="p-3 rounded-2xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/50 text-amber-900 dark:text-amber-200 text-xs leading-relaxed">
                <p className="font-semibold flex items-center gap-1.5 mb-1">
                  <ShieldCheck className="w-4 h-4 text-amber-600 shrink-0" />
                  <span>تنبيه مهني هام:</span>
                </p>
                <p className="text-[11px]">
                  هذه الخطة مجهزة للمراجعة المهنية مع الصيدلي أو الطبيب ولا تمثل وصفة طبية مستقلة أو بديلاً عن الفحص السريري.
                </p>
              </div>
            </>
          )}

        </div>

        {/* Modal Footer */}
        {!savedPlan && (
          <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-950/30">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 text-slate-700 dark:text-slate-300 font-bold text-xs transition-colors"
            >
              إلغاء
            </button>

            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-6 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-bold text-xs flex items-center gap-2 shadow-md shadow-teal-700/20 transition-all cursor-pointer"
            >
              {isSaving ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>جارٍ الحفظ...</span>
                </>
              ) : (
                <>
                  <QrCode className="w-4 h-4" />
                  <span>حفظ وتوليد رمز QR للمراجعة</span>
                </>
              )}
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
