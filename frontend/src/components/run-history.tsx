"use client";

import type { RunListItem } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Props = {
  runs: RunListItem[];
  selectedId: string | null;
  onSelect: (runId: string) => void;
};

export function RunHistory({ runs, selectedId, onSelect }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Past runs</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        {runs.length === 0 && (
          <p className="text-sm text-muted-foreground">No runs yet. Start one above.</p>
        )}
        {runs.map((r) => (
          <button
            key={r.run_id}
            onClick={() => onSelect(r.run_id)}
            className={cn(
              "flex items-center justify-between rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-muted",
              selectedId === r.run_id && "bg-muted",
            )}
          >
            <span className="flex flex-col">
              <span className="font-medium">{r.agent}</span>
              <span className="text-xs text-muted-foreground">
                {new Date(r.created_at).toLocaleString()} · {r.num_cases} cases
              </span>
            </span>
            <span className="font-mono text-sm tabular-nums">
              {Math.round(r.pass_rate * 100)}%
            </span>
          </button>
        ))}
      </CardContent>
    </Card>
  );
}
