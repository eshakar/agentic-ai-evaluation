import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { Providers } from "@/components/providers";
import { SiteNav } from "@/components/site-nav";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: { default: "Agent Eval", template: "%s · Agent Eval" },
  description: "Ask AI agents questions, run evaluations and inspect their scores.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-background">
        <Providers>
          <SiteNav />
          <main className="mx-auto flex w-full max-w-7xl flex-1 flex-col px-4 py-8 sm:px-6">
            {children}
          </main>
          <footer className="border-t py-6 text-center text-xs text-muted-foreground">
            Agentic AI Evaluation · FastAPI + Next.js
          </footer>
        </Providers>
      </body>
    </html>
  );
}
