"use client";

import React, { useState, useEffect } from "react";
import {
  User,
  HeartPulse,
  AlertTriangle,
  Pill,
  History,
  Plus,
  Trash2,
  CheckCircle2,
  Clock,
  Save,
  Scale,
  Stethoscope,
  ShieldCheck,
  Info,
  Key,
  Lock,
  ExternalLink,
  Eye,
  EyeOff
} from "lucide-react";
import {
  fetchPatientProfile,
  updatePatientProfile,
  addPatientCondition,
  deletePatientCondition,
  addPatientAllergy,
  deletePatientAllergy,
  addPatientMedication,
  deletePatientMedication,
  addPatientHistory,
  deletePatientHistory,
  PatientProfileData,
  fetchUserGeminiKeyStatus,
  saveUserGeminiKey,
  deleteUserGeminiKey,
  UserKeyStatus
} from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import ProtectedRoute from "@/components/ProtectedRoute";
import Sidebar from "@/components/Sidebar";

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <div className="flex flex-1 overflow-hidden min-h-0 w-full h-full bg-[#f3f6fa] dark:bg-slate-950">
        <Sidebar activePath="/profile" />
        <main className="flex-1 flex flex-col min-w-0 h-full overflow-y-auto">
          <ProfileContent />
        </main>
      </div>
    </ProtectedRoute>
  );
}

