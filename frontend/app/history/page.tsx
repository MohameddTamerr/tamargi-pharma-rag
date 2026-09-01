"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  MessageSquare,
  Calendar,
  ChevronLeft,
  Trash2,
  Plus,
  Clock,
  ArrowRight
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { fetchUserConversations, deleteUserConversation, ConversationItem } from "@/lib/api";
import ProtectedRoute from "@/components/ProtectedRoute";
import Sidebar from "@/components/Sidebar";

export default function HistoryPage() {
  return (
    <ProtectedRoute>
      <div className="flex flex-1 overflow-hidden min-h-0 w-full h-full bg-[#f3f6fa] dark:bg-slate-950">
        <Sidebar activePath="/history" />
        <main className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto p-4 md:p-8">
          <HistoryContent />
        </main>
      </div>
    </ProtectedRoute>
  );
}

function HistoryContent() {
  const router = useRouter();
  const { user } = useAuth();
  const userId = user?.id || "";

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (userId) {
      loadConversations();
    }
  }, [userId]);

  const loadConversations = async () => {
    if (!userId) return;
    setIsLoading(true);
    try {
      const data = await fetchUserConversations(userId);
      setConversations(data || []);
    } catch (err) {
      console.warn("Failed to load conversations:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!window.confirm("هل أنت متأكد من رغبتك في حذف هذه المحادثة؟")) return;
    try {
      const ok = await deleteUserConversation(convId, userId);
      if (ok) {
        setConversations((prev) => prev.filter((c) => c.id !== convId));
      }
    } catch (err) {
      console.warn("Failed to delete conversation:", err);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div className="space-y-1">
          <h1 className="text-xl md:text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <MessageSquare className="w-6 h-6 text-teal-700 dark:text-teal-400" />
            <span>سجل المحادثات الطبية</span>
          </h1>
          <p className="text-xs md:text-sm text-slate-500 dark:text-slate-400">
            جميع استفساراتك وأدلة الأمان الموثقة السابقة
          </p>
        </div>

        <Link
          href="/chat"
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-2xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs md:text-sm shadow-md shadow-teal-700/20 transition-all shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>محادثة جديدة</span>
        </Link>
      </div>

      {/* Content */}
      {isLoading ? (
        <div className="py-16 text-center space-y-3">
          <div className="w-8 h-8 border-3 border-teal-700 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-sm font-medium text-slate-500">جارٍ تحميل سجل المحادثات...</p>
        </div>
      ) : conversations.length === 0 ? (
        <div className="py-16 px-6 text-center rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4 shadow-xs">
          <div className="w-16 h-16 rounded-2xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center mx-auto">
            <MessageSquare className="w-8 h-8" />
          </div>
          <div className="space-y-1 max-w-md mx-auto">
            <h3 className="font-bold text-slate-900 dark:text-slate-100 text-base">
              لا توجد محادثات سابقة مسجلة
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
              ابدأ بطرح أي سؤال طبي أو دوائي وسيتم حفظ المحادثة في سجلك الشخصي تلقائياً.
            </p>
          </div>
          <Link
            href="/chat"
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs shadow-md transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>بدء محادثة الآن</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {conversations.map((item) => (
            <div
              key={item.id}
              onClick={() => router.push(`/chat?conv=${item.id}`)}
              className="p-5 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-teal-400 dark:hover:border-teal-600 shadow-xs hover:shadow-md transition-all cursor-pointer flex items-center justify-between gap-4 group"
            >
              <div className="space-y-1.5 overflow-hidden">
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 group-hover:text-teal-700 dark:group-hover:text-teal-400 transition-colors truncate">
                  {item.title || "محادثة طبية"}
                </h3>
                <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-teal-600" />
                    <span>{new Date(item.created_at).toLocaleDateString("ar-EG")}</span>
                  </span>
                  <span>•</span>
                  <span>{new Date(item.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={(e) => handleDelete(item.id, e)}
                  className="p-2.5 rounded-xl text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-xl transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
                  title="حذف المحادثة"
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
