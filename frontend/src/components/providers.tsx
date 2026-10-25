"use client";

import { MotionConfig } from "motion/react";
import { ThemeProvider } from "next-themes";

import { TooltipProvider } from "@/components/ui/tooltip";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      {/* "user" = respect the OS "reduce motion" setting for every animation in the app. */}
      <MotionConfig reducedMotion="user">
        <TooltipProvider>{children}</TooltipProvider>
      </MotionConfig>
    </ThemeProvider>
  );
}
