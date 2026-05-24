"use client";

import React from "react";
import Link from "next/link";
import { Logo } from "@/components/logo";
import { Mail, Shield, ArrowUpRight, Globe, MessageSquare, Info } from "lucide-react";

export function LandingFooter() {
  const currentYear = new Date().getFullYear();

  const footerLinks = [
    {
      title: "Product",
      links: [
        { name: "Features", href: "#features" },
        { name: "Legal App", href: "#app" },
        { name: "Pricing", href: "#pricing" },
        { name: "Security", href: "#" },
      ],
    },
    {
      title: "Company",
      links: [
        { name: "About Us", href: "#" },
        { name: "Careers", href: "#" },
        { name: "Blog", href: "#" },
        { name: "Contact", href: "#" },
      ],
    },
    {
      title: "Resources",
      links: [
        { name: "Documentation", href: "#" },
        { name: "Help Center", href: "#" },
        { name: "Community", href: "#" },
        { name: "Privacy Policy", href: "#" },
      ],
    },
  ];

  const socialLinks = [
    { icon: <Globe className="w-5 h-5" />, href: "#", label: "Global" },
    { icon: <MessageSquare className="w-5 h-5" />, href: "#", label: "Community" },
    { icon: <Info className="w-5 h-5" />, href: "#", label: "Updates" },
  ];

  return (
    <footer className="relative z-10 bg-zinc-50 dark:bg-[#050505] border-t border-zinc-200 dark:border-white/5 pt-24 pb-12 px-6">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-12 lg:gap-8 mb-20">
          
          {/* Brand Column */}
          <div className="lg:col-span-2">
            <Link href="/" className="flex items-center gap-2 group mb-6">
              <Logo className="w-8 h-8 transition-transform group-hover:scale-110" />
              <span className="text-xl font-bold tracking-tight text-zinc-900 dark:text-white">
                ContractIQ
              </span>
            </Link>
            <p className="text-zinc-500 dark:text-zinc-400 max-w-sm mb-8 leading-relaxed">
              Empowering legal teams with cutting-edge AI for smarter document review, risk detection, and contract analysis.
            </p>
            <div className="flex items-center gap-4">
              {socialLinks.map((social, idx) => (
                <Link 
                  key={idx} 
                  href={social.href}
                  className="w-10 h-10 rounded-full glass-panel flex items-center justify-center text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-200 dark:hover:bg-white/10 transition-all"
                  aria-label={social.label}
                >
                  {social.icon}
                </Link>
              ))}
            </div>
          </div>

          {/* Links Columns */}
          {footerLinks.map((column, idx) => (
            <div key={idx}>
              <h4 className="text-zinc-900 dark:text-white font-semibold mb-6">{column.title}</h4>
              <ul className="space-y-4">
                {column.links.map((link, linkIdx) => (
                  <li key={linkIdx}>
                    <Link 
                      href={link.href}
                      className="text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors flex items-center gap-1 group"
                    >
                      {link.name}
                      <ArrowUpRight className="w-3 h-3 opacity-0 -translate-y-0.5 group-hover:opacity-100 transition-all" />
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="pt-12 border-t border-zinc-200 dark:border-white/5 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6 text-sm text-zinc-500 dark:text-zinc-400">
            <div className="flex items-center gap-1.5">
              <Shield className="w-4 h-4 text-teal-500" />
              <span>Not legal advice</span>
            </div>
            <span>© {currentYear} ContractIQ.</span>
          </div>
          
          <div className="flex items-center gap-8">
            <Link href="mailto:hello@contractiq.com" className="flex items-center gap-2 text-sm text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white transition-colors">
              <Mail className="w-4 h-4" />
              hello@contractiq.com
            </Link>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400 uppercase tracking-widest">Systems Operational</span>
            </div>
          </div>
        </div>
      </div>

      {/* Decorative background gradient */}
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-teal-500/10 blur-[120px] rounded-full pointer-events-none z-0" />
    </footer>
  );
}
