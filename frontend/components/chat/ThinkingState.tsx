"use client";

import { useEffect, useState } from "react";
import { Search, Database, ShieldCheck, Cpu, Sparkles } from "lucide-react";

interface ThinkingStateProps {
  query?: string;
}

export default function ThinkingState({ query }: ThinkingStateProps) {
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    { label: "جاري فهم واستخلاص المفاهيم الطبية...", sub: "Understanding medical concepts...", icon: Cpu },
    { label: "جاري البحث في 13 مجلد من أدلة الدواء المصرية...", sub: "Searching E5 Dense + BM25 Sparse index...", icon: Search },
    { label: "جاري تحليل الأدلة بواسطة RRF و CrossEncoder...", sub: "Reranking evidence candidates...", icon: Database },
    { label: "جاري صياغة الإجابة الموثقة بالأدلة...", sub: "Preparing grounded answer with strict verification...", icon: ShieldCheck },
  ];

  useEffect(() => {
    const timer1 = setTimeout(() => setCurrentStep(1), 600);
    const timer2 = setTimeout(() => setCurrentStep(2), 1400);
    const timer3 = setTimeout(() => setCurrentStep(3), 2200);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  return (
    <div className="p-4 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 space-y-3 animate-fade-in my-4 shadow-xs">
      <div className="flex items-center gap-2 text-xs font-bold text-blue-600 dark:text-blue-400">
        <Sparkles className="w-4 h-4 animate-spin text-blue-500" />
        <span>Tamargi.ai — نظام البحث والتوليد الموثق بالأدلة</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {steps.map((step, idx) => {
          const Icon = step.icon;
          const isActive = idx === currentStep;
          const isDone = idx < currentStep;

          return (
            <div
              key={idx}
              className={`p-3 rounded-2xl border transition-all flex items-center gap-3 ${
                isActive
                  ? "bg-blue-50/80 dark:bg-blue-950/40 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-bold shadow-xs"
                  : isDone
                  ? "bg-slate-50 dark:bg-slate-800/60 border-slate-200/60 dark:border-slate-800 text-slate-500"
                  : "bg-slate-50/40 dark:bg-slate-900 border-slate-100 dark:border-slate-800 text-slate-400 opacity-60"
              }`}
            >
              <div
                className={`w-7 h-7 rounded-xl flex items-center justify-center text-xs font-bold ${
                  isActive
                    ? "bg-blue-600 text-white animate-pulse"
                    : isDone
                    ? "bg-slate-200 dark:bg-slate-700 text-blue-600 dark:text-blue-400"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-400"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
              </div>
              <div className="overflow-hidden">
                <p className="text-xs truncate">{step.label}</p>
                <p className="text-[10px] text-slate-400 font-mono truncate">{step.sub}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
