"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { useRouter, usePathname } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { Sidebar } from "@/components/layout/Sidebar";
import { Footer } from "@/components/layout/Footer";
import { Menu } from "lucide-react";
import { useApiClient } from "@/lib/api";
import { Contract } from "@/types/api";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoaded, isSignedIn } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Use mock data for the layout to prevent API fetch errors
  const mockRecentContracts = [
    { id: "1", file_name: "Acme_Corp_NDA_2026.pdf", overall_risk_score: 15 },
    { id: "2", file_name: "Senior_Dev_Employment.docx", overall_risk_score: 78 },
    { id: "3", file_name: "SaaS_Subscription_MSA.pdf", overall_risk_score: 45 },
  ];

  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-zinc-200 border-t-zinc-900" />
      </div>
    );
  }

  if (!isSignedIn) {
    router.push("/sign-in");
    return null;
  }

  const isScanPage = pathname?.startsWith("/scan/");

  return (
    <div className="h-screen flex overflow-hidden bg-[#030303] text-zinc-100 font-sans selection:bg-blue-500/30">
      {/* Sidebar on the left, full height */}
      {!isScanPage && (
        <Sidebar 
          isOpen={sidebarOpen} 
          onClose={() => setSidebarOpen(false)}
          recentContracts={mockRecentContracts}
        />
      )}

      {/* Main content area on the right */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        <div className="absolute top-0 left-0 right-0 h-[500px] bg-blue-500/10 blur-[120px] pointer-events-none" />
        
        <Navbar 
          onMenuClick={() => setSidebarOpen(!sidebarOpen)}
          sidebarOpen={sidebarOpen}
          hideLogo={!isScanPage}
        />
        
        <main className="flex-1 overflow-y-auto flex flex-col relative z-10">
          <div className={`flex-1 ${isScanPage ? 'p-2 md:p-4' : 'p-4 md:p-8'}`}>
            {children}
          </div>
          {!isScanPage && <Footer />}
        </main>
      </div>
    </div>
  );
}