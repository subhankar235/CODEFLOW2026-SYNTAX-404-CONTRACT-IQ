"use client";

import { cn } from "@/lib/utils";

interface VersionTabsProps {
  versions: string[];
  activeVersion: string;
  onSelect: (version: string) => void;
}

export function VersionTabs({ versions, activeVersion, onSelect }: VersionTabsProps) {
  return (
    <div className="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground">
      {versions.map((version) => (
        <button
          key={version}
          onClick={() => onSelect(version)}
          className={cn(
            "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
            activeVersion === version
              ? "bg-background text-foreground shadow-sm"
              : "hover:bg-muted/80 hover:text-foreground"
          )}
        >
          {version}
        </button>
      ))}
    </div>
  );
}
