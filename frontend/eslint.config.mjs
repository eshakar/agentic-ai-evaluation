import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Vendored React Bits components (added with `npx shadcn add https://reactbits.dev/r/...`).
  // They keep the latest props in a ref during render, which these React Compiler rules
  // flag. The React Compiler is not enabled here, so they work as published; relaxing the
  // two rules for this folder only keeps the vendor code identical to upstream.
  {
    files: ["src/components/reactbits/**"],
    rules: {
      "react-hooks/refs": "off",
      "react-hooks/set-state-in-effect": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
