"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "motion/react";
import {
  ArrowRightIcon,
  HistoryIcon,
  MessageSquareTextIcon,
  PlayIcon,
  SparklesIcon,
} from "lucide-react";

import { api, type Catalog, type RunListItem } from "@/lib/api";
import BlurText from "@/components/reactbits/BlurText";
import CountUp from "@/components/reactbits/CountUp";
import { RunsList } from "@/components/runs-list";
import { ThemedShinyText, ThemedSpotlightCard } from "@/components/themed";
import { ButtonLink } from "@/components/button-link";
import { Skeleton } from "@/components/ui/skeleton";

const FEATURES = [
  {
    href: "/ask",
    icon: MessageSquareTextIcon,
    title: "Ask",
    body: "Type any question, watch the agent use its tools, and grade the answer with an AI judge. Save good questions to a dataset.",
  },
  {
    href: "/evaluate",
    icon: PlayIcon,
    title: "Evaluate",
    body: "Run an agent over a whole dataset and get a report card: pass rate, a score per check, and every answer.",
  },
  {
    href: "/runs",
    icon: HistoryIcon,
    title: "Past runs",
    body: "Open any earlier report card to compare results over time, or delete runs you no longer need.",
  },
];

function Stat({ label, value, suffix }: { label: string; value: number | null; suffix?: string }) {
  return (
    <div className="flex flex-col gap-1 rounded-xl border bg-card px-5 py-4">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-3xl font-semibold tracking-tight tabular-nums">
        {value === null ? (
          <Skeleton className="h-9 w-16" />
        ) : (
          <CountUp to={value} duration={1.2} suffix={suffix} />
        )}
      </span>
    </div>
  );
}

export function HomeView() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [runs, setRuns] = useState<RunListItem[] | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    Promise.all([api.catalog(), api.runs()])
      .then(([c, r]) => {
        setCatalog(c);
        setRuns(r);
      })
      .catch(() => setOffline(true));
  }, []);

  const avgPass =
    runs && runs.length
      ? Math.round((runs.reduce((n, r) => n + r.pass_rate, 0) / runs.length) * 100)
      : runs
        ? 0
        : null;

  return (
    <div className="flex flex-col gap-14">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl border px-6 py-16 text-center sm:px-12 sm:py-20">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(60%_80%_at_50%_0%,color-mix(in_oklch,var(--foreground)_10%,transparent),transparent_70%)]"
        />
        <motion.div
          aria-hidden
          className="pointer-events-none absolute -top-24 left-1/2 -z-10 size-[28rem] -translate-x-1/2 rounded-full bg-[conic-gradient(from_90deg,oklch(0.7_0.15_250/.25),oklch(0.75_0.15_160/.25),oklch(0.7_0.17_300/.25),oklch(0.7_0.15_250/.25))] blur-3xl"
          animate={{ rotate: 360 }}
          transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
        />
        <div className="mx-auto mb-5 inline-flex items-center gap-2 rounded-full border bg-background/60 px-3 py-1 text-xs backdrop-blur">
          <SparklesIcon className="size-3.5" />
          <ThemedShinyText text="Agentic AI Evaluation" speed={3} />
        </div>
        {/* BlurText renders a <p>, so the real heading is this h1; the animation is decorative. */}
        <h1 className="sr-only">Know whether your AI agent really works</h1>
        <div aria-hidden>
        <BlurText
          text="Know whether your AI agent really works"
          animateBy="words"
          direction="top"
          delay={90}
          className="mx-auto flex max-w-3xl flex-wrap justify-center text-4xl font-semibold tracking-tight sm:text-6xl"
        />
        </div>
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7, duration: 0.5 }}
          className="mx-auto mt-5 max-w-xl text-muted-foreground sm:text-lg"
        >
          Ask questions, check the tools it uses, and score its answers with tests and an AI
          judge, for Claude and Gemini agents side by side.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.85, duration: 0.5 }}
          className="mt-8 flex flex-wrap justify-center gap-3"
        >
          <ButtonLink size="lg" href="/ask">
            <MessageSquareTextIcon />
            Ask a question
          </ButtonLink>
          <ButtonLink size="lg" variant="outline" href="/evaluate">
            <PlayIcon />
            Run an evaluation
          </ButtonLink>
        </motion.div>
      </section>

      {offline && (
        <p className="-mt-8 text-center text-sm text-destructive">
          The backend isn&apos;t reachable, so live stats can&apos;t load. Start it with{" "}
          <code className="font-mono">uvicorn app.main:app --port 8000</code> in the backend folder.
        </p>
      )}

      {/* Stats */}
      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4" aria-label="Overview">
        <Stat label="Runs saved" value={runs ? runs.length : null} />
        <Stat label="Average pass rate" value={avgPass} suffix="%" />
        <Stat label="Agents" value={catalog ? catalog.agents.length : null} />
        <Stat label="Datasets" value={catalog ? catalog.datasets.length : null} />
      </section>

      {/* Features */}
      <section className="grid gap-4 md:grid-cols-3">
        {FEATURES.map(({ href, icon: Icon, title, body }, i) => (
          <motion.div
            key={href}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: i * 0.08, duration: 0.45 }}
            whileHover={{ y: -4 }}
          >
            <Link href={href} className="block h-full rounded-3xl focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none">
              <ThemedSpotlightCard className="h-full border">
                <span className="mb-4 grid size-10 place-items-center rounded-xl bg-primary text-primary-foreground">
                  <Icon className="size-5" />
                </span>
                <h2 className="text-lg font-semibold">{title}</h2>
                <p className="mt-1.5 text-sm text-muted-foreground">{body}</p>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium">
                  Open <ArrowRightIcon className="size-4" />
                </span>
              </ThemedSpotlightCard>
            </Link>
          </motion.div>
        ))}
      </section>

      {/* Recent runs */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Latest runs</h2>
          <ButtonLink variant="ghost" size="sm" href="/runs">
            See all <ArrowRightIcon />
          </ButtonLink>
        </div>
        {runs === null ? (
          !offline && <Skeleton className="h-36 w-full rounded-xl" />
        ) : runs.length === 0 ? (
          <p className="rounded-xl border border-dashed p-8 text-center text-sm text-muted-foreground">
            No runs yet. <Link href="/evaluate" className="underline">Run your first evaluation</Link>.
          </p>
        ) : (
          <RunsList runs={runs.slice(0, 3)} compact />
        )}
      </section>
    </div>
  );
}
