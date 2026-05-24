import Link from "next/link";
import { usePathname } from "next/navigation";
import { FileText, X, LayoutDashboard, Upload, History, Settings } from "lucide-react";
import { motion } from "framer-motion";
import { Logo } from "@/components/logo";

interface SidebarContract {
  id: string;
  file_name: string;
  overall_risk_score: number;
}

interface SidebarProps {
  recentContracts?: SidebarContract[];
  isOpen?: boolean;
  onClose?: () => void;
}

function RiskBadge({ score }: { score: number }) {
  const getColor = () => {
    if (score <= 30) return "bg-green-500/20 text-green-400 border-green-500/30";
    if (score <= 60) return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
    return "bg-red-500/20 text-red-400 border-red-500/30";
  };

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${getColor()}`}>
      {score}
    </span>
  );
}

export function Sidebar({ recentContracts = [], isOpen = true, onClose }: SidebarProps) {
  const pathname = usePathname();
  const isScanPage = pathname?.startsWith("/scan/");

  if (isScanPage) return null;

  const navLinks = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Upload & Scan", href: "/upload", icon: Upload },
    { name: "History", href: "/history", icon: History },
    { name: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed left-0 top-0 z-40 h-screen w-64 transform bg-[#0a0a0a] border-r border-white/10 overflow-y-auto
          transition-transform duration-300 ease-in-out shadow-2xl
          ${isOpen ? "translate-x-0" : "-translate-x-full"}
          md:relative md:translate-x-0
        `}
      >
        <div className="flex items-center justify-between p-4 border-b border-white/10 md:hidden">
          <Link href="/" className="flex items-center gap-2 group">
            <Logo className="w-8 h-8 transition-transform group-hover:scale-105" />
            <span className="text-xl font-semibold tracking-tight text-white">
              ContractIQ
            </span>
          </Link>
          <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-full text-zinc-400">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="hidden md:flex items-center p-6 border-b border-white/10">
          <Link href="/" className="flex items-center gap-2 group">
            <Logo className="w-8 h-8 transition-transform group-hover:scale-105" />
            <span className="text-xl font-semibold tracking-tight text-white">
              ContractIQ
            </span>
          </Link>
        </div>

        <div className="p-4 space-y-8">
          <div>
            <h3 className="px-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
              Main Navigation
            </h3>
            <nav className="space-y-1">
              {navLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.name}
                    href={link.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                      isActive
                        ? "bg-blue-600/10 text-blue-400"
                        : "text-zinc-400 hover:text-white hover:bg-white/5"
                    }`}
                  >
                    <link.icon className={`h-4 w-4 ${isActive ? "text-blue-400" : "text-zinc-400"}`} />
                    {link.name}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div>
            <h3 className="px-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">
              Recent Activity
            </h3>
            {recentContracts.length === 0 ? (
              <p className="px-2 text-sm text-zinc-600">No recent activity</p>
            ) : (
              <ul className="space-y-1">
                {recentContracts.slice(0, 5).map((contract) => (
                  <li key={contract.id}>
                    <Link
                      href={`/scan/${contract.id}`}
                      className="group flex items-center justify-between p-2 rounded-lg hover:bg-white/5 transition-colors border border-transparent hover:border-white/5"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <FileText className="h-4 w-4 flex-shrink-0 text-zinc-500 group-hover:text-white transition-colors" />
                        <span className="text-sm text-zinc-400 group-hover:text-white truncate transition-colors">
                          {contract.file_name}
                        </span>
                      </div>
                      <RiskBadge score={contract.overall_risk_score} />
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10 bg-[#0a0a0a]">
          <Link
            href="/upload"
            className="group relative flex items-center justify-center w-full px-4 py-2 text-sm font-medium bg-zinc-100 text-black rounded-lg hover:bg-white transition-all overflow-hidden"
          >
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/20 to-blue-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-700 ease-in-out" />
            <span className="relative flex items-center gap-2">
              <Upload className="h-4 w-4" /> New Scan
            </span>
          </Link>
        </div>
      </aside>
    </>
  );
}