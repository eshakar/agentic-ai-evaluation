"use client";

import { useCallback, useEffect, useState } from "react";

import { api, type Catalog } from "@/lib/api";

/** Loads agents, tools, evaluators and datasets from the backend. */
export function useCatalog() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    () =>
      api
        .catalog()
        .then((c) => {
          setCatalog(c);
          setError(null);
        })
        .catch((e: Error) => setError(e.message)),
    [],
  );

  useEffect(() => {
    load();
  }, [load]);

  return { catalog, error, reload: load };
}
