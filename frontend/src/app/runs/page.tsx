import type { Metadata } from "next";

import { RunsView } from "@/components/views/runs-view";

export const metadata: Metadata = { title: "Past runs" };

export default function RunsPage() {
  return <RunsView />;
}
