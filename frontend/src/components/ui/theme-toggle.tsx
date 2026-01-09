"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { IconSun, IconMoon } from "@tabler/icons-react";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className={cn("w-14 h-7 rounded-full bg-muted", className)} />;
  }

  const isDark = theme === "dark";

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className={cn(
        "relative flex h-8 w-14 items-center rounded-full border border-white/10 bg-black/20 p-1 backdrop-blur-md transition-colors hover:bg-black/30 dark:bg-white/10 dark:hover:bg-white/20",
        className
      )}
      aria-label="Toggle theme"
    >
      <motion.div
        layout
        transition={{
          type: "spring",
          stiffness: 700,
          damping: 30,
        }}
        animate={{
          x: isDark ? 24 : 0,
        }}
        className="flex h-6 w-6 items-center justify-center rounded-full bg-background shadow-sm"
      >
        <motion.div
          animate={{
            scale: isDark ? 0 : 1,
            opacity: isDark ? 0 : 1,
          }}
          transition={{ duration: 0.2 }}
          className="absolute"
        >
          <IconSun className="h-4 w-4 text-yellow-500" stroke={2.5} />
        </motion.div>
        <motion.div
          animate={{
            scale: isDark ? 1 : 0,
            opacity: isDark ? 1 : 0,
          }}
          transition={{ duration: 0.2 }}
          className="absolute"
        >
          <IconMoon className="h-4 w-4 text-blue-500" stroke={2.5} />
        </motion.div>
      </motion.div>
    </button>
  );
}
