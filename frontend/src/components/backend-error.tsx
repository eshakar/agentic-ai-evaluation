"use client";

import { CircleAlertIcon } from "lucide-react";

import { Alert, AlertAction, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";

export function BackendError({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Alert variant="destructive">
      <CircleAlertIcon />
      <AlertTitle>Something went wrong</AlertTitle>
      <AlertDescription>{message}</AlertDescription>
      {onRetry && (
        <AlertAction>
          <Button size="sm" variant="outline" onClick={onRetry}>
            Retry
          </Button>
        </AlertAction>
      )}
    </Alert>
  );
}
