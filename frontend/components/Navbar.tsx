"use client";

import Link from "next/link";
import { useState } from "react";
import {
  Menu,
  Stethoscope,
  FileText,
  User,
  Moon,
  Sun,
  ShieldCheck,
  Type
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export default function Navbar({ onToggleSidebar }: NavbarProps) {
  const { user, fontSize, setFontSize, toggleSidebar } = useAuth();
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark");
    }
  };

  const cycleFontSize = () => {
    if (fontSize === "normal") setFontSize("large");
    else if (fontSize === "large") setFontSize("extra-large");
    else setFontSize("normal");
  };

  const getFontSizeLabel = () => {
    if (fontSize === "large") return "خط كبير (A+)";
    if (fontSize === "extra-large") return "خط عريض (A++)";
    return "خط عادي (A)";
  };

  return (
    <header className="w-full h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 md:px-6 flex items-center justify-between flex-shrink-0 z-30 no-print">
      
      {/* Right side: Mobile Menu & Brand */}
      <div className="flex items-center gap-3">
        <button
          onClick={onToggleSidebar || toggleSidebar}
          className="md:hidden p-2 rounded-xl text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 min-h-[44px] min-w-[44px] flex items-center justify-center"
          aria-label="فتح القائمة الجانبية"
        >
          <Menu className="w-6 h-6" />
        </button>

        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-teal-700 text-white flex items-center justify-center shadow-xs">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <span className="font-extrabold text-base text-slate-900 dark:text-white block leading-tight">
              Tamargi.ai
            </span>
            <span className="text-[10px] text-teal-700 dark:text-teal-400 font-semibold block">
              الأدلة الدوائية المعتمدة
            </span>
          </div>
        </Link>

        <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300 text-[11px] font-bold mr-3">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
          <span>مطابق لأدلة هيئة الدواء المصرية</span>
        </div>
      </div>

      {/* Left side: Elderly Font Control & Shortcuts */}
      <div className="flex items-center gap-2">
        
        {/* Elderly Accessibility Font Size Toggle Button (44px min target) */}
        <button
          onClick={cycleFontSize}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-teal-50 dark:hover:bg-teal-950/60 text-slate-700 dark:text-slate-200 hover:text-teal-800 font-bold text-xs border border-slate-200 dark:border-slate-700 transition-colors min-h-[44px]"
          title="تغيير حجم الخط لكبار السن"
          aria-label="تغيير حجم الخط"
        >
          <Type className="w-4 h-4 text-teal-700 dark:text-teal-400" />
          <span>{getFontSizeLabel()}</span>
        </button>

        {/* Medication Plans Link */}
        <Link
          href="/plans"
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors min-h-[44px]"
          title="الخطط الدوائية"
        >
          <FileText className="w-4 h-4 text-slate-500" />
          <span>الخطط الدوائية</span>
        </Link>

        {/* Patient Profile Link */}
        <Link
          href="/profile"
          className="flex items-center gap-1.5 p-2 sm:px-3 rounded-xl bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-xs font-bold transition-colors min-h-[44px]"
          title="الملف الطبي"
        >
          <User className="w-4 h-4 text-slate-500" />
          <span className="hidden sm:inline">الملف الطبي</span>
        </Link>

        {/* Dark Mode Toggle */}
        <button
          onClick={toggleDarkMode}
          className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
          title="تبديل الوضع الليلي"
          aria-label="تبديل الوضع الليلي"
        >
          {isDarkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
        </button>

      </div>

    </header>
  );
}
