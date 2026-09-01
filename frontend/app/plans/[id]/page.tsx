"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { QRCodeSVG } from "qrcode.react";
import {
  FileText,
  Printer,
  ChevronRight,
  ShieldCheck,
  AlertTriangle,
  Info,
  Calendar,
  User,
  Stethoscope,
  ExternalLink,
  QrCode,
  Lock
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { fetchPlanById, MedicationPlan } from "@/lib/api";
import ProtectedRoute from "@/components/ProtectedRoute";
import Sidebar from "@/components/Sidebar";

export default function PlanDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const planId = resolvedParams.id;

  return (
    <ProtectedRoute>
      <div className="flex flex-1 overflow-hidden min-h-0 w-full h-full bg-[#f3f6fa] dark:bg-slate-950">
        <Sidebar activePath="/plans" />
        <main className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto">
          <PlanDetailContent planId={planId} />
        </main>
      </div>
    </ProtectedRoute>
  );
}

function PlanDetailContent({ planId }: { planId: string }) {
  const router = useRouter();
  const { user } = useAuth();
  const userId = user?.id || "";

  const [plan, setPlan] = useState<MedicationPlan | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [originUrl, setOriginUrl] = useState("");

  useEffect(() => {
    if (typeof window !== "undefined") {
      setOriginUrl(window.location.origin);
    }
    loadPlan();
  }, [planId, userId]);

  const loadPlan = async () => {
    setIsLoading(true);
    try {
      const data = await fetchPlanById(planId, userId);
      setPlan(data);
    } catch (e) {
      console.warn("Error fetching plan:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePrint = () => {
    if (typeof window !== "undefined") {
      window.print();
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-slate-500">
        جاري تحميل الخطة الدوائية...
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 space-y-4">
        <p className="text-sm font-bold text-slate-700">لم يتم العثور على الخطة الدوائية المطلوبة أو انتهت صلاحيتها.</p>
        <Link href="/plans" className="px-4 py-2 rounded-xl bg-teal-700 text-white text-xs font-bold">
          العودة لقائمة الخطط
        </Link>
      </div>
    );
  }

  const verifyUrl = `${originUrl}/verify-plan/${plan.verification_token}`;

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] dark:bg-slate-950 overflow-y-auto p-4 md:p-8">
      <div className="max-w-4xl mx-auto w-full space-y-6">
        
        {/* Navigation & Action Bar (Hidden in Print) */}
        <div className="flex items-center justify-between no-print pb-2">
          <Link
            href="/plans"
            className="flex items-center gap-1.5 text-slate-600 dark:text-slate-400 hover:text-teal-700 text-xs font-bold min-h-[44px]"
          >
            <ChevronRight className="w-4 h-4" />
            <span>العودة إلى الخطط الدوائية</span>
          </Link>

          <button
            onClick={handlePrint}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white text-xs font-bold shadow-xs transition-colors min-h-[44px]"
          >
            <Printer className="w-4 h-4" />
            <span>طباعة الخطة / حفظ كـ PDF</span>
          </button>
        </div>

        {/* Prescription Sheet Card (Formatted for screen and print) */}
        <div className="prescription-sheet p-6 md:p-10 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-8 text-slate-900 dark:text-slate-100">
          
          {/* Prescription Header */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pb-6 border-b-2 border-teal-700/80">
            <div className="space-y-1.5">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-xl bg-teal-700 text-white flex items-center justify-center font-extrabold text-lg shadow-xs">
                  <Stethoscope className="w-6 h-6" />
                </div>
                <div>
                  <h1 className="text-xl font-black text-slate-900 dark:text-slate-100 tracking-tight">
                    Tamargi.ai
                  </h1>
                  <span className="text-xs text-teal-800 dark:text-teal-400 font-bold block -mt-0.5">
                    مسودة خطة دوائية للمراجعة الطبية والصيدلانية
                  </span>
                </div>
              </div>
              <p className="text-[11px] text-slate-500 font-medium">
                Draft Medication Plan for Professional Review
              </p>
            </div>

            {/* Plan Meta */}
            <div className="text-left sm:text-right space-y-1 text-xs text-slate-600 dark:text-slate-400">
              <div>
                <span className="font-bold text-slate-800 dark:text-slate-200">رقم الخطة (Plan ID): </span>
                <span className="font-mono text-[11px]">{plan.id.slice(0, 13)}...</span>
              </div>
              <div>
                <span className="font-bold text-slate-800 dark:text-slate-200">تاريخ الإنشاء: </span>
                <span>
                  {new Date(plan.created_at).toLocaleDateString("ar-EG", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </span>
              </div>
              <div>
                <span className="font-bold text-slate-800 dark:text-slate-200">الحالة: </span>
                <span className="text-teal-700 dark:text-teal-400 font-bold">جاهزة للتقييم الصيدلي</span>
              </div>
            </div>
          </div>

          {/* Patient Details Grid */}
          <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-3">
            <h3 className="text-xs font-bold text-teal-800 dark:text-teal-400 uppercase tracking-wider flex items-center gap-1.5">
              <User className="w-4 h-4" />
              <span>بيانات المريض (Patient Information)</span>
            </h3>
            
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-slate-400 block text-[10px]">الاسم</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">{plan.patient_info?.full_name || "مريض عام"}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">العمر</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">{plan.patient_info?.age ? `${plan.patient_info.age} سنة` : "غير محدد"}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">النوع</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">{plan.patient_info?.sex === "female" ? "أنثى" : "ذكر"}</span>
              </div>
              <div>
                <span className="text-slate-400 block text-[10px]">الوزن</span>
                <span className="font-bold text-slate-800 dark:text-slate-200">{plan.patient_info?.weight_kg ? `${plan.patient_info.weight_kg} كجم` : "غير محدد"}</span>
              </div>
            </div>
          </div>

          {/* Confirmed Medical Factors */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 space-y-1.5">
              <span className="font-bold text-slate-700 dark:text-slate-300 block text-[11px]">الأمراض المزمنة المسجلة:</span>
              <div className="text-slate-600 dark:text-slate-400 space-y-0.5">
                {plan.confirmed_factors?.conditions?.map((c, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-600 shrink-0" />
                    <span>{c}</span>
                  </div>
                )) || <div>لا توجد أمراض مسجلة</div>}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 space-y-1.5">
              <span className="font-bold text-slate-700 dark:text-slate-300 block text-[11px]">الحساسية الدوائية:</span>
              <div className="text-slate-600 dark:text-slate-400 space-y-0.5">
                {plan.confirmed_factors?.allergies?.map((a, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-rose-600 shrink-0" />
                    <span>{a}</span>
                  </div>
                )) || <div>لا توجد حساسية مسجلة</div>}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 space-y-1.5">
              <span className="font-bold text-slate-700 dark:text-slate-300 block text-[11px]">الأدوية الحالية:</span>
              <div className="text-slate-600 dark:text-slate-400 space-y-0.5">
                {plan.confirmed_factors?.medications?.map((m, i) => (
                  <div key={i} className="flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0" />
                    <span>{m}</span>
                  </div>
                )) || <div>لا توجد أدوية مسجلة</div>}
              </div>
            </div>
          </div>

          {/* Rx / Medication Plan Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <span className="text-teal-700 dark:text-teal-400 font-serif text-lg">℞</span>
                <span>جدول الأدوية المقترحة للمراجعة (Medication Plan)</span>
              </h3>
            </div>

            <div className="overflow-x-auto rounded-2xl border border-slate-200 dark:border-slate-700">
              <table className="w-full text-right text-xs">
                <thead className="bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold border-b border-slate-200 dark:border-slate-700">
                  <tr>
                    <th className="p-3">الدواء (Generic / Brand)</th>
                    <th className="p-3">الشكل الدوائي والقوة</th>
                    <th className="p-3">طريقة الاستخدام</th>
                    <th className="p-3">الجرعة والتكرار</th>
                    <th className="p-3">تعليمات المريض</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {plan.medications.map((med, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                      <td className="p-3 font-bold text-slate-900 dark:text-slate-100">
                        {med.generic_name}
                        {med.brand_name && <span className="block text-[10px] text-slate-500 font-normal">({med.brand_name})</span>}
                      </td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">
                        <div>{med.dosage_form || "Requires professional determination"}</div>
                        <div className="text-[10px] text-slate-500">{med.strength || "Requires professional determination"}</div>
                      </td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">
                        {med.route || "Oral"}
                      </td>
                      <td className="p-3 text-amber-800 dark:text-amber-300 font-medium">
                        <div>{med.dose || "Requires professional determination"}</div>
                        <div className="text-[10px] text-slate-500">{med.frequency || "يُحدد بمعرفة الطبيب المعالج"}</div>
                      </td>
                      <td className="p-3 text-slate-600 dark:text-slate-400">
                        {med.instructions || "يُحدد بمعرفة الصيدلي"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Safety Summary Section */}
          <div className="p-5 rounded-2xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 space-y-3">
            <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-teal-700 dark:text-teal-400" />
              <span>ملخص فحص الأمان الدوائي (Safety Verification Summary)</span>
            </h3>
            
            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-semibold">
              {plan.safety_summary?.summary_text || "تمت مراجعة الخطة مع محددات أمان هيئة الدواء المصرية."}
            </p>

            {plan.evidence_provenance && plan.evidence_provenance.length > 0 && (
              <div className="space-y-1.5 pt-2 border-t border-slate-200 dark:border-slate-700 text-[11px] text-slate-600 dark:text-slate-400">
                <span className="font-bold text-slate-700 dark:text-slate-300 block">مرجعية الأدلة المصرية المعتمدة (EDA Provenance):</span>
                {plan.evidence_provenance.map((ev, i) => (
                  <div key={i} className="font-mono p-2 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700">
                    📄 {ev.source} — صفحة {ev.page} ({ev.section || "Monograph Evidence"})
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* QR Verification & Security Footer */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 p-6 rounded-2xl bg-teal-50/70 dark:bg-teal-950/40 border border-teal-200 dark:border-teal-900">
            <div className="space-y-2 text-right">
              <div className="flex items-center gap-2">
                <QrCode className="w-5 h-5 text-teal-700 dark:text-teal-400" />
                <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  رمز التحقق الصيدلي المباشر (Pharmacist Verification QR)
                </h4>
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md leading-relaxed">
                امسح الرمز بواسطة كاميرا الهاتف لفتح بوابة التحقق الصيدلي الآمنة وقراءة تفاصيل الأدلة المعتمدة لهذه الخطة.
              </p>
              <div className="text-[10px] text-slate-400 font-mono">
                Token: {plan.verification_token}
              </div>
            </div>

            {/* QR Code Container */}
            <div className="p-3 bg-white rounded-2xl shadow-xs border border-slate-200 shrink-0">
              <QRCodeSVG
                value={verifyUrl}
                size={120}
                level="M"
                includeMargin={false}
              />
            </div>
          </div>

          {/* Official Safety Disclaimer */}
          <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-center text-xs text-slate-600 dark:text-slate-400 leading-relaxed space-y-1">
            <p className="font-bold text-slate-800 dark:text-slate-200">
              إخلاء مسؤولية طبي واعتماد صيدلاني
            </p>
            <p>
              هذه الخطة تم إنشاؤها بواسطة Tamargi.ai للمساعدة في مراجعة الأدوية، ولا تُعد بديلاً عن وصف أو مراجعة الطبيب أو الصيدلي.
            </p>
          </div>

        </div>

      </div>
    </div>
  );
}
