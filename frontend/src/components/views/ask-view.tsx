"use client";

import { MessageSquareTextIcon } from "lucide-react";

import { AskPanel } from "@/components/ask-panel";
import { BackendError } from "@/components/backend-error";
import { PageHeader } from "@/components/page-header";
import { useCatalog } from "@/components/use-catalog";
import { Skeleton } from "@/components/ui/skeleton";

export function AskView() {
  const { catalog, error, reload } = useCatalog();
  return (
    <>
      <PageHeader
        icon={<MessageSquareTextIcon />}
        title="Ask an agent"
        description="Try any question and see exactly how the agent answers it. Add checks to grade it, then save the good ones to a dataset."
      />
      {error && <BackendError message={error} onRetry={reload} />}
      {catalog ? (
        <AskPanel catalog={catalog} />
      ) : (
        !error && <Skeleton className="h-[32rem] w-full rounded-xl" />
      )}
    </>
  );
}
