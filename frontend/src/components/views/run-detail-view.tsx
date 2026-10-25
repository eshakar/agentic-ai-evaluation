"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeftIcon, FileQuestionIcon } from "lucide-react";

import { api, type RunSummary } from "@/lib/api";
import { BackendError } from "@/components/backend-error";
import { ButtonLink } from "@/components/button-link";
import { DeleteRunButton } from "@/components/delete-run-button";
import { RunSummaryView } from "@/components/run-summary";
import { Skeleton } from "@/components/ui/skeleton";

export function RunDetailView({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let alive = true;
    api
      .getRun(id)
      .then((s) => alive && setSummary(s))
      .catch((e: Error) => {
        if (!alive) return;
        if (e.message.startsWith("404")) setNotFound(true);
        else setError(e.message);
      });
    return () => {
      alive = false;
    };
  }, [id]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <ButtonLink href="/runs" variant="ghost" size="sm">
          <ArrowLeftIcon />
          All runs
        </ButtonLink>
        {summary && (
          <DeleteRunButton
            runId={summary.run_id}
            agent={summary.agent}
            onDeleted={() => router.push("/runs")}
          />
        )}
      </div>

      {error && <BackendError message={error} />}
      {notFound ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed p-12 text-center">
          <FileQuestionIcon className="size-8 text-muted-foreground" />
          <p className="font-medium">
            Run <span className="font-mono">{id}</span> doesn&apos;t exist
          </p>
          <p className="text-sm text-muted-foreground">It may have been deleted.</p>
          <ButtonLink href="/runs" variant="outline">
            Back to past runs
          </ButtonLink>
        </div>
      ) : summary ? (
        <RunSummaryView summary={summary} />
      ) : (
        !error && <Skeleton className="h-96 w-full rounded-xl" />
      )}
    </div>
  );
}
