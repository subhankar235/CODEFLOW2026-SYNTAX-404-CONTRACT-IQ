import React from "react";

export function HeroBackground() {
  return (
    <div className="absolute inset-0 z-0 overflow-hidden pointer-events-none">
      {/* Top Right Orb - Massive milky white glow */}
      <div className="absolute top-[-30%] right-[-10%] w-[1200px] h-[1200px] rounded-full bg-gradient-to-tr from-teal-100/60 to-white/60 dark:from-white/5 dark:to-white/20 blur-[160px] opacity-100" />
      
      {/* Bottom Left Orb - Soft white glow */}
      <div className="absolute bottom-[-20%] left-[-20%] w-[1000px] h-[1000px] rounded-full bg-gradient-to-bl from-white/60 to-blue-100/60 dark:from-white/10 dark:to-white/5 blur-[140px] opacity-100" />
      
      {/* Center ambient glow - very faint */}
      <div className="absolute top-[20%] left-[20%] w-[600px] h-[600px] rounded-full bg-white/40 dark:bg-white/5 blur-[150px] opacity-100" />
    </div>
  );
}
