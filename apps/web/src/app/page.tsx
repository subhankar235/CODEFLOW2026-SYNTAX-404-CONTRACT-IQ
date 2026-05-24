"use client";

import Link from "next/link";
import { UserButton, useUser } from "@clerk/nextjs";
import { ArrowRight, ShieldCheck, Play, ArrowDown, ExternalLink, User } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Logo } from "@/components/logo";
import { motion } from "framer-motion";
import { HeroBackground } from "@/components/landing/hero-background";
import { InsightsSection } from "@/components/landing/insights-section";
import { IntegritySection } from "@/components/landing/integrity-section";
import { LandingFooter } from "@/components/landing/landing-footer";
import MagicRings from "@/components/MagicRings";
import AnimatedContent from "@/components/animations/AnimatedContent";

export default function Home() {
  const { isLoaded, isSignedIn } = useUser();

  return (
    <div className="relative min-h-screen bg-zinc-50 dark:bg-[#050505] overflow-x-hidden font-sans selection:bg-teal-500/30">
      <div className="fixed inset-0 z-0 opacity-100 pointer-events-none">
        <MagicRings 
          speed={1} 
          ringCount={12} 
          color="#00ffcc" 
          colorTwo="#3b82f6" 
          opacity={1} 
          blur={0}
          followMouse={true}
          mouseInfluence={0.2}
          radiusStep={0.12}
        />
      </div>
      
      {/* Floating Navbar */}
      <nav className="fixed top-6 left-1/2 -translate-x-1/2 z-50 w-[95%] max-w-5xl glass-panel rounded-full px-6 py-3 flex items-center justify-between shadow-2xl shadow-black/5 dark:shadow-black/20">
        <Link href="/" className="flex items-center gap-2 group">
          <Logo className="w-8 h-8 transition-transform group-hover:scale-105" />
        </Link>

        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-600 dark:text-zinc-300">
          <Link href="/" className="text-zinc-900 dark:text-white">Home</Link>
          <Link href="#app" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Legal App</Link>
          <Link href="#assets" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Assets</Link>
          <Link href="#features" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Features</Link>
          <Link href="#pricing" className="hover:text-zinc-900 dark:hover:text-white transition-colors">Pricing</Link>

          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 dark:bg-white/10 text-xs text-zinc-900 dark:text-white">
            Protection <ExternalLink className="w-3 h-3" />
          </div>
          <ShieldCheck className="w-5 h-5 text-zinc-400" />
        </div>

        <div className="flex items-center gap-4">
          <ThemeToggle />
          {isLoaded && isSignedIn ? (
            <div className="flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-sm font-medium text-zinc-600 dark:text-zinc-300 hover:text-zinc-900 dark:hover:text-white"
              >
                Dashboard
              </Link>
              <UserButton />
            </div>
          ) : (
            <Link
              href="/sign-up"
              className="flex items-center gap-2 text-sm font-medium text-zinc-900 dark:text-white hover:opacity-80 transition-opacity"
            >
              <span className="hidden sm:inline">Create Account</span>
              <div className="w-8 h-8 rounded-full bg-zinc-200 dark:bg-white/10 flex items-center justify-center">
                <User className="w-4 h-4" />
              </div>
            </Link>
          )}
        </div>
      </nav>

      {/* Main Hero Content */}
      <main className="relative z-10 flex flex-col items-center justify-center min-h-screen px-4 pt-32 pb-20">

        {/* Play Button Indicator */}
        <AnimatedContent distance={50} direction="vertical" delay={0.2}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="mb-12 w-12 h-12 rounded-full glass-panel flex items-center justify-center hover:scale-110 transition-transform cursor-pointer"
          >
            <Play className="w-4 h-4 text-zinc-900 dark:text-white ml-1" />
          </motion.div>
        </AnimatedContent>

        {/* Small Tag */}
        <AnimatedContent distance={50} direction="vertical" delay={0.3}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel text-xs font-medium text-zinc-800 dark:text-zinc-200 mb-8"
          >
            <ShieldCheck className="w-3 h-3 text-teal-500" />
            Unlock Your Contract Spark! <ArrowRight className="w-3 h-3 ml-1" />
          </motion.div>
        </AnimatedContent>

        {/* Hero Typography */}
        <AnimatedContent distance={80} direction="vertical" delay={0.4}>
          <div className="text-center max-w-4xl mx-auto">
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight text-zinc-900 dark:text-white mb-6 font-sans">
              One-click for <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-blue-500">Contract Defense</span>
            </h1>
            <p className="text-lg md:text-xl text-zinc-600 dark:text-zinc-400 mb-10 max-w-2xl mx-auto font-light">
              Dive into your legal assets, where innovative AI technology meets professional legal expertise.
            </p>
          </div>
        </AnimatedContent>

        {/* CTA Buttons */}
        <AnimatedContent distance={40} direction="vertical" delay={0.6}>
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <Link
              href="/sign-up"
              className="group flex items-center justify-center gap-2 px-6 py-3 rounded-full glass-panel text-sm font-medium text-zinc-900 dark:text-white hover:bg-zinc-200 dark:hover:bg-white/10 transition-all"
            >
              Open App <ExternalLink className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
            </Link>
            <Link
              href="#discover"
              className="px-8 py-3 rounded-full bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-sm font-medium hover:scale-105 transition-transform shadow-xl shadow-zinc-900/20 dark:shadow-white/20"
            >
              Discover More
            </Link>
          </div>
        </AnimatedContent>

        {/* Floating Nodes Map (Simulated) */}
        <div className="absolute inset-0 pointer-events-none z-0 overflow-hidden max-w-7xl mx-auto">
          {/* Node 1: Risk Scanner */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1, delay: 0.6 }}
            className="absolute top-[20%] left-[5%] md:left-[10%] flex flex-col items-center gap-2"
          >
            <div className="w-3 h-3 rounded-full bg-teal-500 shadow-[0_0_15px_rgba(20,184,166,0.5)]" />
            <div className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
              <span className="text-zinc-800 dark:text-zinc-200 font-bold">Risk Scanner</span><br />
              99.9%
            </div>
          </motion.div>

          {/* Node 2: Power Meter */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1, delay: 0.7 }}
            className="absolute top-[15%] right-[5%] md:right-[15%] flex flex-col items-center gap-2"
          >
            <div className="w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_15px_rgba(59,130,246,0.5)]" />
            <div className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
              <span className="text-zinc-800 dark:text-zinc-200 font-bold">Power Meter</span><br />
              Balanced
            </div>
          </motion.div>

          {/* Node 3: Counter-Offer */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.8 }}
            className="absolute bottom-[25%] left-[2%] md:left-[8%] flex flex-col items-center gap-2"
          >
            <div className="w-4 h-4 rounded-full bg-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.5)] border-2 border-zinc-950" />
            <div className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
              <span className="text-zinc-800 dark:text-zinc-200 font-bold">Counter-Offer</span><br />
              12 Generated
            </div>
          </motion.div>

          {/* Node 4: Precedent */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.9 }}
            className="absolute bottom-[30%] right-[2%] md:right-[10%] flex flex-col items-center gap-2"
          >
            <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-[0_0_15px_rgba(16,185,129,0.5)]" />
            <div className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
              <span className="text-zinc-800 dark:text-zinc-200 font-bold">Precedent</span><br />
              440 Cases
            </div>
          </motion.div>
        </div>

        {/* Scroll Indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1 }}
          className="absolute bottom-32 left-8 md:left-16 flex items-center gap-3 text-xs font-mono text-zinc-500 dark:text-zinc-400"
        >
          <div className="w-8 h-8 rounded-full glass-panel flex items-center justify-center">
            <ArrowDown className="w-3 h-3" />
          </div>
          <span>01/03 . Scroll down</span>
        </motion.div>

        {/* Right Indicator (Legal Horizons) */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1, delay: 1 }}
          className="absolute bottom-32 right-8 md:right-16 hidden md:flex flex-col gap-2 text-xs font-mono text-zinc-500 dark:text-zinc-400"
        >
          <span>Legal horizons</span>
          <div className="flex items-center gap-1">
            <div className="w-8 h-1 rounded-full bg-zinc-900 dark:bg-white" />
            <div className="w-4 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
            <div className="w-4 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
            <div className="w-4 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
          </div>
        </motion.div>

      </main>

      {/* Logos Strip */}
      <section id="assets" className="relative z-10 border-t border-zinc-200 dark:border-white/5 bg-white/30 dark:bg-[#050505]/30 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-8 flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-60 grayscale hover:grayscale-0 transition-all duration-500">
          <span className="text-lg font-bold font-mono tracking-tighter">OpenAI</span>
          <span className="text-lg font-bold font-mono tracking-tighter">Stripe</span>
          <span className="text-lg font-bold font-mono tracking-tighter">Vercel</span>
          <span className="text-lg font-bold font-mono tracking-tighter">Clerk</span>
          <span className="text-lg font-bold font-mono tracking-tighter">LegalTech</span>
        </div>
      </section>

      {/* New Extended Sections */}
      <div id="features">
        <AnimatedContent distance={100} direction="vertical" threshold={0.2}>
          <InsightsSection />
        </AnimatedContent>
      </div>
      
      <div id="app">
        <AnimatedContent distance={100} direction="vertical" threshold={0.2}>
          <IntegritySection />
        </AnimatedContent>
      </div>

      {/* Placeholder Pricing Section to satisfy the #pricing link */}
      <section id="pricing" className="py-24 px-4 bg-zinc-50/30 dark:bg-[#050505]/30 backdrop-blur-md border-t border-zinc-200 dark:border-white/5">
        <AnimatedContent distance={60} direction="vertical" threshold={0.3}>
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-zinc-900 dark:text-white mb-6">Simple, Transparent Pricing</h2>
            <p className="text-zinc-500 dark:text-zinc-400 mb-12">Designed for legal teams of all sizes. Coming soon.</p>
            <div className="inline-flex items-center justify-center glass-panel px-8 py-4 rounded-2xl text-zinc-800 dark:text-zinc-200">
              Contact us for early access and enterprise plans.
            </div>
          </div>
        </AnimatedContent>
      </section>

      <LandingFooter />

    </div>
  );
}