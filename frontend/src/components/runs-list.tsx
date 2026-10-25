"use client";

import Link from "next/link";
import { AnimatePresence, motion } from "motion/react";
import { ChevronRightIcon } from "lucide-react";

import type { RunListItem } from "@/lib/api";
import { cn } from "@/lib/utils";
import { DeleteRunButton } from "@/components/delete-run-button";

function PassRing({ rate }: { rate: number }) {
  const pct = Math.round(rate * 100);
  const r = 16;
  const c = 2 * Math.PI * r;
  return (
    <span className="relative grid size-11 shrink-0 place-items-center" title={`Pass rate ${pct}%`}>
      <svg viewBox="0 0 40 40" className="absolute inset-0 -rotate-90" aria-hidden>
        <circle cx="20" cy="20" r={r} fill="none" strokeWidth="3.5" className="stroke-muted" />
        <motion.circle
          cx="20"
          cy="20"
          r={r}
          fill="none"
          strokeWidth="3.5"
          strokeLinecap="round"
          className="stroke-primary"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: c * (1 - rate) }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <span className="text-[11px] font-semibold tabular-nums">{pct}%</span>
    </span>
  );
}

type Props = {
  runs: RunListItem[];
  /** Called with the run id after it is deleted, so the parent can drop it. */
  onDeleted?: (runId: string) => void;
  compact?: boolean;
};

export function RunsList({ runs, onDeleted, compact = false }: Props) {
  return (
    <ul className="flex flex-col gap-2">
      <AnimatePresence initial={false}>
        {runs.map((r, i) => (
          <motion.li
            key={r.run_id}
            layout
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0, transition: { delay: Math.min(i, 10) * 0.03 } }}
            exit={{ opacity: 0, x: -24, height: 0, marginBottom: -8, transition: { duration: 0.25 } }}
          >
            {/* The delete button is a sibling of the link, not inside it, so clicks in its
                confirmation dialog can't bubble up and trigger navigation. */}
            <div className="flex items-center gap-1 rounded-xl border bg-card pr-2 transition-colors hover:border-foreground/20 hover:bg-muted/40">
              <Link
                href={`/runs/${r.run_id}`}
                className={cn(
                  "group flex min-w-0 flex-1 items-center gap-4 rounded-xl px-4",
                  compact ? "py-2.5" : "py-3",
                )}
              >
                <PassRing rate={r.pass_rate} />
                <span className="flex min-w-0 flex-1 flex-col">
                  <span className="flex items-center gap-2">
                    <span className="font-medium">{r.agent}</span>
                    <span className="truncate font-mono text-xs text-muted-foreground">
                      {r.run_id}
                    </span>
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(r.created_at).toLocaleString()} · {r.num_cases}{" "}
                    {r.num_cases === 1 ? "question" : "questions"}
                  </span>
                </span>
                <ChevronRightIcon className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
              </Link>
              {onDeleted && (
                <DeleteRunButton
                  variant="icon"
                  runId={r.run_id}
                  agent={r.agent}
                  onDeleted={() => onDeleted(r.run_id)}
                />
              )}
            </div>
          </motion.li>
        ))}
      </AnimatePresence>
    </ul>
  );
}
