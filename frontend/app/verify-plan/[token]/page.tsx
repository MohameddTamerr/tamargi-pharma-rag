"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import {
  Stethoscope,
  ShieldCheck,
  AlertTriangle,
  FileText,
  User,
  Calendar,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  BookOpen,
  Info
} from "lucide-react";
import { verifyPlanByToken, MedicationPlan } from "@/lib/api";

export default function VerifyPlanPage({ params }: { params: Promise<{ token: string }> }) {
  const resolvedParams = use(params);
  const token = resolvedParams.token;

  const [plan, setPlan] = useState<MedicationPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorStatus, setErrorStatus] = useState<string | null>(null);

  useEffect(() => {
    async function loadVerification() {
      setIsLoading(true);
      setErrorStatus(null);
      try {
        const data = await verifyPlanByToken(token);
        if (data) {
          setPlan(data);
        } else {
          setErrorStatus("not_found");
        }
      } catch (err: any) {
        if (err.message && err.message.includes("410")) {
          setErrorStatus("expired");
        } else {
          setErrorStatus("not_found");
        }
      } finally {
        setIsLoading(false);
      }
    }
    loadVerification();
  }, [token]);

  if (isLoading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center p-6 bg-[#f8fafc] text-slate-600">
        <div className="text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-teal-700 text-white flex items-center justify-center mx-auto animate-pulse">
            <Stethoscope className="w-6 h-6" />
          </div>
          <p className="text-sm font-bold">جاري التحقق من رمز الخطة الدوائية...</p>
        </div>
      </div>
    );
  }

  if (errorStatus === "expired" || errorStatus === "revoked") {
    return (
      <div className="min-h-screen w-full flex items-center justify-center p-6 bg-[#f8fafc]">
        <div className="max-w-md w-full p-8 rounded-3xl bg-white border border-slate-200 shadow-sm text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
            <AlertTriangle className="w-7 h-7" />
          </div>
          <h2 className="text-lg font-bold text-slate-800">
            This medication plan is no longer available for verification.
          </h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            انتهت صلاحية رمز التحقق أو تم إلغاء هذه الخطة الدوائية بواسطة المريض.
          </p>
        </div>
      </div>
    );
  }

  if (errorStatus || !plan) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center p-6 bg-[#f8fafc]">
        <div className="max-w-md w-full p-8 rounded-3xl bg-white border border-slate-200 shadow-sm text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
            <AlertCircle className="w-7 h-7" />
          </div>
          <h2 className="text-lg font-bold text-slate-800">رمز التحقق غير صالح</h2>
          <p className="text-xs text-slate-500 leading-relaxed">
            لم نتمكن من العثور على خطة دوائية مطابقة لهذا الرمز. تأكد من صحة الرابط أو رمز QR.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#f8fafc] text-slate-800 py-8 px-4 md:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        
        {/* Pharmacist Portal Header */}
        <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-teal-700 text-white flex items-center justify-center">
                <Stethoscope className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">
                  بوابة التحقق الصيدلي المباشر
                </h1>
                <span className="text-xs text-teal-800 font-bold block">
                  Tamargi.ai — Pharmacist Review Portal
                </span>
              </div>
            </div>

            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold shrink-0">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>رمز معتمد ونشط</span>
            </div>
          </div>

          {/* Audit Notice */}
          <div className="p-3.5 rounded-2xl bg-teal-50 border border-teal-200 text-teal-950 text-xs leading-relaxed flex items-start gap-2.5">
            <Info className="w-4 h-4 text-teal-700 shrink-0 mt-0.5" />
            <div>
              <strong>تأكيد مصدري للصيدلي:</strong> تم إنشاء هذه المسودة بواسطة <strong>Tamargi.ai</strong> كخطة استرشادية لمساعدة الصيدلي في مراجعة الأدوية والتأكد من ملاءمتها.
            </div>
          </div>
        </div>

        {/* Minimal Clinical Context */}
        <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-xs font-bold text-teal-800 uppercase tracking-wider flex items-center gap-2">
            <User className="w-4 h-4" />
            <span>بيانات الحالة السريرية المصاحبة</span>
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-slate-400 block text-[10px]">المريض</span>
              <span className="font-bold text-slate-800">{plan.patient_info?.full_name || "مريض عام"}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">العمر</span>
              <span className="font-bold text-slate-800">{plan.patient_info?.age ? `${plan.patient_info.age} سنة` : "غير محدد"}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">النوع</span>
              <span className="font-bold text-slate-800">{plan.patient_info?.sex === "female" ? "أنثى" : "ذكر"}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[10px]">تاريخ الإنشاء</span>
              <span className="font-bold text-slate-800">
                {new Date(plan.created_at).toLocaleDateString("ar-EG")}
              </span>
            </div>
          </div>

          {/* Clinical factors */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="font-bold text-slate-700 block text-[11px] mb-1">الأمراض المؤكدة:</span>
              <div className="text-slate-600 space-y-0.5">
                {plan.confirmed_factors?.conditions?.map((c, i) => (
                  <div key={i}>• {c}</div>
                )) || <div>لا توجد أمراض مسجلة</div>}
              </div>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200">
              <span className="font-bold text-slate-700 block text-[11px] mb-1">الحساسية والأدوية الحالية:</span>
              <div className="text-slate-600 space-y-0.5">
                {plan.confirmed_factors?.allergies?.map((a, i) => (
                  <div key={i}>• حساسية: {a}</div>
                ))}
                {plan.confirmed_factors?.medications?.map((m, i) => (
                  <div key={i}>• دواء حالي: {m}</div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Rx Medication Items */}
        <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-xs space-y-4">
          <h2 className="text-xs font-bold text-teal-800 uppercase tracking-wider flex items-center gap-2">
            <FileText className="w-4 h-4" />
            <span>قائمة الأدوية والملاحظات السريرية</span>
          </h2>

          <div className="overflow-x-auto rounded-2xl border border-slate-200">
            <table className="w-full text-right text-xs">
              <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200">
                <tr>
                  <th className="p-3">الدواء</th>
                  <th className="p-3">الشكل والقوة</th>
                  <th className="p-3">الجرعة</th>
                  <th className="p-3">توجيهات الصيدلي</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {plan.medications.map((m, idx) => (
                  <tr key={idx}>
                    <td className="p-3 font-bold text-slate-900">{m.generic_name}</td>
                    <td className="p-3 text-slate-600">{m.dosage_form || "Requires professional determination"}</td>
                    <td className="p-3 text-amber-800 font-medium">{m.dose || "Requires professional determination"}</td>
                    <td className="p-3 text-slate-600">{m.instructions || "يُحدد بمعرفة الصيدلي"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* EDA Source Evidence Provenance */}
        <div className="p-6 rounded-3xl bg-white border border-slate-200 shadow-xs space-y-3">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-teal-700" />
            <span>توثيق الأدلة المعتمدة من هيئة الدواء المصرية (EDA Evidence Provenance)</span>
          </h2>

          <div className="space-y-2 text-xs">
            {plan.evidence_provenance && plan.evidence_provenance.length > 0 ? (
              plan.evidence_provenance.map((ev, i) => (
                <div key={i} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <div className="font-bold text-teal-900 font-mono text-[11px]">
                    📄 {ev.source} (Page {ev.page})
                  </div>
                  {ev.excerpt && (
                    <p className="text-slate-600 text-[11px] leading-relaxed italic">
                      "{ev.excerpt}"
                    </p>
                  )}
                </div>
              ))
            ) : (
              <div className="p-3 rounded-xl bg-slate-50 text-slate-500 text-xs">
                تم تدقيق الخطة وفق قواعد ومعايير الأمان الوطنية المعتمدة.
              </div>
            )}
          </div>
        </div>

        {/* Pharmacist Footer Disclaimer */}
        <div className="text-center text-[11px] text-slate-500 space-y-1 py-4">
          <p className="font-bold text-slate-700">Tamargi.ai Medication Safety Engine</p>
          <p>هذه الصفحة مخصصة للاطلاع المهني للصيدلي ولا تمنح صلاحيات تعديل لحساب المريض.</p>
        </div>

      </div>
    </div>
  );
}
