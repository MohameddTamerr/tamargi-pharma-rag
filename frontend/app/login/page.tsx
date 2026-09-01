"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Stethoscope, Lock, Mail, Eye, EyeOff, ShieldCheck, ArrowRight } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { signIn } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");

    if (!email.trim() || !password.trim()) {
      setErrorMessage("يرجى إدخال البريد الإلكتروني وكلمة المرور.");
      return;
    }

    setIsSubmitting(true);
    const { error } = await signIn(email, password);
    setIsSubmitting(false);

    if (error) {
      setErrorMessage(error.message || "فشل تسجيل الدخول. تحقق من صحة البيانات.");
    } else {
      router.push("/");
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center p-4 bg-[#f8fafc] dark:bg-slate-950 overflow-y-auto">
      <div className="w-full max-w-md p-6 md:p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
        
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-teal-700 text-white flex items-center justify-center mx-auto shadow-sm">
            <Stethoscope className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100">
            تسجيل الدخول إلى Tamargi.ai
          </h1>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            سجل دخولك للوصول إلى ملفك الطبي وخططك الدوائية ومحادثاتك المحفوظة
          </p>
        </div>

        {/* Error Alert Box */}
        {errorMessage && (
          <div className="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-900 text-rose-800 dark:text-rose-300 text-xs font-semibold text-center">
            {errorMessage}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* Email Field */}
          <div className="space-y-1.5">
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
              البريد الإلكتروني
            </label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="example@mail.com"
                className="w-full px-4 py-3 pr-10 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm outline-none focus:border-teal-600 focus:bg-white dark:focus:bg-slate-900 transition-all min-h-[44px]"
              />
              <Mail className="w-5 h-5 text-slate-400 absolute top-3 right-3" />
            </div>
          </div>

          {/* Password Field */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
                كلمة المرور
              </label>
              <Link
                href="/forgot-password"
                className="text-[11px] text-teal-700 dark:text-teal-400 font-bold hover:underline"
              >
                نسيت كلمة المرور؟
              </Link>
            </div>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-3 pr-10 pl-10 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm outline-none focus:border-teal-600 focus:bg-white dark:focus:bg-slate-900 transition-all min-h-[44px]"
              />
              <Lock className="w-5 h-5 text-slate-400 absolute top-3 right-3" />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="p-1 text-slate-400 hover:text-slate-600 absolute top-2.5 left-3 min-h-[30px] min-w-[30px] flex items-center justify-center"
                aria-label={showPassword ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {/* Submit Button (44px min touch target) */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 px-4 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-sm shadow-xs transition-colors min-h-[44px] flex items-center justify-center gap-2"
          >
            {isSubmitting ? "جاري تسجيل الدخول..." : "تسجيل الدخول"}
          </button>

        </form>

        {/* Footer Actions */}
        <div className="space-y-3 pt-2 text-center text-xs border-t border-slate-100 dark:border-slate-800">
          <p className="text-slate-600 dark:text-slate-400">
            ليس لديك حساب؟{" "}
            <Link href="/signup" className="text-teal-700 dark:text-teal-400 font-bold hover:underline">
              إنشاء حساب جديد
            </Link>
          </p>

          <Link
            href="/"
            className="inline-flex items-center gap-1 text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 font-medium pt-1"
          >
            <span>المتابعة كزائر</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Trust Seal */}
        <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-400 text-center">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>بياناتك محمية ومشفرة وفق أعلى معايير الخصوصية الطبية</span>
        </div>

      </div>
    </div>
  );
}
