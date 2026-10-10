"use client";

import { CircleCheckIcon, CircleXIcon } from "lucide-react";

import { isCasePassed, type MetricResult, type RunSummary } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const pct = (v: number) => `${Math.round(v * 100)}%`;
const ms = (v: number) => (v >= 1000 ? `${(v / 1000).toFixed(1)}s` : `${Math.round(v)}ms`);

function StatTile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card size="sm">
      <CardContent className="flex flex-col gap-1">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="text-3xl font-semibold tracking-tight tabular-nums">{value}</span>
        {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
      </CardContent>
    </Card>
  );
}

/** Status: always icon + label, never color alone. */
function PassBadge({ passed }: { passed: boolean }) {
  return passed ? (
    <Badge className="bg-emerald-600/10 text-emerald-700 dark:bg-emerald-400/15 dark:text-emerald-300">
      <CircleCheckIcon /> Pass
    </Badge>
  ) : (
    <Badge variant="destructive">
      <CircleXIcon /> Fail
    </Badge>
  );
}

/** Single-series horizontal bars (0–1). One hue, values at the tip, hover for detail. */
function MetricBars({ scores, results }: { scores: Record<string, number>; results: RunSummary["results"] }) {
  const entries = Object.entries(scores);
  return (
    <Card>
      <CardHeader>
        <CardTitle>Mean score by metric</CardTitle>
        <CardDescription>0 = always fails, 1 = always passes. Hover a bar for details.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-1">
        {entries.length === 0 && (
          <p className="text-sm text-muted-foreground">No metric applied to these cases.</p>
        )}
        {entries.map(([name, score]) => {
          const applied = results.filter((r) => r.metrics.some((m) => m.name === name));
          const passed = applied.filter((r) => r.metrics.find((m) => m.name === name)?.passed);
          return (
            <Tooltip key={name}>
              <TooltipTrigger
                render={
                  <div className="grid grid-cols-[8.5rem_1fr_3rem] items-center gap-3 rounded-md px-1 py-2 hover:bg-muted/60" />
                }
              >
                <span className="truncate font-mono text-[13px]">{name}</span>
                <span className="h-2.5 w-full rounded-r-[4px] bg-muted">
                  <span
                    className="block h-full rounded-r-[4px] bg-primary"
                    style={{ width: `${Math.max(score * 100, score > 0 ? 1 : 0)}%` }}
                  />
                </span>
                <span className="text-right font-mono text-sm tabular-nums">
                  {score.toFixed(2)}
                </span>
              </TooltipTrigger>
              <TooltipContent>
                {name}: mean {score.toFixed(3)} · passed {passed.length}/{applied.length} cases
              </TooltipContent>
            </Tooltip>
          );
        })}
      </CardContent>
    </Card>
  );
}

function MetricChip({ m }: { m: MetricResult }) {
  return (
    <Tooltip>
      <TooltipTrigger render={<span />}>
        <Badge variant={m.passed ? "outline" : "destructive"} className="font-mono">
          {m.passed ? <CircleCheckIcon /> : <CircleXIcon />}
          {m.name}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        score {m.score.toFixed(2)}
        {m.reason && ` · ${m.reason}`}
      </TooltipContent>
    </Tooltip>
  );
}

export function RunSummaryView({ summary }: { summary: RunSummary }) {
  const passed = summary.results.filter(isCasePassed).length;
  const tokens = summary.results.reduce(
    (n, r) => n + r.trace.input_tokens + r.trace.output_tokens,
    0,
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-xl font-semibold">
          Run <span className="font-mono">{summary.run_id}</span>
        </h2>
        <span className="text-sm text-muted-foreground">
          agent <span className="font-medium text-foreground">{summary.agent}</span> ·{" "}
          {new Date(summary.created_at).toLocaleString()}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Pass rate" value={pct(summary.pass_rate)} hint={`${passed} of ${summary.num_cases} cases`} />
        <StatTile label="Cases" value={String(summary.num_cases)} />
        <StatTile label="Mean latency" value={ms(summary.mean_latency_ms)} />
        <StatTile label="Tokens used" value={tokens.toLocaleString()} />
      </div>

      <MetricBars scores={summary.mean_scores} results={summary.results} />

      <Card>
        <CardHeader>
          <CardTitle>Cases</CardTitle>
          <CardDescription>A case passes only when every metric that applies passes.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Case</TableHead>
                <TableHead>Result</TableHead>
                <TableHead>Agent output</TableHead>
                <TableHead>Tools called</TableHead>
                <TableHead>Metrics</TableHead>
                <TableHead className="text-right">Latency</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {summary.results.map((r) => (
                <TableRow key={r.case_id}>
                  <TableCell className="font-mono text-[13px]">{r.case_id}</TableCell>
                  <TableCell>
                    <PassBadge passed={isCasePassed(r)} />
                  </TableCell>
                  <TableCell className="max-w-72 truncate" title={r.trace.output}>
                    {r.trace.error ? (
                      <span className="text-destructive">{r.trace.error}</span>
                    ) : (
                      r.trace.output || <span className="text-muted-foreground">(empty)</span>
                    )}
                  </TableCell>
                  <TableCell className="font-mono text-[13px]">
                    {r.trace.tool_calls.length
                      ? r.trace.tool_calls.map((t) => t.name).join(" → ")
                      : <span className="text-muted-foreground">none</span>}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {r.metrics.map((m) => (
                        <MetricChip key={m.name} m={m} />
                      ))}
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-mono text-[13px] tabular-nums">
                    {ms(r.trace.latency_ms)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