function ProfileContent() {
  const { user } = useAuth();
  const userId = user?.id || "";

  const [profile, setProfile] = useState<PatientProfileData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // New item inputs
  const [newCondition, setNewCondition] = useState("");
  const [newAllergen, setNewAllergen] = useState("");
  const [newMedication, setNewMedication] = useState("");
  const [newMedStrength, setNewMedStrength] = useState("");
  const [newHistoryType, setNewHistoryType] = useState("surgery");
  const [newHistoryVal, setNewHistoryVal] = useState("");

  // Demographics form
  const [dob, setDob] = useState("");
  const [sex, setSex] = useState("male");
  const [pregnancy, setPregnancy] = useState("none");
  const [breastfeeding, setBreastfeeding] = useState("none");
  const [weight, setWeight] = useState("");
  const [height, setHeight] = useState("");

  // BYOK Gemini API Key state
  const [keyStatus, setKeyStatus] = useState<UserKeyStatus | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [showApiKey, setShowApiKey] = useState(false);
  const [savingKey, setSavingKey] = useState(false);
  const [keySuccessMsg, setKeySuccessMsg] = useState("");
  const [keyErrorMsg, setKeyErrorMsg] = useState("");

  const loadKeyStatus = async () => {
    if (!userId) return;
    const status = await fetchUserGeminiKeyStatus();
    setKeyStatus(status);
  };

  const loadData = async () => {
    if (!userId) return;
    setLoading(true);
    const data = await fetchPatientProfile(userId);
    if (data) {
      setProfile(data);
      setDob(data.date_of_birth || "");
      setSex(data.sex || "male");
      setPregnancy(data.pregnancy_status || "none");
      setBreastfeeding(data.breastfeeding_status || "none");
      setWeight(data.weight_kg ? String(data.weight_kg) : "");
      setHeight(data.height_cm ? String(data.height_cm) : "");
      window.dispatchEvent(new Event("patient_profile_updated"));
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
    loadKeyStatus();
  }, [userId]);

  const handleSaveKey = async (e: React.FormEvent) => {
    e.preventDefault();
    setKeyErrorMsg("");
    setKeySuccessMsg("");

    if (!apiKeyInput.trim()) {
      setKeyErrorMsg("يرجى إدخال مفتاح Gemini API صالح.");
      return;
    }

    setSavingKey(true);
    const res = await saveUserGeminiKey(apiKeyInput.trim());
    setSavingKey(false);

    if (res.success) {
      setKeySuccessMsg("تم التحقق من مفتاح Gemini API وتشفيره وحفظه بنجاح!");
      setApiKeyInput("");
      loadKeyStatus();
      setTimeout(() => setKeySuccessMsg(""), 4000);
    } else {
      setKeyErrorMsg(res.error || "فشل التحقق من المفتاح. يرجى التأكد من نسخه بشكل صحيح.");
    }
  };

  const handleDeleteKey = async () => {
    if (!confirm("هل أنت متأكد من رغبتك في حذف مفتاح Gemini API الخاص بك؟")) return;
    setSavingKey(true);
    const ok = await deleteUserGeminiKey();
    setSavingKey(false);
    if (ok) {
      setKeySuccessMsg("تم حذف مفتاح Gemini API بنجاح.");
      loadKeyStatus();
      setTimeout(() => setKeySuccessMsg(""), 4000);
    } else {
      setKeyErrorMsg("فشل حذف المفتاح.");
    }
  };

  const handleSaveDemographics = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = await updatePatientProfile({
      user_id: userId,
      date_of_birth: dob || undefined,
      sex,
      pregnancy_status: pregnancy,
      breastfeeding_status: breastfeeding,
      weight_kg: weight ? parseFloat(weight) : undefined,
      height_cm: height ? parseFloat(height) : undefined,
    });
    if (ok) {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
      loadData();
    }
  };

  const handleAddCondition = async () => {
    if (!newCondition.trim()) return;
    await addPatientCondition(userId, newCondition.trim());
    setNewCondition("");
    loadData();
  };

  const handleDeleteCondition = async (id?: string) => {
    if (!id) return;
    await deletePatientCondition(id, userId);
    loadData();
  };

  const handleAddAllergy = async () => {
    if (!newAllergen.trim()) return;
    await addPatientAllergy(userId, newAllergen.trim());
    setNewAllergen("");
    loadData();
  };

  const handleDeleteAllergy = async (id?: string) => {
    if (!id) return;
    await deletePatientAllergy(id, userId);
    loadData();
  };

  const handleAddMed = async () => {
    if (!newMedication.trim()) return;
    await addPatientMedication(userId, newMedication.trim(), newMedStrength.trim() || undefined);
    setNewMedication("");
    setNewMedStrength("");
    loadData();
  };

  const handleDeleteMed = async (id?: string) => {
    if (!id) return;
    await deletePatientMedication(id, userId);
    loadData();
  };

  const handleAddHist = async () => {
    if (!newHistoryVal.trim()) return;
    await addPatientHistory(userId, newHistoryType, newHistoryVal.trim());
    setNewHistoryVal("");
    loadData();
  };

  const handleDeleteHist = async (id?: string) => {
    if (!id) return;
    await deletePatientHistory(id, userId);
    loadData();
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#f8fafc] dark:bg-slate-950 overflow-y-auto p-4 md:p-8">
      <div className="max-w-4xl mx-auto w-full space-y-6">
        
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2.5">
              <User className="w-7 h-7 text-teal-700 dark:text-teal-400" />
              <span>الملف الطبي والصحي للمريض</span>
            </h1>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
              تُستخدم هذه البيانات حصرياً لفحص أمان الأدوية والتأكد من عدم وجود تعارضات أو موانع استخدام
            </p>
          </div>

          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900 text-xs font-bold">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>محمي بخصوصية تامة</span>
          </div>
        </div>

        {/* Save Success Alert */}
        {saveSuccess && (
          <div className="p-3.5 rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900 text-xs font-bold flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>تم حفظ التعديلات في ملفك الطبي بنجاح!</span>
          </div>
        )}

        {/* BYOK: Gemini API Key Settings Card */}
        <div id="byok-key" className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-teal-200 dark:border-teal-800/60 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-teal-50 dark:bg-teal-950 text-teal-700 dark:text-teal-400 flex items-center justify-center">
                <Key className="w-4 h-4" />
              </div>
              <div>
                <h3 className="text-sm font-extrabold text-slate-900 dark:text-slate-100">
                  مفتاح الذكاء الاصطناعي (Gemini API Key - BYOK)
                </h3>
                <span className="text-[11px] text-slate-500 dark:text-slate-400 block">
                  استخدم مفتاحك الخاص من Google لتشغيل الإجابات السريرية المخصصة دون قيود
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {keyStatus?.has_key ? (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/80 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 text-[11px] font-bold">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>مفعل ({keyStatus.key_hint})</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-amber-50 dark:bg-amber-950/80 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800 text-[11px] font-bold">
                  <Lock className="w-3.5 h-3.5 text-amber-600" />
                  <span>غير مهيأ (مطلوب للذكاء الاصطناعي)</span>
                </span>
              )}
            </div>
          </div>

          {/* Alerts */}
          {keySuccessMsg && (
            <div className="p-3 rounded-2xl bg-emerald-50 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900 text-xs font-bold flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>{keySuccessMsg}</span>
            </div>
          )}

          {keyErrorMsg && (
            <div className="p-3 rounded-2xl bg-rose-50 dark:bg-rose-950 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-900 text-xs font-bold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{keyErrorMsg}</span>
            </div>
          )}

          <form onSubmit={handleSaveKey} className="space-y-3 text-xs">
            <div className="space-y-1.5">
              <label className="font-bold text-slate-700 dark:text-slate-300 flex items-center justify-between">
                <span>{keyStatus?.has_key ? "تحديث أو استبدال المفتاح:" : "أدخل مفتاح Gemini API:"}</span>
                <a
                  href="https://aistudio.google.com/app/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-teal-700 dark:text-teal-400 hover:underline flex items-center gap-1 text-[11px] font-medium"
                >
                  <span>احصل على مفتاح مجاني من Google AI Studio</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </label>

              <div className="relative">
                <input
                  type={showApiKey ? "text" : "password"}
                  value={apiKeyInput}
                  onChange={(e) => setApiKeyInput(e.target.value)}
                  placeholder={keyStatus?.has_key ? "أدخل مفتاحاً جديداً لاستبدال الحالي..." : "AIzaSy..."}
                  className="w-full pl-10 pr-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm font-mono min-h-[44px]"
                  autoComplete="off"
                  spellCheck={false}
                />
                <button
                  type="button"
                  onClick={() => setShowApiKey(!showApiKey)}
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                  tabIndex={-1}
                >
                  {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                🔒 يتم تشفير المفتاح فوراً باستخدام مفتاح تشفير عسكري على الخادم (AES/Fernet) ولا يتم حفظه بصيغة نصية مجردة إطلاقاً.
              </p>
            </div>

            <div className="flex items-center gap-3 pt-1">
              <button
                type="submit"
                disabled={savingKey || !apiKeyInput.trim()}
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 disabled:bg-slate-300 dark:disabled:bg-slate-800 text-white font-bold text-xs shadow-xs min-h-[44px] transition-colors"
              >
                <Save className="w-4 h-4" />
                <span>{savingKey ? "جاري التحقق والحفظ..." : "حفظ وتفعيل المفتاح"}</span>
              </button>

              {keyStatus?.has_key && (
                <button
                  type="button"
                  onClick={handleDeleteKey}
                  disabled={savingKey}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 dark:hover:bg-rose-900/60 text-rose-700 dark:text-rose-300 font-bold text-xs border border-rose-200 dark:border-rose-900 min-h-[44px] transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>حذف المفتاح</span>
                </button>
              )}
            </div>
          </form>
        </div>

        {/* Section 1: Demographics */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-slate-100 border-b border-slate-100 dark:border-slate-800 pb-3">
            <Scale className="w-5 h-5 text-teal-700 dark:text-teal-400" />
            <span>البيانات الشخصية والفسيولوجية</span>
          </div>

          <form onSubmit={handleSaveDemographics} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1.5">
                <label className="font-bold text-slate-700 dark:text-slate-300">تاريخ الميلاد</label>
                <input
                  type="date"
                  value={dob}
                  onChange={(e) => setDob(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-slate-700 dark:text-slate-300">النوع</label>
                <select
                  value={sex}
                  onChange={(e) => setSex(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
                >
                  <option value="male">ذكر</option>
                  <option value="female">أنثى</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-slate-700 dark:text-slate-300">الوزن (كجم)</label>
                <input
                  type="number"
                  step="0.5"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  placeholder="مثال: 75"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
                />
              </div>

              <div className="space-y-1.5">
                <label className="font-bold text-slate-700 dark:text-slate-300">الطول (سم)</label>
                <input
                  type="number"
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  placeholder="مثال: 170"
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
                />
              </div>
            </div>

            {sex === "female" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100 dark:border-slate-800">
                <div className="space-y-1.5">
                  <label className="font-bold text-slate-700 dark:text-slate-300">حالة الحمل</label>
                  <select
                    value={pregnancy}
                    onChange={(e) => setPregnancy(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
                  >
                    <option value="none">غير حامل</option>
                    <option value="first_trimester">الثلث الأول</option>
                    <option value="second_trimester">الثلث الثاني</option>
                    <option value="third_trimester">الثلث الثالث</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="font-bold text-slate-700 dark:text-slate-300">حالة الرضاعة</label>
                  <select
                    value={breastfeeding}
                    onChange={(e) => setBreastfeeding(e.target.value)}
                    className="w-full px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
                  >
                    <option value="none">لا توجد رضاعة طبيعية</option>
                    <option value="exclusive">رضاعة طبيعية حصرية</option>
                    <option value="partial">رضاعة جزئية</option>
                  </select>
                </div>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs shadow-xs min-h-[44px]"
              >
                <Save className="w-4 h-4" />
                <span>حفظ البيانات الشخصية</span>
              </button>
            </div>
          </form>
        </div>

        {/* Section 2: Chronic Conditions */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-slate-100">
              <HeartPulse className="w-5 h-5 text-teal-700 dark:text-teal-400" />
              <span>الأمراض المزمنة والحالات الصحية (Conditions)</span>
            </div>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={newCondition}
              onChange={(e) => setNewCondition(e.target.value)}
              placeholder="أضف مرض مزمن (مثل: ضغط الدم، السكري، الربو)..."
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
            />
            <button
              onClick={handleAddCondition}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs min-h-[44px]"
            >
              <Plus className="w-4 h-4" />
              <span>إضافة</span>
            </button>
          </div>

          <div className="space-y-2">
            {profile?.conditions && profile.conditions.length > 0 ? (
              profile.conditions.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">{c.condition_name}</span>
                    {c.confirmed ? (
                      <span className="px-2 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 font-bold text-[10px] flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>مؤكد سريرياً</span>
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-md bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-300 font-bold text-[10px] flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>بانتظار تأكيد المحادثة</span>
                      </span>
                    )}
                  </div>

                  <button
                    onClick={() => handleDeleteCondition(c.id)}
                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg min-h-[36px] min-w-[36px] flex items-center justify-center"
                    title="حذف"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 py-2">لا توجد أمراض مزمنة مسجلة</p>
            )}
          </div>
        </div>

        {/* Section 3: Allergies */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-slate-100">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              <span>الحساسية الدوائية والغذائية (Allergies)</span>
            </div>
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={newAllergen}
              onChange={(e) => setNewAllergen(e.target.value)}
              placeholder="أضف مادة تسبب حساسية (مثل: البنسلين، السلفا)..."
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
            />
            <button
              onClick={handleAddAllergy}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs min-h-[44px]"
            >
              <Plus className="w-4 h-4" />
              <span>إضافة</span>
            </button>
          </div>

          <div className="space-y-2">
            {profile?.allergies && profile.allergies.length > 0 ? (
              profile.allergies.map((a) => (
                <div
                  key={a.id}
                  className="flex items-center justify-between p-3.5 rounded-xl bg-rose-50/60 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-900/60 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="font-bold text-rose-900 dark:text-rose-200 text-sm">{a.allergen}</span>
                    {a.confirmed && (
                      <span className="px-2 py-0.5 rounded-md bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 font-bold text-[10px]">
                        مؤكد
                      </span>
                    )}
                  </div>

                  <button
                    onClick={() => handleDeleteAllergy(a.id)}
                    className="p-1.5 text-rose-400 hover:text-red-600 hover:bg-rose-100 dark:hover:bg-rose-900/40 rounded-lg min-h-[36px] min-w-[36px] flex items-center justify-center"
                    title="حذف"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 py-2">لا توجد حساسية مسجلة</p>
            )}
          </div>
        </div>

        {/* Section 4: Current Medications */}
        <div className="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
            <div className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-slate-100">
              <Pill className="w-5 h-5 text-teal-700 dark:text-teal-400" />
              <span>الأدوية الحالية المنتظمة (Current Medications)</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input
              type="text"
              value={newMedication}
              onChange={(e) => setNewMedication(e.target.value)}
              placeholder="اسم الدواء (مثل: وارفارين، كونكور)..."
              className="sm:col-span-2 px-4 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
            />
            <div className="flex gap-2">
              <input
                type="text"
                value={newMedStrength}
                onChange={(e) => setNewMedStrength(e.target.value)}
                placeholder="الجرعة (اختياري)"
                className="flex-1 px-3 py-2.5 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 text-sm min-h-[44px]"
              />
              <button
                onClick={handleAddMed}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-teal-700 hover:bg-teal-800 text-white font-bold text-xs min-h-[44px]"
              >
                <Plus className="w-4 h-4" />
                <span>إضافة</span>
              </button>
            </div>
          </div>

          <div className="space-y-2">
            {profile?.medications && profile.medications.length > 0 ? (
              profile.medications.map((m: any) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span className="font-bold text-slate-900 dark:text-slate-100 text-sm">{m.generic_name || m.medication_name}</span>
                    {m.strength && (
                      <span className="text-slate-500 text-xs">({m.strength})</span>
                    )}
                  </div>

                  <button
                    onClick={() => handleDeleteMed(m.id)}
                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/40 rounded-lg min-h-[36px] min-w-[36px] flex items-center justify-center"
                    title="حذف"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))
            ) : (
              <p className="text-xs text-slate-400 py-2">لا توجد أدوية حالية مسجلة</p>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
