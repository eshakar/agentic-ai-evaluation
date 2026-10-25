"use client";

import { useState } from "react";
import { Loader2Icon, Trash2Icon } from "lucide-react";

import { api } from "@/lib/api";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";

type Props = {
  runId: string;
  agent?: string;
  onDeleted: () => void;
  /** "icon" for compact lists, "full" for a labelled button. */
  variant?: "icon" | "full";
};

/** Deletes a run after an in-app confirmation (never a blocking browser confirm()). */
export function DeleteRunButton({ runId, agent, onDeleted, variant = "full" }: Props) {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirm = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.deleteRun(runId);
      setOpen(false);
      onDeleted();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      {variant === "icon" ? (
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Delete run ${runId}`}
          className="text-muted-foreground hover:text-destructive"
          onClick={() => setOpen(true)}
        >
          <Trash2Icon />
        </Button>
      ) : (
        <Button variant="destructive" onClick={() => setOpen(true)}>
          <Trash2Icon />
          Delete run
        </Button>
      )}

      <AlertDialog
        open={open}
        onOpenChange={(next) => {
          if (!busy) {
            setOpen(next);
            setError(null);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this run?</AlertDialogTitle>
            <AlertDialogDescription>
              Run <span className="font-mono">{runId}</span>
              {agent ? ` (agent ${agent})` : ""} and its report card will be permanently deleted.
              This can&apos;t be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <AlertDialogFooter>
            <AlertDialogCancel disabled={busy}>Cancel</AlertDialogCancel>
            <AlertDialogAction variant="destructive" onClick={confirm} disabled={busy}>
              {busy ? <Loader2Icon className="animate-spin" /> : <Trash2Icon />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
