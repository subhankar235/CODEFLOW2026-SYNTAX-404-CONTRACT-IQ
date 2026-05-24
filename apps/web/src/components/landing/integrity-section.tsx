"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, FileCheck, FileWarning, Zap, Lock, Database, Globe, Cpu } from "lucide-react";

export function IntegritySection() {
  const [activeStep, setActiveStep] = useState(1);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  const steps = [
    { id: 1, label: "Step 01", title: "Target 2024 Legal API", icon: <Zap className="w-6 h-6" />, color: "zinc" },
    { id: 2, label: "Step 02", title: "Consensus Layer", icon: <Globe className="w-6 h-6" />, color: "blue" },
    { id: 3, label: "Step 03", title: "Smart Verification", icon: <Lock className="w-6 h-6" />, color: "teal" },
    { id: 4, label: "Step 04", title: "Tokenized Assets", icon: <Database className="w-6 h-6" />, color: "purple" },
  ];

  // Auto-cycle effect
  useEffect(() => {
    if (!isAutoPlaying) return;

    const interval = setInterval(() => {
      setActiveStep((prev) => (prev % 4) + 1);
    }, 4000); // 4 second interval

    return () => clearInterval(interval);
  }, [isAutoPlaying]);

  const currentStep = steps.find(s => s.id === activeStep) || steps[0];

  const floatingAnimation = {
    y: [0, -10, 0],
    transition: {
      duration: 4,
      repeat: Infinity,
      ease: "easeInOut" as const
    }
  };

  const handleStepClick = (id: number) => {
    setActiveStep(id);
    setIsAutoPlaying(false); // Stop auto-playing when user interacts
  };

  return (
    <section 
      onMouseEnter={() => setIsAutoPlaying(false)}
      onMouseLeave={() => setIsAutoPlaying(true)}
      className="relative z-10 py-32 px-4 bg-zinc-50/30 dark:bg-[#050505]/30 backdrop-blur-md border-t border-zinc-200 dark:border-white/5 overflow-hidden"
    >
      
      {/* Background glow for this specific section */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full bg-zinc-200/50 dark:bg-zinc-900/50 blur-[120px] pointer-events-none" />

      <div className="max-w-6xl mx-auto relative z-10">
        <div className="text-center mb-24">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold text-zinc-900 dark:text-white mb-6 tracking-tight"
          >
            Document Integrity
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-zinc-500 dark:text-zinc-400 max-w-xl mx-auto mb-8"
          >
            Exploratory mission with Legal Horizon & navigating through the vast possibilities.
          </motion.p>
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-zinc-200 dark:bg-white/10 text-zinc-900 dark:text-white text-sm cursor-pointer hover:bg-zinc-300 dark:hover:bg-white/20 transition-colors"
          >
            How it works?
          </motion.div>
        </div>

        <div className="flex flex-col lg:flex-row items-center justify-between gap-16 lg:gap-8">
          
          {/* Left Graphic: Nested Ovals / Flow */}
          <motion.div 
            initial={{ opacity: 0, x: -50 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="flex-1 w-full max-w-lg relative h-[350px] md:h-[400px]"
          >
            <div className="absolute top-0 left-0 md:left-4">
              <h3 className="text-zinc-500 dark:text-zinc-400 text-xs md:text-sm mb-1 font-mono uppercase tracking-widest">Legal Review System</h3>
              <p className="text-3xl md:text-4xl font-bold text-zinc-900 dark:text-white">+A3.7</p>
            </div>

            {/* Simulated orbital paths */}
            <svg viewBox="0 0 400 400" className="absolute inset-0 w-full h-full opacity-30 text-zinc-400 dark:text-white">
              <motion.ellipse 
                cx="200" cy="200" rx="180" ry="80" fill="none" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" transform="rotate(-15 200 200)"
                animate={{ rotate: [-15, -13, -15] }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" as const }}
              />
              <motion.ellipse 
                cx="200" cy="200" rx="120" ry="50" fill="none" stroke="currentColor" strokeWidth="1" transform="rotate(-15 200 200)"
                animate={{ rotate: [-15, -17, -15] }}
                transition={{ duration: 8, repeat: Infinity, ease: "linear" as const }}
              />
            </svg>

            {/* Nodes on paths */}
            <motion.div 
              animate={floatingAnimation}
              className="absolute top-[20%] right-[-10px] md:right-[5%] glass-panel px-3 md:px-4 py-1.5 md:py-2 rounded-full flex items-center gap-2 md:gap-3 border border-zinc-200 dark:border-white/10 shadow-xl scale-90 md:scale-100 origin-right hover:scale-105 transition-transform cursor-pointer"
            >
              <div className="w-5 h-5 md:w-6 md:h-6 rounded-full bg-white dark:bg-zinc-800 flex items-center justify-center shrink-0">
                <FileWarning className="w-3 h-3 text-red-500 dark:text-red-400" />
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] md:text-xs text-zinc-900 dark:text-white leading-tight">Pending</span>
                <span className="text-[8px] md:text-[10px] text-zinc-500 leading-tight">from 0x938</span>
              </div>
              <span className="text-[10px] md:text-xs font-mono text-zinc-500 dark:text-zinc-400 ml-1 md:ml-2">12 docs</span>
            </motion.div>

            <motion.div 
              animate={{ ...floatingAnimation, transition: { ...floatingAnimation.transition, delay: 1 } }}
              className="absolute top-[50%] left-[-10px] md:left-[10%] glass-panel px-3 md:px-4 py-1.5 md:py-2 rounded-full flex items-center gap-2 md:gap-3 border border-zinc-200 dark:border-white/10 shadow-xl scale-90 md:scale-100 origin-left hover:scale-105 transition-transform cursor-pointer"
            >
              <div className="w-5 h-5 md:w-6 md:h-6 rounded-full bg-white dark:bg-zinc-800 flex items-center justify-center shrink-0">
                <ShieldCheck className="w-3 h-3 text-teal-500 dark:text-teal-400" />
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] md:text-xs text-zinc-900 dark:text-white leading-tight">Verified</span>
                <span className="text-[8px] md:text-[10px] text-zinc-500 leading-tight">from 0xB47</span>
              </div>
              <span className="text-[10px] md:text-xs font-mono text-zinc-500 dark:text-zinc-400 ml-1 md:ml-2">1,038 docs</span>
            </motion.div>

            <motion.div 
              animate={{ ...floatingAnimation, transition: { ...floatingAnimation.transition, delay: 2 } }}
              className="absolute bottom-[-5%] md:bottom-[10%] left-[50%] -translate-x-1/2 md:translate-x-0 md:left-[20%] glass-panel px-3 md:px-4 py-1.5 md:py-2 rounded-full flex items-center gap-2 md:gap-3 border border-zinc-200 dark:border-white/10 shadow-xl scale-90 md:scale-100 hover:scale-105 transition-transform cursor-pointer"
            >
              <div className="w-5 h-5 md:w-6 md:h-6 rounded-full bg-white dark:bg-zinc-800 flex items-center justify-center shrink-0">
                <FileCheck className="w-3 h-3 text-blue-500 dark:text-blue-400" />
              </div>
              <div className="flex flex-col">
                <span className="text-[10px] md:text-xs text-zinc-900 dark:text-white leading-tight">Sent</span>
                <span className="text-[8px] md:text-[10px] text-zinc-500 leading-tight">to x7360</span>
              </div>
              <span className="text-[10px] md:text-xs font-mono text-zinc-500 dark:text-zinc-400 ml-1 md:ml-2">4,948</span>
            </motion.div>
            
            <div className="absolute bottom-[10%] md:bottom-[5%] right-[10%] md:right-[25%] text-[10px] md:text-xs text-zinc-500 font-mono">
              Done
            </div>
          </motion.div>

          {/* Right Graphic: Circular Progress Ring */}
          <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="flex-1 w-full max-w-sm flex flex-col items-center justify-center relative"
          >
            <div className="relative w-72 h-72 flex items-center justify-center">
              {/* Animated Outer Rings */}
              <svg className="absolute inset-0 w-full h-full -rotate-90">
                <circle cx="144" cy="144" r="130" fill="none" className="stroke-zinc-200 dark:stroke-white/5" strokeWidth="2" />
                <motion.circle 
                  cx="144" cy="144" r="110" fill="none" className="stroke-zinc-200 dark:stroke-white/5" strokeWidth="24" 
                />
                <motion.circle 
                  cx="144" cy="144" r="110" fill="none" 
                  className={`stroke-zinc-800 dark:stroke-white/80 transition-colors duration-500`} 
                  strokeWidth="24" 
                  strokeDasharray="690" 
                  animate={{ strokeDashoffset: [690, 690 - (activeStep * 172)] }}
                  transition={{ type: "spring", stiffness: 50 }}
                />
              </svg>
              
              {/* Inner Glowing Orb */}
              <AnimatePresence mode="wait">
                <motion.div 
                  key={activeStep}
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  exit={{ scale: 0.8, opacity: 0 }}
                  className="absolute inset-0 m-auto w-36 h-36 rounded-full bg-white dark:bg-zinc-900 shadow-[0_0_50px_rgba(0,0,0,0.05)] dark:shadow-[0_0_50px_rgba(255,255,255,0.1)] flex flex-col items-center justify-center border border-zinc-200 dark:border-white/10 z-10"
                >
                  <motion.div 
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="flex flex-col items-center"
                  >
                    <div className="text-zinc-900 dark:text-white mb-1">
                      {currentStep.icon}
                    </div>
                    <span className="text-[10px] font-bold text-zinc-900 dark:text-white tracking-widest uppercase">{currentStep.label}</span>
                  </motion.div>
                </motion.div>
              </AnimatePresence>
              
              {/* Floating Indicator Tooltip */}
              <motion.div 
                key={`tooltip-${activeStep}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="absolute top-[10%] -right-8 text-[10px] text-zinc-500 font-mono bg-white/80 dark:bg-zinc-950/80 p-2 rounded-lg border border-zinc-200 dark:border-white/10 shadow-lg backdrop-blur-md z-20 w-24"
              >
                <div className="text-zinc-400 mb-1 leading-tight">Target Context</div>
                <div className="text-zinc-900 dark:text-zinc-100 font-bold leading-tight">{currentStep.title}</div>
              </motion.div>
            </div>

            {/* Interactive Step Controls / Tags */}
            <div className="mt-16 flex flex-wrap justify-center gap-3">
              {[
                { id: 1, label: "2.7K Assets", icon: <ShieldCheck className="w-3 h-3" /> },
                { id: 2, label: "Success", icon: <FileCheck className="w-3 h-3" /> },
                { id: 3, label: "Decentralized", icon: <Zap className="w-3 h-3" /> }
              ].map((btn) => (
                <motion.button
                  key={btn.id}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleStepClick(btn.id)}
                  className={`px-4 py-2 rounded-full text-xs transition-all duration-300 flex items-center gap-2 border cursor-pointer ${
                    activeStep === btn.id 
                    ? "bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 shadow-[0_0_20px_rgba(255,255,255,0.2)] border-transparent" 
                    : "bg-zinc-200 dark:bg-white/5 text-zinc-500 border-zinc-300 dark:border-white/10 hover:border-zinc-400 dark:hover:border-white/30"
                  }`}
                >
                  {btn.icon} {btn.label}
                </motion.button>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap justify-center gap-3">
              {[
                { id: 4, label: "Smart Contracts", icon: <Cpu className="w-3 h-3" /> },
                { id: 1, label: "Tokenized Trust", icon: <Lock className="w-3 h-3" /> }
              ].map((btn, idx) => (
                <motion.button
                  key={`${btn.id}-${idx}`}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => handleStepClick(btn.id)}
                  className={`px-4 py-2 rounded-full text-xs transition-all duration-300 border cursor-pointer ${
                    activeStep === btn.id && btn.id === 4
                    ? "bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 border-transparent" 
                    : "bg-zinc-200 dark:bg-white/5 text-zinc-500 border-zinc-300 dark:border-white/10"
                  }`}
                >
                  ◆ {btn.label}
                </motion.button>
              ))}
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}


