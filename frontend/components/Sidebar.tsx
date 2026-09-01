"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import {
  MessageSquarePlus,
  MessageSquare,
  FileText,
  User,
  LogOut,
  Trash2,
  ShieldCheck,
  X,
  Stethoscope,
  ChevronLeft
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { fetchUserConversations, createUserConversation, deleteUserConversation, ConversationItem } from "@/lib/api";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  currentConvId?: string;
  activePath?: string;
  onSelectConversation?: (convId: string) => void;
}

export default function Sidebar({
  isOpen: propIsOpen,
  onClose: propOnClose,
  currentConvId,
  onSelectConversation,
}: SidebarProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, signOut, isSidebarOpen: authIsOpen, closeSidebar: authCloseSidebar } = useAuth();
  const isOpen = propIsOpen !== undefined ? propIsOpen : authIsOpen;
  const onClose = propOnClose || authCloseSidebar;
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [isLoadingConvs, setIsLoadingConvs] = useState(false);

  const userId = user?.id || "guest_user";

  useEffect(() => {
    loadConversations();
  }, [userId]);

  const loadConversations = async () => {
    setIsLoadingConvs(true);
    try {
      const data = await fetchUserConversations(userId);
      setConversations(data);
    } catch (e) {
      console.warn("Failed to load conversations:", e);
    } finally {
      setIsLoadingConvs(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const newConv = await createUserConversation(userId, "محادثة جديدة");
      if (newConv) {
        setConversations((prev) => [newConv, ...prev]);
        if (onSelectConversation) {
          onSelectConversation(newConv.id);
        } else {
          router.push(`/chat?conv=${newConv.id}`);
        }
      }
    } catch (e) {
      console.warn("New chat error:", e);
    }
    if (onClose) onClose();
  };

  const handleDeleteConv = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    e.preventDefault();
    if (!confirm("هل أنت متأكد من حذف هذه المحادثة؟")) return;

    await deleteUserConversation(convId, userId);
    setConversations((prev) => prev.filter((c) => c.id !== convId));
    if (currentConvId === convId) {
      if (onSelectConversation) onSelectConversation("");
      else router.push("/");
    }
  };

  // Group conversations by Today, Yesterday, Older
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  const convsToday: ConversationItem[] = [];
  const convsYesterday: ConversationItem[] = [];
  const convsOlder: ConversationItem[] = [];

  conversations.forEach((c) => {
    const cDate = new Date(c.updated_at || c.created_at).toDateString();
    if (cDate === today) convsToday.push(c);
    else if (cDate === yesterday) convsYesterday.push(c);
    else convsOlder.push(c);
  });

  const mainNav = [
    { name: "المحادثة الطبية", path: "/", icon: MessageSquare },
    { name: "الخطط الدوائية", path: "/plans", icon: FileText },
    { name: "الملف الصحي", path: "/profile", icon: User },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full bg-[#f8fafc] dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 text-slate-800 dark:text-slate-100">
      
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-teal-600 text-white flex items-center justify-center shadow-xs">
            <Stethoscope className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-base font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Tamargi.ai
            </h1>
            <span className="text-[11px] text-teal-700 dark:text-teal-400 font-medium block -mt-0.5">
              مساعدك الدوائي المعتمد
            </span>
          </div>
        </Link>

        {onClose && (
          <button
            onClick={onClose}
            className="md:hidden p-2 rounded-xl text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 min-h-[44px] min-w-[44px] flex items-center justify-center"
            aria-label="إغلاق القائمة"
          >
            <X className="w-5 h-5" />
          </button>
        )}
      </div>

      {/* New Chat Button (Minimum 44px touch target) */}
      <div className="p-3 border-b border-slate-200/80 dark:border-slate-800">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-sm shadow-xs transition-colors min-h-[44px]"
        >
          <MessageSquarePlus className="w-5 h-5" />
          <span>محادثة جديدة</span>
        </button>
      </div>

      {/* Scrollable Conversations History */}
      <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-4 text-xs scrollbar-thin">
        {conversations.length === 0 && !isLoadingConvs && (
          <div className="text-center py-6 text-slate-400">
            <p>لا توجد محادثات سابقة</p>
            <p className="text-[10px] text-slate-400 mt-1">ابدأ محادثة جديدة الآن</p>
          </div>
        )}

        {convsToday.length > 0 && (
          <div className="space-y-1">
            <span className="px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider block">اليوم</span>
            {convsToday.map((c) => (
              <ConversationRow
                key={c.id}
                item={c}
                isActive={currentConvId === c.id}
                onSelect={() => {
                  if (onSelectConversation) onSelectConversation(c.id);
                  else router.push(`/?conv=${c.id}`);
                  if (onClose) onClose();
                }}
                onDelete={(e) => handleDeleteConv(e, c.id)}
              />
            ))}
          </div>
        )}

        {convsYesterday.length > 0 && (
          <div className="space-y-1">
            <span className="px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider block">أمس</span>
            {convsYesterday.map((c) => (
              <ConversationRow
                key={c.id}
                item={c}
                isActive={currentConvId === c.id}
                onSelect={() => {
                  if (onSelectConversation) onSelectConversation(c.id);
                  else router.push(`/?conv=${c.id}`);
                  if (onClose) onClose();
                }}
                onDelete={(e) => handleDeleteConv(e, c.id)}
              />
            ))}
          </div>
        )}

        {convsOlder.length > 0 && (
          <div className="space-y-1">
            <span className="px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider block">المحادثات السابقة</span>
            {convsOlder.map((c) => (
              <ConversationRow
                key={c.id}
                item={c}
                isActive={currentConvId === c.id}
                onSelect={() => {
                  if (onSelectConversation) onSelectConversation(c.id);
                  else router.push(`/?conv=${c.id}`);
                  if (onClose) onClose();
                }}
                onDelete={(e) => handleDeleteConv(e, c.id)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Main Section Navigation */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 space-y-1">
        {mainNav.map((nav, idx) => {
          const Icon = nav.icon;
          const isActive = pathname === nav.path;
          return (
            <Link
              key={idx}
              href={nav.path}
              onClick={onClose}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-bold transition-all min-h-[44px] ${
                isActive
                  ? "bg-teal-50 dark:bg-teal-950 text-teal-800 dark:text-teal-300 border border-teal-200 dark:border-teal-800"
                  : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              <div className="flex items-center gap-2.5">
                <Icon className={`w-4 h-4 ${isActive ? "text-teal-700 dark:text-teal-400" : "text-slate-500"}`} />
                <span>{nav.name}</span>
              </div>
              <ChevronLeft className="w-3.5 h-3.5 text-slate-400" />
            </Link>
          );
        })}
      </div>

      {/* User Info & Sign Out Footer */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60">
        <div className="flex items-center justify-between">
          <div className="truncate max-w-[130px]">
            <span className="block text-xs font-bold text-slate-900 dark:text-slate-100 truncate">
              {user?.email ? user.email.split("@")[0] : "زائر"}
            </span>
            <span className="block text-[10px] text-slate-500 truncate">
              {user?.email || "غير مسجل"}
            </span>
          </div>

          {user ? (
            <button
              onClick={signOut}
              className="p-2 rounded-xl text-slate-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
              title="تسجيل الخروج"
              aria-label="تسجيل الخروج"
            >
              <LogOut className="w-4 h-4" />
            </button>
          ) : (
            <Link
              href="/login"
              className="px-2.5 py-1.5 rounded-lg bg-teal-50 dark:bg-teal-900/40 text-teal-700 dark:text-teal-300 text-xs font-bold hover:bg-teal-100 min-h-[44px] flex items-center"
            >
              تسجيل الدخول
            </Link>
          )}
        </div>
      </div>

    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside className="w-[260px] hidden md:block flex-shrink-0 h-full overflow-hidden no-print">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex no-print">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={onClose}
          />
          <div className="relative w-[280px] max-w-[85vw] h-full z-50 shadow-xl">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}

function ConversationRow({
  item,
  isActive,
  onSelect,
  onDelete,
}: {
  item: ConversationItem;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
}) {
  return (
    <div
      onClick={onSelect}
      className={`group flex items-center justify-between px-3 py-2 rounded-xl cursor-pointer transition-all min-h-[44px] ${
        isActive
          ? "bg-teal-50 dark:bg-teal-950/60 text-teal-900 dark:text-teal-200 font-bold border border-teal-200 dark:border-teal-800/80"
          : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800/60"
      }`}
    >
      <div className="flex items-center gap-2 truncate max-w-[170px]">
        <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? "text-teal-700 dark:text-teal-400" : "text-slate-400"}`} />
        <span className="truncate">{item.title || "محادثة"}</span>
      </div>
      <button
        onClick={onDelete}
        className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-slate-200 dark:hover:bg-slate-700 transition-opacity"
        title="حذف المحادثة"
      >
        <Trash2 className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}
