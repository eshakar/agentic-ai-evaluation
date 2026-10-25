"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { HistoryIcon, PlayIcon, SearchIcon } from "lucide-react";

import { api, type RunListItem } from "@/lib/api";
import { BackendError } from "@/components/backend-error";
import { ButtonLink } from "@/components/button-link";
import { PageHeader } from "@/components/page-header";
import { RunsList } from "@/components/runs-list";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export function RunsView() {
  const [runs, setRuns] = useState<RunListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const load = useCallback(
    () =>
      api
        .runs(500)
        .then((r) => {
          setRuns(r);
          setError(null);
        })
        .catch((e: Error) => setError(e.message)),
    [],
  );

  useEffect(() => {
    load();
  }, [load]);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!runs || !q) return runs;
    return runs.filter((r) => r.agent.toLowerCase().includes(q) || r.run_id.includes(q));
  }, [runs, query]);

  return (
    <>
      <PageHeader
        icon={<HistoryIcon />}
        title="Past runs"
        description="Every evaluation you've run, newest first. Open one to see its full report card."
        actions={
          <ButtonLink href="/evaluate">
            <PlayIcon />
            New evaluation
          </ButtonLink>
        }
      />
      {error && <BackendError message={error} onRetry={load} />}
      {runs && runs.length > 0 && (
        <div className="relative mb-4 max-w-sm">
          <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            aria-label="Filter runs by agent or id"
            placeholder="Filter by agent or run id"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-8"
          />
        </div>
      )}
      {runs === null ? (
        !error && (
          <div className="flex flex-col gap-2">
            {[0, 1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-[4.25rem] w-full rounded-xl" />
            ))}
          </div>
        )
      ) : runs.length === 0 ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center text-sm text-muted-foreground">
          No runs yet.
          <ButtonLink href="/evaluate" variant="outline">
            <PlayIcon />
            Run your first evaluation
          </ButtonLink>
        </div>
      ) : shown && shown.length === 0 ? (
        <p className="p-8 text-center text-sm text-muted-foreground">
          No runs match &ldquo;{query}&rdquo;.
        </p>
      ) : (
        <>
          <p className="mb-2 text-xs text-muted-foreground">
            {shown!.length} of {runs.length} {runs.length === 1 ? "run" : "runs"}
          </p>
          <RunsList
            runs={shown!}
            onDeleted={(id) => setRuns((prev) => prev?.filter((r) => r.run_id !== id) ?? null)}
          />
        </>
      )}
    </>
  );
}
