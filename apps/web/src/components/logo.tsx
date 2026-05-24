import * as React from "react";

export function Logo({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <path
        d="M12 2L3 6V11C3 16.55 6.84 21.74 12 23C17.16 21.74 21 16.55 21 11V6L12 2Z"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="text-zinc-900 dark:text-zinc-100"
      />
      <path
        d="M12 22C12 22 19 16 19 11V7L12 4L5 7V11C5 16 12 22 12 22Z"
        fill="currentColor"
        className="text-zinc-900 dark:text-white"
        fillOpacity="0.2"
      />
      <circle
        cx="12"
        cy="11"
        r="3"
        stroke="currentColor"
        strokeWidth="2"
        className="text-teal-500 dark:text-teal-400"
      />
      <path
        d="M12 14V17"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        className="text-teal-500 dark:text-teal-400"
      />
    </svg>
  );
}
