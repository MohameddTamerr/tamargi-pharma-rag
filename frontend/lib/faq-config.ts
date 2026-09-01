export interface SuggestedQuestion {
  id: string;
  category: string;
  question: string;
}

export const SUGGESTED_QUESTIONS: SuggestedQuestion[] = [
  {
    id: "faq-1",
    category: "إرشادات الاستخدام",
    question: "هل يمكن تناول الباراسيتامول على معدة فارغة؟"
  },
  {
    id: "faq-2",
    category: "الأمان والتحذيرات",
    question: "ما هي موانع استخدام دواء باراسيتامول؟"
  },
  {
    id: "faq-3",
    category: "التفاعلات الدوائية",
    question: "ما هي التداخلات الدوائية للوارفارين؟"
  },
  {
    id: "faq-4",
    category: "استخدام الأجهزة",
    question: "كيف أستخدم جهاز التربوهيلر بطريقة صحيحة؟"
  }
];
