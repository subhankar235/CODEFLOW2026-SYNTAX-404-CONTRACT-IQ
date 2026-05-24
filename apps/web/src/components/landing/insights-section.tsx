"use client";

import React from "react";
import { motion } from "framer-motion";

export function InsightsSection() {
  const barVariants = {
    hidden: { height: 0, opacity: 0 },
    visible: (custom: number) => ({
      height: `${custom}%`,
      opacity: 1,
      transition: { duration: 1, ease: "easeOut" as const, delay: Math.random() * 0.5 }
    })
  };

  return (
    <section className="relative z-10 py-24 px-4 bg-zinc-100/30 dark:bg-[#050505]/30 backdrop-blur-md">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-4xl md:text-5xl font-bold text-zinc-900 dark:text-white mb-4 tracking-tight"
          >
            Meet Legal Insights
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-zinc-500 dark:text-zinc-400 max-w-xl mx-auto"
          >
            Save your legal team&apos;s precious time. Our AI replaces the lengthy process of manual document review.
          </motion.p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[250px]">
          
          {/* Top Left: Accuracy Map */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5, scale: 1.01 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="col-span-1 md:col-span-2 row-span-1 glass-panel rounded-3xl p-8 relative overflow-hidden flex flex-col justify-between group transition-all"
          >
            <div className="z-10">
              <motion.h3 
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                className="text-4xl font-bold text-zinc-900 dark:text-white mb-1"
              >
                98.2%<span className="text-teal-500">.</span>
              </motion.h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">Accuracy . Global Standards</p>
            </div>
            
            {/* Abstract Map Graphic */}
            <div className="absolute right-0 top-0 bottom-0 w-1/2 opacity-30 pointer-events-none">
              <svg viewBox="0 0 200 200" fill="none" className="w-full h-full text-zinc-400 dark:text-white/20">
                <motion.ellipse 
                  cx="100" cy="100" rx="80" ry="40" stroke="currentColor" strokeWidth="1" strokeDasharray="4 4" transform="rotate(-20 100 100)" 
                  animate={{ rotate: [-20, 340] }}
                  transition={{ duration: 20, repeat: Infinity, ease: "linear" as const }}
                />
                <motion.circle 
                  cx="150" cy="80" r="4" fill="currentColor" className="text-teal-500 dark:text-white" 
                  animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 3, repeat: Infinity }}
                />
                <circle cx="80" cy="60" r="3" fill="currentColor" />
                <circle cx="120" cy="130" r="5" fill="currentColor" />
              </svg>
            </div>

            <div className="flex gap-2 text-xs font-mono text-zinc-500 dark:text-zinc-400 z-10">
              <span className="bg-zinc-200 dark:bg-white/5 px-3 py-1.5 rounded-full hover:bg-zinc-300 dark:hover:bg-white/10 transition-colors cursor-pointer">Open Scans</span>
              <span className="bg-zinc-200 dark:bg-white/5 px-3 py-1.5 rounded-full hover:bg-zinc-300 dark:hover:bg-white/10 transition-colors cursor-pointer">Assign Issue</span>
            </div>
          </motion.div>

          {/* Top Right: Risk Detection Bar Chart */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5, scale: 1.01 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="col-span-1 row-span-1 glass-panel rounded-3xl p-8 relative overflow-hidden flex flex-col group transition-all"
          >
            <div className="mb-auto z-10">
              <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">Risk Detection</h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 line-clamp-2">
                Clause-by-clause analysis where each turn reveals new insights.
              </p>
            </div>
            
            {/* Animated Bar Chart */}
            <div className="flex items-end justify-center gap-3 h-24 mt-4 relative">
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={40} className="w-4 bg-zinc-300 dark:bg-white/20 rounded-t-sm" />
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={80} className="w-4 bg-teal-400/50 dark:bg-teal-500 rounded-t-sm" />
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={60} className="w-4 bg-zinc-300 dark:bg-white/20 rounded-t-sm" />
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={30} className="w-4 bg-zinc-300 dark:bg-white/20 rounded-t-sm" />
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={90} className="w-4 bg-blue-400/50 dark:bg-blue-500 rounded-t-sm shadow-[0_0_15px_rgba(59,130,246,0.3)]" />
            </div>
          </motion.div>

          {/* Bottom Left: Growth Stats */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5, scale: 1.01 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="col-span-1 row-span-1 glass-panel rounded-3xl p-8 flex flex-col justify-between group transition-all"
          >
            <div className="flex justify-between items-end border-b border-zinc-200 dark:border-white/10 pb-4 mb-4">
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1 flex items-center gap-1">
                  <span className="w-1 h-3 bg-yellow-500 rounded-full" /> Financial
                </p>
                <p className="text-zinc-500 dark:text-zinc-400 text-sm">Saved</p>
                <p className="text-3xl font-bold text-zinc-900 dark:text-white mt-1">19.2<span className="text-sm font-normal text-zinc-500 dark:text-zinc-400 ml-1">k</span></p>
              </div>
              <div>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mb-1 flex items-center gap-1">
                  <span className="w-1 h-3 bg-teal-500 rounded-full" /> Time
                </p>
                <p className="text-zinc-500 dark:text-zinc-400 text-sm">Saved</p>
                <p className="text-3xl font-bold text-zinc-900 dark:text-white mt-1">24<span className="text-sm font-normal text-zinc-500 dark:text-zinc-400 ml-1">hrs</span></p>
              </div>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-zinc-900 dark:text-white group-hover:text-teal-500 transition-colors">Your Palette of Opportunities</h3>
              <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1">Watch your legal efficiency grow in a thriving ecosystem.</p>
            </div>
          </motion.div>

          {/* Bottom Right: Line Chart Landscape */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            whileHover={{ y: -5, scale: 1.01 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="col-span-1 md:col-span-2 row-span-1 glass-panel rounded-3xl p-8 relative overflow-hidden group transition-all"
          >
            <div className="absolute inset-0 bg-gradient-to-t from-zinc-200/50 dark:from-white/5 to-transparent z-0 pointer-events-none" />
            <div className="relative z-10 flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold text-zinc-900 dark:text-white group-hover:text-blue-500 transition-colors">Legal Space . Opportunities</h3>
                <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 max-w-sm">
                  Where every contract reviewed is a chance to build a stronger foundation.
                </p>
              </div>
            </div>
            
            {/* Simulated Animated Chart */}
            <div className="absolute bottom-6 left-8 right-8 h-24 flex items-end justify-around z-10">
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={40} className="w-6 bg-red-400/60 rounded-t-sm" />
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={60} className="w-6 bg-yellow-400/60 rounded-t-sm" />
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={100} className="w-6 bg-teal-400/80 rounded-t-sm shadow-[0_0_15px_rgba(20,184,166,0.3)]" />
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={50} className="w-6 bg-blue-400/60 rounded-t-sm" />
              <motion.div variants={barVariants} initial="hidden" whileInView="visible" custom={70} className="w-6 bg-emerald-400/60 rounded-t-sm" />
              
              {/* Overlay line */}
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
                <motion.path 
                  d="M0,60 Q50,20 100,50 T200,10 T300,40 T400,20" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2" 
                  className="dark:text-white/30 text-zinc-400/50"
                  initial={{ pathLength: 0 }}
                  whileInView={{ pathLength: 1 }}
                  transition={{ duration: 2, ease: "easeInOut" as const }}
                />
              </svg>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
