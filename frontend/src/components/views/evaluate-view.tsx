"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import { PlayIcon } from "lucide-react";

import { api, type RunRequest } from "@/lib/api";
import { BackendError } from "@/components/backend-error";
import { PageHeader } from "@/components/page-header";
import { RunForm } from "@/components/run-form";
import { useCatalog } from "@/components/use-catalog";
import { Skeleton } from "@/components/ui/skeleton";

const STEPS = [
  "Loading the questions…",
  "The agent is answering…",
  "Running the checks…",
  "Writing the report card…",
];

export function EvaluateView() {
  const router = useRouter();
  const { catalog, error: loadError, reload } = useCatalog();
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState(0);

  const handleRun = async (req: RunRequest) => {
    setRunning(true);
    setError(null);
    setStep(0);
    // Cosmetic progress hints; the request itself is a single call.
    const timer = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 2500);
    try {
      const summary = await api.run(req);
      router.push(`/runs/${summary.run_id}`);
    } catch (e) {
      setError((e as Error).message);
      setRunning(false);
    } finally {
      clearInterval(timer);
    }
  };

  return (
    <>
      <PageHeader
        icon={<PlayIcon />}
        title="Run an evaluation"
        description="Pick an agent and a dataset. Every question is answered and checked, and you get a report card at the end."
      />
      <div className="grid gap-6 lg:grid-cols-[22rem_1fr]">
        <div>
          {catalog ? (
            <RunForm catalog={catalog} running={running} onRun={handleRun} />
          ) : (
            !loadError && <Skeleton className="h-96 w-full rounded-xl" />
          )}
        </div>
        <div className="flex min-w-0 flex-col gap-4">
          {loadError && <BackendError message={loadError} onRetry={reload} />}
          {error && <BackendError message={error} />}
          <AnimatePresence mode="wait">
            {running ? (
              <motion.div
                key="running"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="flex h-72 flex-col items-center justify-center gap-5 rounded-xl border"
              >
                <motion.span
                  className="size-12 rounded-full border-4 border-muted border-t-primary"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
                />
                <AnimatePresence mode="wait">
                  <motion.p
                    key={step}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -6 }}
                    className="text-sm text-muted-foreground"
                  >
                    {STEPS[step]}
                  </motion.p>
                </AnimatePresence>
                <p className="max-w-sm text-center text-xs text-muted-foreground">
                  Real agents can take a while: each question may involve several AI calls. You
                  will be taken to the report card when it is done.
                </p>
              </motion.div>
            ) : (
              <motion.div
                key="idle"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex h-72 flex-col items-center justify-center gap-2 rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground"
              >
                <p>
                  Start with the <span className="font-mono">echo</span> agent to see how it works
                  for free, then try a real agent.
                </p>
                <p>The finished report opens on its own page and is kept under Past runs.</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </>
  );
}
