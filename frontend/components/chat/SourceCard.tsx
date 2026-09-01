"use client";

import { useState } from "react";
import { FileText, ChevronDown, ChevronUp } from "lucide-react";
import { SourceItem } from "@/lib/api";

interface SourceCardProps {
  source: SourceItem;
}

export default function SourceCard({ source }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-2xl bg-slate-50 dark:bg-slate-800/80 border border-slate-200/80 dark:border-slate-700/80 hover:border-emerald-500/40 transition-all p-3 shadow-xs">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 overflow-hidden">
          <span className="px-2 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 font-mono text-xs font-bold border border-emerald-200 dark:border-emerald-800">
            [{source.evidenceId}]
          </span>
          <div className="overflow-hidden">
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate flex items-center gap-1.5" title={source.fileName}>
              <FileText className="w-3.5 h-3.5 text-teal-600 dark:text-teal-400 shrink-0" />
              {source.fileName}
            </h4>
            <span className="text-[11px] text-slate-500 dark:text-slate-400 block font-mono">
              الصفحة {source.pageNumber}
            </span>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 px-2.5 py-1 rounded-xl text-xs font-bold text-emerald-700 dark:text-emerald-300 bg-white dark:bg-slate-900 border border-emerald-200 dark:border-emerald-800 hover:bg-emerald-50 dark:hover:bg-slate-800 transition-colors shrink-0"
        >
          <span>{expanded ? "إخفاء الدليل" : "عرض الدليل"}</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      {expanded && (
        <div className="mt-2.5 pt-2.5 border-t border-slate-200/60 dark:border-slate-700/60 space-y-2">
          <div className="p-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800 text-xs font-mono text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
            {source.excerpt}
          </div>
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
            <span>رتبة البحث: #{source.rank}</span>
            {source.score !== undefined && (
              <span>درجة التوافق: {source.score.toFixed(3)}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
