"use client";

import { useState } from "react";
import { Loader2Icon, PlayIcon } from "lucide-react";

import type { Catalog, RunRequest } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const DEFAULT_EVALUATORS = ["contains", "tool_sequence", "latency", "no_error"];
const NEEDS_API_KEY = new Set(["claude", "llm_judge"]);

type Props = {
  catalog: Catalog;
  running: boolean;
  onRun: (req: RunRequest) => void;
};

export function RunForm({ catalog, running, onRun }: Props) {
  const [agent, setAgent] = useState(catalog.agents.includes("echo") ? "echo" : catalog.agents[0]);
  const [dataset, setDataset] = useState(catalog.datasets[0] ?? "");
  const [evaluators, setEvaluators] = useState<string[]>(
    DEFAULT_EVALUATORS.filter((e) => catalog.evaluators.includes(e)),
  );

  const toggle = (name: string, checked: boolean) =>
    setEvaluators((prev) => (checked ? [...prev, name] : prev.filter((e) => e !== name)));

  const canRun = !running && agent && dataset && evaluators.length > 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle>New evaluation</CardTitle>
        <CardDescription>Pick an agent, a dataset and how to score it.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <Label>Agent</Label>
          <Select value={agent} onValueChange={(v) => v && setAgent(v)}>
            <SelectTrigger className="w-full">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {catalog.agents.map((a) => (
                <SelectItem key={a} value={a}>
                  {a}
                  {NEEDS_API_KEY.has(a) && (
                    <span className="text-muted-foreground"> (needs API key)</span>
                  )}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="flex flex-col gap-2">
          <Label>Dataset</Label>
          <Select value={dataset} onValueChange={(v) => v && setDataset(v)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="No datasets found" />
            </SelectTrigger>
            <SelectContent>
              {catalog.datasets.map((d) => (
                <SelectItem key={d} value={d}>
                  {d}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <fieldset className="flex flex-col gap-2.5">
          <legend className="mb-2.5 text-sm font-medium">Evaluators</legend>
          {catalog.evaluators.map((e) => (
            <Label key={e} className="flex items-center gap-2.5 font-normal">
              <Checkbox
                checked={evaluators.includes(e)}
                onCheckedChange={(checked) => toggle(e, checked)}
              />
              <span className="font-mono text-[13px]">{e}</span>
              {NEEDS_API_KEY.has(e) && (
                <span className="text-xs text-muted-foreground">needs API key</span>
              )}
            </Label>
          ))}
        </fieldset>

        <Button
          disabled={!canRun}
          onClick={() => onRun({ agent, dataset, evaluators })}
          className="w-full"
        >
          {running ? <Loader2Icon className="animate-spin" /> : <PlayIcon />}
          {running ? "Running…" : "Run evaluation"}
        </Button>
      </CardContent>
    </Card>
  );
}
