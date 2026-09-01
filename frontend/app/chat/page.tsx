"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import Sidebar from "@/components/Sidebar";
import Chat from "@/components/chat/Chat";
import RightPanel from "@/components/RightPanel";

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <div className="flex flex-1 overflow-hidden min-h-0 w-full h-full bg-[#f3f6fa] dark:bg-slate-950">
        <Sidebar activePath="/chat" />
        <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
          <Chat />
        </main>
        <RightPanel />
      </div>
    </ProtectedRoute>
  );
}
