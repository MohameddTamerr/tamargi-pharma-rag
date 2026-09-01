"use client";

import { useState } from "react";
import ProtectedRoute from "@/components/ProtectedRoute";
import Sidebar from "@/components/Sidebar";
import Chat from "@/components/chat/Chat";
import RightPanel from "@/components/RightPanel";

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [selectedConvId, setSelectedConvId] = useState<string>("");

  return (
    <ProtectedRoute>
      <div className="flex flex-1 overflow-hidden min-h-0 w-full h-full bg-[#f3f6fa] dark:bg-slate-950">
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          currentConvId={selectedConvId}
          onSelectConversation={(id) => setSelectedConvId(id)}
        />
        <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
          <Chat conversationId={selectedConvId} />
        </main>
        <RightPanel />
      </div>
    </ProtectedRoute>
  );
}
