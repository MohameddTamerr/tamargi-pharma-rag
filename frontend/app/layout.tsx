import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { AuthProvider } from "@/lib/auth-context";

export const metadata: Metadata = {
  title: "Tamargi.ai — مساعدك الصحي والدوائي الموثوق",
  description: "Tamargi.ai — منصة مساعدة دوائية قائمة على الأدلة المعتمدة لهيئة الدواء المصرية وحسابات الأمان الشخصية للمرضى.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl" className="h-full overflow-hidden">
      <body className="h-dvh max-h-dvh overflow-hidden flex flex-col bg-[#f8fafc] text-slate-900 antialiased selection:bg-teal-100 selection:text-teal-900">
        <AuthProvider>
          <Navbar />
          <main className="flex-1 flex overflow-hidden min-h-0 w-full">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
