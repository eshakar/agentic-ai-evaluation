"use client";

import { useCallback, useEffect, useState } from "react";
import { CircleAlertIcon, FlaskConicalIcon } from "lucide-react";

import { api, API_URL, type Catalog, type RunListItem, type RunRequest, type RunSummary } from "@/lib/api";
import { RunForm } from "@/components/run-form";
import { RunHistory } from "@/components/run-history";
import { RunSummaryView } from "@/components/run-summary";
import { ThemeToggle } from "@/components/theme-toggle";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function Dashboard() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [runs, setRuns] = useState<RunListItem[]>([]);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshRuns = useCallback(() => api.runs().then(setRuns), []);

  useEffect(() => {
    Promise.all([api.catalog(), api.runs()])
      .then(([c, r]) => {
        setCatalog(c);
        setRuns(r);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const handleRun = async (req: RunRequest) => {
    setRunning(true);
    setError(null);
    try {
      setSummary(await api.run(req));
      await refreshRuns();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setRunning(false);
    }
  };

  const handleSelect = async (runId: string) => {
    setError(null);
    try {
      setSummary(await api.getRun(runId));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  return (
    <div className="min-h-full bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <FlaskConicalIcon className="size-5" />
            <div>
              <h1 className="font-semibold leading-tight">Agentic AI Evaluation</h1>
              <p className="text-xs text-muted-foreground">Backend: {API_URL}</p>
            </div>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[20rem_1fr]">
        <aside className="flex flex-col gap-6">
          {catalog ? (
            <RunForm catalog={catalog} running={running} onRun={handleRun} />
          ) : (
            !error && <Skeleton className="h-96 w-full rounded-xl" />
          )}
          <RunHistory runs={runs} selectedId={summary?.run_id ?? null} onSelect={handleSelect} />
        </aside>

        <section className="flex min-w-0 flex-col gap-4">
          {error && (
            <Alert variant="destructive">
              <CircleAlertIcon />
              <AlertTitle>Something went wrong</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {summary ? (
            <RunSummaryView summary={summary} />
          ) : (
            <Card className="border-dashed">
              <CardContent className="py-16 text-center text-muted-foreground">
                Run an evaluation or pick a past run to see its report card here.
              </CardContent>
            </Card>
          )}
        </section>
      </main>
    </div>
  );
}
