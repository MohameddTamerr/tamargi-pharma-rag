"use client";

import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  FileText,
  Plus,
  Calendar,
  ShieldCheck,
  QrCode,
  Printer,
  Trash2,
  ChevronLeft,
  AlertTriangle,
  Stethoscope,
  Info,
  ExternalLink,
  MessageSquare,
  ClipboardList
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { fetchUserPlans, deleteMedicationPlan, MedicationPlan } from "@/lib/api";
import ProtectedRoute from "@/components/ProtectedRoute";
import Sidebar from "@/components/Sidebar";

export default function PlansPage() {
  return (
    <ProtectedRoute>
      <div className="flex flex-1 overflow-hidden min-h-0 w-full h-full bg-[#f3f6fa] dark:bg-slate-950">
        <Sidebar activePath="/plans" />
        <main className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto p-4 md:p-8">
          <Suspense fallback={<div className="flex-1 flex items-center justify-center p-8 text-slate-500">جاري تحميل الخطط الدوائية...</div>}>
            <PlansContent />
          </Suspense>
        </main>
      </div>
    </ProtectedRoute>
  );
}

function PlansContent() {
  const router = useRouter();
  const { user } = useAuth();
  const userId = user?.id || "";

  const [plans, setPlans] = useState<MedicationPlan[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (userId) {
      loadPlans();
    }
  }, [userId]);

  const loadPlans = async () => {
    if (!userId) return;
    setIsLoading(true);
    try {
      const data = await fetchUserPlans(userId);
      setPlans(data);
    } catch (e) {
      console.warn("Failed to load plans:", e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (planId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm("هل أنت متأكد من رغبتك في حذف هذه الخطة الدوائية؟")) return;
    try {
      const ok = await deleteMedicationPlan(planId, userId);
      if (ok) {
        setPlans((prev) => prev.filter((p) => p.id !== planId));
      }
    } catch (err) {
      console.warn("Failed to delete plan:", err);
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case "contraindicated":
        return (
          <span className="px-2.5 py-1 rounded-full bg-rose-100 dark:bg-rose-950/80 text-rose-800 dark:text-rose-200 border border-rose-300 dark:border-rose-800 text-[11px] font-bold flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-rose-600" />
            <span>تعارض دوائي</span>
          </span>
        );
      case "warning":
        return (
          <span className="px-2.5 py-1 rounded-full bg-amber-100 dark:bg-amber-950/80 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-800 text-[11px] font-bold flex items-center gap-1">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            <span>تحذير طبي</span>
          </span>
        );
      case "caution":
        return (
          <span className="px-2.5 py-1 rounded-full bg-yellow-100 dark:bg-yellow-950/80 text-yellow-800 dark:text-yellow-200 border border-yellow-300 dark:border-yellow-800 text-[11px] font-bold flex items-center gap-1">
            <Info className="w-3 h-3 text-yellow-600" />
            <span>يتطلب حذراً</span>
          </span>
        );
      case "safe_no_known_issue":
        return (
          <span className="px-2.5 py-1 rounded-full bg-emerald-100 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-200 border border-emerald-300 dark:border-emerald-800 text-[11px] font-bold flex items-center gap-1">
            <ShieldCheck className="w-3 h-3 text-emerald-600" />
            <span>آمن معتمد</span>
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700 text-[11px] font-bold flex items-center gap-1">
            <Info className="w-3 h-3 text-slate-500" />
            <span>قيد المراجعة</span>
          </span>
        );
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-extrabold text-xl md:text-2xl">
            <ClipboardList className="w-6 h-6 text-teal-700 dark:text-teal-400" />
            <h1>سجل الخطط الدوائية للمراجعة</h1>
          </div>
          <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400">
            خطط دوائية استرشادية مستخرجة وموثقة من محادثاتك الطبية لتقديمها للصيدلي
          </p>
        </div>

        <Link
          href="/chat"
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-2xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs md:text-sm shadow-md shadow-teal-700/20 transition-all cursor-pointer shrink-0"
        >
          <MessageSquare className="w-4 h-4" />
          <span>ابدأ محادثة لإنشاء خطة جديدة</span>
        </Link>
      </div>

      {/* Plan List Content */}
      {isLoading ? (
        <div className="py-16 text-center space-y-3">
          <div className="w-8 h-8 border-3 border-teal-700 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-medium text-slate-500">جارٍ تحميل الخطط الدوائية...</p>
        </div>
      ) : plans.length === 0 ? (
        <div className="py-16 px-6 text-center rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center mx-auto">
            <FileText className="w-8 h-8" />
          </div>
          <div className="space-y-1 max-w-md mx-auto">
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">
              لا توجد خطط دوائية مسجلة حالياً
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              يمكنك إنشاء خطة دوائية موثقة تلقائياً من أي محادثة في تمرجي تحتوي على أدوية تم فحص أمانها.
            </p>
          </div>
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs shadow-md transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            <span>الذهاب إلى المحادثة</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {plans.map((plan) => (
            <div
              key={plan.id}
              onClick={() => router.push(`/plans/${plan.id}`)}
              className="p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-400 dark:hover:border-teal-600 shadow-xs hover:shadow-md transition-all cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 group"
            >
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-extrabold text-slate-900 dark:text-slate-100 text-base group-hover:text-teal-700 dark:group-hover:text-teal-400 transition-colors">
                    {plan.title}
                  </h3>
                  {getStatusBadge(plan.safety_summary?.overall_status)}
                </div>

                <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-teal-600" />
                    <span>{new Date(plan.created_at).toLocaleDateString("ar-EG")}</span>
                  </span>
                  <span>•</span>
                  <span>{plan.medications?.length || 0} أدوية مسجلة</span>
                  <span>•</span>
                  <span className="font-mono text-[11px]">رمز: {plan.verification_token?.slice(0, 8)}...</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 shrink-0">
                <Link
                  href={`/verify-plan/${plan.verification_token}`}
                  target="_blank"
                  onClick={(e) => e.stopPropagation()}
                  className="p-2.5 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 hover:bg-teal-100 dark:hover:bg-teal-900 border border-teal-200 dark:border-teal-800 text-xs font-bold transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                  title="عرض رمز QR وصفحة الصيدلي"
                >
                  <QrCode className="w-4 h-4" />
                </Link>

                <button
                  onClick={(e) => handleDelete(plan.id, e)}
                  className="p-2.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-xl transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                  title="حذف الخطة"
                >
                  <Trash2 className="w-4 h-4" />
                </button>

                <ChevronLeft className="w-5 h-5 text-slate-400 group-hover:text-teal-700 transition-transform group-hover:-translate-x-1" />
              </div>
            </div>
          ))}
        </div>
      )}

    </div>
  );
}
