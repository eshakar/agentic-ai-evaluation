"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion } from "motion/react";
import { KeyRoundIcon, Loader2Icon, LockIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

/** Only same-site paths, so a crafted ?next= link can't send you to another website. */
function safeNext(next: string | null): string {
  return next && next.startsWith("/") && !next.startsWith("//") && !next.startsWith("/\\")
    ? next
    : "/";
}

export function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!key.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        setError(body?.detail ?? "Login failed.");
        return;
      }
      router.replace(safeNext(params.get("next")));
      router.refresh();
    } catch {
      setError("Cannot reach the server. Check your connection.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.35 }}
      className="w-full max-w-sm"
    >
      <Card>
        <CardHeader className="text-center">
          <span className="mx-auto mb-2 grid size-12 place-items-center rounded-xl bg-primary text-primary-foreground">
            <LockIcon className="size-5" />
          </span>
          <CardTitle className="text-xl">Log in to Agent Eval</CardTitle>
          <CardDescription>This site is private. Enter the access key to continue.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label htmlFor="access-key">Access key</Label>
              <div className="relative">
                <KeyRoundIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  id="access-key"
                  type="password"
                  autoComplete="current-password"
                  autoFocus
                  value={key}
                  onChange={(e) => setKey(e.target.value)}
                  className="pl-8"
                  aria-invalid={error ? true : undefined}
                  aria-describedby={error ? "login-error" : undefined}
                />
              </div>
              {error && (
                <p id="login-error" role="alert" className="text-sm text-destructive">
                  {error}
                </p>
              )}
            </div>
            <Button type="submit" size="lg" disabled={busy || !key.trim()}>
              {busy && <Loader2Icon className="animate-spin" />}
              Log in
            </Button>
          </form>
        </CardContent>
      </Card>
    </motion.div>
  );
}
