import Link from "next/link";
import { UserButton, useUser } from "@clerk/nextjs";
import { LayoutDashboard, Upload, Bell, Search } from "lucide-react";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Logo } from "@/components/logo";

export function Navbar({ 
  onMenuClick, 
  sidebarOpen, 
  hideLogo 
}: { 
  onMenuClick?: () => void; 
  sidebarOpen?: boolean; 
  hideLogo?: boolean; 
}) {
  const { isLoaded, isSignedIn } = useUser();
  const pathname = usePathname();

  if (!isLoaded) {
    return (
      <header className="sticky top-0 z-50 w-full glass-panel border-b border-white/5 bg-black/40">
        <div className="flex h-16 items-center justify-between px-6">
          <div className="h-5 w-32 animate-pulse rounded bg-white/10" />
        </div>
      </header>
    );
  }

  return (
    <header className="sticky top-0 z-50 w-full glass-panel border-b border-white/5 bg-black/40 backdrop-blur-md">
      <div className="flex h-16 items-center justify-between px-4 lg:px-8">
        <div className="flex items-center gap-4 lg:gap-10">
          {/* Hamburger Menu (Mobile Only) */}
          <button 
            onClick={onMenuClick}
            className="md:hidden relative h-10 w-10 flex items-center justify-center rounded-full hover:bg-white/5 transition-colors focus:outline-none"
            aria-label="Toggle menu"
          >
            <div className="w-5 flex flex-col items-end justify-center gap-[5px]">
              <span className={`h-[2px] w-full bg-white rounded-full transition-transform duration-300 ${sidebarOpen ? 'rotate-45 translate-y-[7px]' : ''}`} />
              <span className={`h-[2px] w-full bg-white rounded-full transition-opacity duration-300 ${sidebarOpen ? 'opacity-0' : 'opacity-100'}`} />
              <span className={`h-[2px] w-full bg-white rounded-full transition-transform duration-300 ${sidebarOpen ? '-rotate-45 -translate-y-[7px]' : ''}`} />
            </div>
          </button>

          {(!hideLogo) && (
            <Link href="/" className={`flex items-center gap-2 group ${hideLogo ? 'md:hidden' : ''}`}>
              <Logo className="w-8 h-8 transition-transform group-hover:scale-105" />
              <span className="text-xl font-semibold tracking-tight text-white hidden sm:block">
                ContractIQ
              </span>
            </Link>
          )}
          
          {isSignedIn && (
            <div className="hidden md:flex items-center relative group">
               <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                 <Search className="h-4 w-4 text-zinc-500" />
               </div>
               <input
                 type="text"
                 className="block w-64 pl-10 pr-3 py-1.5 border border-white/10 rounded-md leading-5 bg-white/5 text-zinc-300 placeholder-zinc-500 focus:outline-none focus:bg-white/10 focus:border-white/20 focus:ring-0 sm:text-sm transition-all"
                 placeholder="Search contracts..."
               />
            </div>
          )}
        </div>

        <div className="flex items-center gap-4">
          {isSignedIn ? (
             <div className="flex items-center gap-4">
               <button className="p-2 text-zinc-400 hover:text-white transition-colors rounded-full hover:bg-white/5">
                 <Bell className="h-4 w-4" />
               </button>
               <div className="h-6 w-px bg-white/10" />
               <UserButton 
                 appearance={{
                   elements: {
                     userButtonAvatarBox: "h-8 w-8 rounded-full border border-white/10 shadow-sm"
                   }
                 }}
               />
             </div>
          ) : (
             <div className="flex items-center gap-3">
               <Link
                 href="/sign-in"
                 className="px-4 py-2 text-sm font-medium text-zinc-400 hover:text-white transition-colors"
               >
                 Log in
               </Link>
               <Link
                 href="/sign-up"
                 className="px-4 py-2 text-sm font-medium bg-white text-black rounded-lg hover:bg-zinc-200 transition-colors shadow-[0_0_15px_rgba(255,255,255,0.1)]"
               >
                 Start free
               </Link>
             </div>
          )}
        </div>
      </div>
    </header>
  );
}