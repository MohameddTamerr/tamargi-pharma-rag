import type { Metadata } from "next";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { AuthProvider } from "@/lib/auth-context";
import { ThemeProvider } from "@/lib/theme-context";

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
    <html lang="ar" dir="rtl" className="h-full overflow-hidden" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('tamargi_theme');if(t==='dark'||(t==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches)){document.documentElement.classList.add('dark')}else{document.documentElement.classList.remove('dark')}}catch(e){}})()`,
          }}
        />
      </head>
      <body className="h-dvh max-h-dvh overflow-hidden flex flex-col bg-[#f8fafc] dark:bg-slate-950 text-slate-900 dark:text-slate-100 antialiased selection:bg-teal-100 selection:text-teal-900">
        <ThemeProvider>
          <AuthProvider>
            <Navbar />
            <main className="flex-1 flex overflow-hidden min-h-0 w-full">{children}</main>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
