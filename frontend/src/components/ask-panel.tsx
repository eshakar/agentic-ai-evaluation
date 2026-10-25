"use client";

import { useId, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  BookmarkPlusIcon,
  CircleAlertIcon,
  CircleCheckIcon,
  CircleXIcon,
  GavelIcon,
  Loader2Icon,
  SendIcon,
  WrenchIcon,
} from "lucide-react";

import {
  api,
  formatMs,
  type AskResponse,
  type Catalog,
  type MetricResult,
  type SaveCaseResponse,
} from "@/lib/api";
import { cn } from "@/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

const EXAMPLES = [
  { q: "What is 4,872 multiplied by 391?", expected: "1904952", tools: ["calculator"] },
  { q: "What year is it right now in UTC?", tools: ["current_utc_time"] },
  { q: "What is the capital of Japan?", expected: "Tokyo", tools: [] as string[] },
  {
    q: "Explain in one sentence what an API is.",
    tools: [] as string[],
    rubric: "One accurate sentence: an API is a defined way for programs to talk to each other.",
  },
];

const METRIC_LABELS: Record<string, string> = {
  no_error: "Finished without errors",
  exact_match: "Exactly the expected answer",
  contains: "Contains the expected answer",
  tool_sequence: "Used the expected tools",
  llm_judge: "AI judge",
};

/** Models often mark key words as **bold**; show that as bold text (as React text, never raw HTML). */
function WithBold({ text }: { text: string }) {
  return text
    .split(/(\*\*[^*]+\*\*)/g)
    .map((part, i) =>
      part.startsWith("**") && part.endsWith("**") && part.length > 4 ? (
        <strong key={i}>{part.slice(2, -2)}</strong>
      ) : (
        part
      ),
    );
}

/** Expected tools: null = don't check; [] = should use none; [...] = these, in this order. */
function ToolPicker({
  tools,
  value,
  onChange,
}: {
  tools: string[];
  value: string[] | null;
  onChange: (v: string[] | null) => void;
}) {
  const chip = (active: boolean) =>
    cn(
      "rounded-full border px-3 py-1 text-xs transition-colors",
      active
        ? "border-primary bg-primary text-primary-foreground"
        : "text-muted-foreground hover:bg-muted hover:text-foreground",
    );
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      <button type="button" className={chip(value === null)} onClick={() => onChange(null)}>
        Don&apos;t check
      </button>
      <button
        type="button"
        className={chip(value !== null && value.length === 0)}
        onClick={() => onChange([])}
      >
        No tools
      </button>
      {tools.map((t) => {
        const pos = value?.indexOf(t) ?? -1;
        return (
          <button
            key={t}
            type="button"
            aria-pressed={pos >= 0}
            className={cn(chip(pos >= 0), "font-mono")}
            onClick={() =>
              onChange(pos >= 0 ? value!.filter((x) => x !== t) : [...(value ?? []), t])
            }
          >
            {pos >= 0 && <span className="mr-1 font-sans font-semibold">{pos + 1}.</span>}
            {t}
          </button>
        );
      })}
    </div>
  );
}

