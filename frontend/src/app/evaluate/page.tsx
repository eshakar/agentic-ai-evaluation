import type { Metadata } from "next";

import { EvaluateView } from "@/components/views/evaluate-view";

export const metadata: Metadata = { title: "Evaluate" };

export default function EvaluatePage() {
  return <EvaluateView />;
}
