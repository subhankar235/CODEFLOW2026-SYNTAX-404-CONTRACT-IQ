"use client";

import * as React from "react";
import { Moon, CloudRain } from "lucide-react";
import { useTheme } from "next-themes";
import { motion } from "framer-motion";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div className="w-16 h-8 rounded-full bg-zinc-200 dark:bg-zinc-800 animate-pulse" />
    );
  }

  const isDark = theme === "dark";

  const toggleTheme = (e: React.MouseEvent<HTMLButtonElement>) => {
    const nextTheme = isDark ? "light" : "dark";

    // Fallback for browsers that don't support View Transitions API
    if (!document.startViewTransition) {
      setTheme(nextTheme);
      return;
    }

    const x = e.clientX;
    const y = e.clientY;
    const endRadius = Math.hypot(
      Math.max(x, innerWidth - x),
      Math.max(y, innerHeight - y)
    );

    const transition = document.startViewTransition(() => {
      setTheme(nextTheme);
    });

    transition.ready.then(() => {
      const clipPath = [
        `circle(0px at ${x}px ${y}px)`,
        `circle(${endRadius}px at ${x}px ${y}px)`,
      ];

      document.documentElement.animate(
        {
          clipPath: isDark ? [...clipPath].reverse() : clipPath,
        },
        {
          duration: 700,
          easing: "ease-in-out",
          pseudoElement: isDark
            ? "::view-transition-old(root)"
            : "::view-transition-new(root)",
        }
      );
    });
  };

  return (
    <button
      onClick={toggleTheme}
      className={`relative flex items-center w-16 h-8 rounded-full transition-colors duration-500 cursor-pointer overflow-hidden ${
        isDark ? 'bg-black border border-white/20' : 'bg-[#4da3e8]'
      }`}
      aria-label="Toggle theme"
    >
      {/* Background Icons */}
      <div className="absolute inset-0 flex items-center justify-between px-2 pointer-events-none">
        {/* Moon for Dark Mode (Left side) */}
        <motion.div
          initial={false}
          animate={{ opacity: isDark ? 1 : 0, scale: isDark ? 1 : 0.5 }}
          className="flex items-center justify-center relative w-4 h-4"
        >
          <Moon className="w-3.5 h-3.5 text-white fill-white" />
          {/* Small stars */}
          <div className="absolute top-0 right-0 w-0.5 h-0.5 bg-white rounded-full" />
          <div className="absolute bottom-0 left-[-2px] w-0.5 h-0.5 bg-white rounded-full" />
        </motion.div>

        {/* Sun/Cloud for Light Mode (Right side) */}
        <motion.div
          initial={false}
          animate={{ opacity: isDark ? 0 : 1, scale: isDark ? 0.5 : 1 }}
          className="flex items-center justify-center"
        >
          {/* Custom Sun/Cloud assembly to match the image */}
          <div className="relative flex items-center justify-center w-5 h-5">
            <div className="absolute w-3 h-3 bg-yellow-400 rounded-full top-0 right-0" />
            <CloudRain className="w-4 h-4 text-white fill-white absolute bottom-0 left-0" />
          </div>
        </motion.div>
      </div>

      {/* The Sliding Handle */}
      <motion.div
        layout
        initial={false}
        animate={{
          x: isDark ? 36 : 4,
        }}
        transition={{ type: "spring", stiffness: 700, damping: 30 }}
        className="w-6 h-6 rounded-full bg-white shadow-sm z-10"
      />
    </button>
  );
}