export function AskPanel({ catalog }: { catalog: Catalog }) {
  const ids = useId();
  const preferred = ["gemini", "claude"].find((a) => catalog.agents.includes(a));
  const [agent, setAgent] = useState(preferred ?? catalog.agents[0]);
  const [question, setQuestion] = useState("");
  const [expected, setExpected] = useState("");
  const [expectedTools, setExpectedTools] = useState<string[] | null>(null);
  const [rubric, setRubric] = useState("");
  const [useJudge, setUseJudge] = useState(false);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ask = async () => {
    if (!question.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      setResult(
        await api.ask({
          agent,
          question: question.trim(),
          expected_output: expected.trim() || undefined,
          expected_tools: expectedTools,
          rubric: rubric.trim() || undefined,
          use_judge: useJudge,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const loadExample = (ex: (typeof EXAMPLES)[number]) => {
    setQuestion(ex.q);
    setExpected(ex.expected ?? "");
    setExpectedTools(ex.tools ?? null);
    setRubric(ex.rubric ?? "");
    setUseJudge(Boolean(ex.rubric));
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle>Your question</CardTitle>
          <CardDescription>
            Fill in only what you want checked. Every field except the question is optional.
          </CardDescription>
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
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor={`${ids}-q`}>Question</Label>
            <Textarea
              id={`${ids}-q`}
              placeholder="Type a question, then press Ask (or Ctrl+Enter)"
              value={question}
              maxLength={4000}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) ask();
              }}
            />
            <div className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
              Examples:
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.q}
                  type="button"
                  onClick={() => loadExample(ex)}
                  className="rounded-md border px-2 py-0.5 text-left hover:bg-muted"
                >
                  {ex.q}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor={`${ids}-exp`}>Expected answer</Label>
            <Input
              id={`${ids}-exp`}
              placeholder="e.g. 1904952 (leave empty for open-ended questions)"
              value={expected}
              maxLength={1000}
              onChange={(e) => setExpected(e.target.value)}
            />
          </div>

          <div className="flex flex-col gap-2">
            <Label>Tools it should use</Label>
            <ToolPicker tools={catalog.tools} value={expectedTools} onChange={setExpectedTools} />
            <p className="text-xs text-muted-foreground">
              Click tools in the order they should be used.
            </p>
          </div>

          <div className="flex flex-col gap-3 rounded-lg border p-3">
            <div className="flex items-center justify-between gap-3">
              <Label htmlFor={`${ids}-judge`} className="flex items-center gap-2">
                <GavelIcon className="size-4" /> Grade with AI judge
              </Label>
              <Switch
                id={`${ids}-judge`}
                checked={useJudge}
                onCheckedChange={(checked) => setUseJudge(checked)}
              />
            </div>
            <Textarea
              placeholder="Grading rules (optional), e.g. 'Says division by zero is undefined; does not give a number.' Without rules, the judge checks the answer is correct and complete."
              value={rubric}
              maxLength={2000}
              onChange={(e) => {
                setRubric(e.target.value);
                if (e.target.value.trim()) setUseJudge(true);
              }}
              className="min-h-14 text-sm"
            />
            <p className="text-xs text-muted-foreground">
              The judge is best for questions with no single right string. It costs one extra AI
              request.
            </p>
          </div>

          <Button onClick={ask} disabled={busy || !question.trim()} size="lg">
            {busy ? <Loader2Icon className="animate-spin" /> : <SendIcon />}
            {busy ? "Thinking…" : "Ask"}
          </Button>
        </CardContent>
      </Card>

      <div className="flex min-w-0 flex-col gap-4">
        {error && (
          <Alert variant="destructive">
            <CircleAlertIcon />
            <AlertTitle>Request failed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        <AnimatePresence mode="wait">
          {busy ? (
            <motion.div
              key="busy"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex h-64 flex-col items-center justify-center gap-3 rounded-xl border border-dashed text-sm text-muted-foreground"
            >
              <motion.span
                className="flex gap-1.5"
                initial="a"
                animate="b"
                transition={{ staggerChildren: 0.15, repeat: Infinity, repeatType: "reverse" }}
              >
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="size-2.5 rounded-full bg-foreground/60"
                    variants={{ a: { y: 0, opacity: 0.4 }, b: { y: -8, opacity: 1 } }}
                    transition={{ duration: 0.4, repeat: Infinity, repeatType: "reverse" }}
                  />
                ))}
              </motion.span>
              {agent} is working on it…
            </motion.div>
          ) : result ? (
            <motion.div
              key={result.question + result.trace.latency_ms}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex flex-col gap-4"
            >
              <AskResult result={result} />
              <SaveToDataset
                catalog={catalog}
                question={result.question}
                expected={expected}
                expectedTools={expectedTools}
                rubric={rubric}
              />
            </motion.div>
          ) : (
            <motion.div
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex h-64 items-center justify-center rounded-xl border border-dashed p-6 text-center text-sm text-muted-foreground"
            >
              The answer, the tools used and every check will appear here.
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

function MetricRow({ m }: { m: MetricResult }) {
  return (
    <li className="flex items-start gap-2 text-sm">
      {m.passed ? (
        <CircleCheckIcon className="mt-0.5 size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
      ) : (
        <CircleXIcon className="mt-0.5 size-4 shrink-0 text-destructive" />
      )}
      <span className="min-w-0">
        <span className="font-medium">{METRIC_LABELS[m.name] ?? m.name}</span>
        <span className="text-muted-foreground">
          {" "}
          · {m.passed ? "pass" : "fail"}
          {m.name === "llm_judge" && ` · score ${Math.round(m.score * 4 + 1)}/5`}
        </span>
        {m.reason && (
          <span className="block break-words text-xs text-muted-foreground">{m.reason}</span>
        )}
      </span>
    </li>
  );
}

function AskResult({ result }: { result: AskResponse }) {
  const { trace, metrics } = result;
  const allPassed = metrics.every((m) => m.passed);

  return (
    <Card aria-live="polite">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <CardTitle>
            Answer from <span className="font-mono">{result.agent}</span>
          </CardTitle>
          <span className="text-xs text-muted-foreground tabular-nums">
            {formatMs(trace.latency_ms)} · {trace.turns} {trace.turns === 1 ? "round" : "rounds"} ·{" "}
            {(trace.input_tokens + trace.output_tokens).toLocaleString()} tokens
          </span>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        {trace.error ? (
          <Alert variant="destructive">
            <CircleAlertIcon />
            <AlertTitle>The agent hit an error</AlertTitle>
            <AlertDescription className="break-words">{trace.error}</AlertDescription>
          </Alert>
        ) : (
          <p className="whitespace-pre-wrap text-base">
            {trace.output ? (
              <WithBold text={trace.output} />
            ) : (
              <span className="text-muted-foreground">(empty answer)</span>
            )}
          </p>
        )}

        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
            Tools used ({trace.tool_calls.length})
          </span>
          {trace.tool_calls.length === 0 ? (
            <span className="text-sm text-muted-foreground">None, it answered directly.</span>
          ) : (
            <ol className="flex flex-col gap-1.5">
              {trace.tool_calls.map((c, i) => (
                <motion.li
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 * i }}
                  className="flex flex-wrap items-center gap-1.5 font-mono text-[13px]"
                >
                  <WrenchIcon className="size-3.5 text-muted-foreground" />
                  <span className="font-medium">{c.name}</span>
                  <span className="text-muted-foreground">
                    ({Object.values(c.arguments).map(String).join(", ")})
                  </span>
                  <span className="text-muted-foreground">→</span>
                  <span>{c.output}</span>
                </motion.li>
              ))}
            </ol>
          )}
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium tracking-wide text-muted-foreground uppercase">
              Checks
            </span>
            {metrics.length > 1 &&
              (allPassed ? (
                <Badge className="bg-emerald-600/10 text-emerald-700 dark:bg-emerald-400/15 dark:text-emerald-300">
                  <CircleCheckIcon /> All passed
                </Badge>
              ) : (
                <Badge variant="destructive">
                  <CircleXIcon /> Some failed
                </Badge>
              ))}
          </div>
          <ul className="flex flex-col gap-2">
            {metrics.map((m) => (
              <MetricRow key={m.name} m={m} />
            ))}
          </ul>
          {metrics.length === 1 && (
            <p className="text-xs text-muted-foreground">
              Only error-checking ran. Add an expected answer, expected tools or the AI judge to
              check whether the answer is right.
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function SaveToDataset({
  catalog,
  question,
  expected,
  expectedTools,
  rubric,
}: {
  catalog: Catalog;
  question: string;
  expected: string;
  expectedTools: string[] | null;
  rubric: string;
}) {
  const ids = useId();
  const [dataset, setDataset] = useState("my_questions.jsonl");
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState<SaveCaseResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // A different question or different checks = a different case to save.
  const key = JSON.stringify([question, expected, expectedTools, rubric]);
  const [lastKey, setLastKey] = useState(key);
  if (key !== lastKey) {
    setLastKey(key);
    setSaved(null);
    setError(null);
  }

  const checkable = Boolean(expected.trim() || expectedTools !== null || rubric.trim());

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      setSaved(
        await api.saveCase({
          dataset: dataset.trim(),
          question,
          expected_output: expected.trim() || undefined,
          expected_tools: expectedTools,
          rubric: rubric.trim() || undefined,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card size="sm">
      <CardContent className="flex flex-col gap-3">
        <div className="flex items-center gap-2 font-medium">
          <BookmarkPlusIcon className="size-4" /> Save to a dataset
        </div>
        <p className="text-xs text-muted-foreground">
          Keep this question, with its checks, so every future evaluation includes it.
        </p>
        <div className="flex flex-col gap-2 sm:flex-row">
          <Input
            aria-label="Dataset file name"
            list={`${ids}-datasets`}
            value={dataset}
            onChange={(e) => {
              setDataset(e.target.value);
              setError(null);
            }}
            placeholder="my_questions.jsonl"
            className="font-mono text-sm"
          />
          <datalist id={`${ids}-datasets`}>
            {catalog.datasets.map((d) => (
              <option key={d} value={d} />
            ))}
          </datalist>
          <Button
            onClick={save}
            disabled={busy || !checkable || !dataset.trim()}
            variant="secondary"
            className="shrink-0"
          >
            {busy ? <Loader2Icon className="animate-spin" /> : <BookmarkPlusIcon />}
            Save question
          </Button>
        </div>
        {!checkable && (
          <p className="text-xs text-muted-foreground">
            To save, add at least one check: an expected answer, expected tools, or grading rules.
          </p>
        )}
        {error && <p className="text-xs text-destructive">{error}</p>}
        <AnimatePresence>
          {saved && (
            <motion.p
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-1.5 text-sm text-emerald-700 dark:text-emerald-400"
            >
              <CircleCheckIcon className="size-4" />
              Saved as <span className="font-mono">{saved.case.id}</span> in{" "}
              <span className="font-mono">{saved.dataset}</span> ({saved.total_cases}{" "}
              {saved.total_cases === 1 ? "question" : "questions"}).
            </motion.p>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  );
}
