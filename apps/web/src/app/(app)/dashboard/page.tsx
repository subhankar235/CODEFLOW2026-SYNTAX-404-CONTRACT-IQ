"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { 
  FileText, Upload, AlertCircle, ShieldCheck, 
  Activity, ArrowRight, Loader2, Sparkles
} from "lucide-react";
import { motion } from "framer-motion";
import { useApiClient } from "@/lib/api";
import { DashboardContract } from "@/types/analysis";
import { ContractCard } from "@/features/dashboard/ContractCard";

export default function DashboardPage() {
  const { getDashboard } = useApiClient();
  const [data, setData] = useState<{
    contracts: DashboardContract[];
    power_trend: { average_power_score: number; trend_description: string } | null;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const result = await getDashboard();
        setData(result);
      } catch (err) {
        console.error("Dashboard failed to load", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [getDashboard]);

  const highRiskCount = data?.contracts.filter(c => c.overall_risk_score > 60).length || 0;
  const activeCount = data?.contracts.length || 0;

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 space-y-10 relative">
      {/* Background glow */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-blue-600/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Hero Strip */}
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative rounded-3xl p-10 border border-white/5 bg-gradient-to-br from-zinc-900 to-zinc-950 overflow-hidden flex flex-col md:flex-row justify-between items-center gap-8"
      >
        <div className="absolute top-0 right-0 p-8 opacity-10">
          <Sparkles className="h-32 w-32 text-blue-500" />
        </div>
        
        <div className="relative z-10 space-y-3">
          <h1 className="text-4xl font-extrabold tracking-tight text-white">Your Workspace</h1>
          <p className="text-zinc-400 text-lg max-w-xl">
            {activeCount > 0 
              ? `You've analyzed ${activeCount} contracts. ${highRiskCount > 0 ? `We've flagged ${highRiskCount} as high-risk.` : 'All currently processed documents look stable.'}`
              : "Welcome to LegalTech AI. Start by uploading your first contract for a deep-dive integrity analysis."}
          </p>
        </div>
        
        <Link
          href="/upload"
          className="relative z-10 flex items-center gap-3 px-8 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-500 transition-all shadow-xl shadow-blue-900/20 whitespace-nowrap group"
        >
          <Upload className="h-5 w-5 group-hover:-translate-y-0.5 transition-transform" /> 
          Analyze New Contract
        </Link>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="Critical Flags" 
          value={highRiskCount} 
          icon={<AlertCircle className="h-5 w-5 text-red-500" />}
          desc="Requires review"
          color="red"
          delay={0.1}
        />
        <StatCard 
          title="Active Scans" 
          value={activeCount} 
          icon={<FileText className="h-5 w-5 text-blue-500" />}
          desc="Managed contracts"
          color="blue"
          delay={0.2}
        />
        <StatCard 
          title="Power Trend" 
          value={data?.power_trend?.average_power_score || 0} 
          icon={<Activity className="h-5 w-5 text-purple-500" />}
          desc={data?.power_trend?.trend_description || "Balanced leverage"}
          color="purple"
          delay={0.3}
        />
      </div>

      {/* Contracts Section */}
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <ClockIcon className="h-5 w-5 text-zinc-500" />
            Recent Analysis
          </h2>
          <Link href="/history" className="text-sm font-semibold text-zinc-500 hover:text-white transition-colors flex items-center gap-1">
            Browse all <ArrowRight className="h-4 w-4" />
          </Link>
        </div>

        {activeCount > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {data?.contracts.map((contract, i) => (
              <ContractCard key={contract.id} contract={contract} index={i} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 border border-dashed border-white/10 rounded-3xl bg-white/[0.01]">
             <FileText className="h-12 w-12 text-zinc-700 mb-4" />
             <p className="text-zinc-500 font-medium">No contracts analyzed yet.</p>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, desc, color, delay }: any) {
  const colors: any = {
    red: "bg-red-500/10 text-red-500 border-red-500/10",
    blue: "bg-blue-500/10 text-blue-500 border-blue-500/10",
    purple: "bg-purple-500/10 text-purple-500 border-purple-500/10",
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="p-8 rounded-3xl border border-white/5 bg-zinc-900/50 backdrop-blur-sm space-y-4"
    >
      <div className="flex items-center justify-between">
        <span className="text-sm font-bold uppercase tracking-widest text-zinc-500">{title}</span>
        <div className={`p-2 rounded-xl ${colors[color]}`}>
          {icon}
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-5xl font-black text-white">{value}</span>
      </div>
      <p className="text-sm font-medium text-zinc-400">{desc}</p>
    </motion.div>
  );
}

function ClockIcon(props: any) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}