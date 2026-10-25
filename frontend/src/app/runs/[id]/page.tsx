import { Suspense } from "react";
import type { Metadata } from "next";

import { RunDetailView } from "@/components/views/run-detail-view";
import { Skeleton } from "@/components/ui/skeleton";

export const metadata: Metadata = { title: "Run report" };

// Reading the URL's id is request-time data, so (with cacheComponents on) it
// must sit inside a Suspense boundary; the skeleton shows while it resolves.
export default function RunPage({ params }: PageProps<"/runs/[id]">) {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full rounded-xl" />}>
      <RunDetailView params={params} />
    </Suspense>
  );
}
