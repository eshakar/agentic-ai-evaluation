"use client";

import { useSyncExternalStore } from "react";
import { useTheme } from "next-themes";

import ShinyText, { type ShinyTextProps } from "@/components/reactbits/ShinyText";
import SpotlightCard, { type SpotlightCardProps } from "@/components/reactbits/SpotlightCard";

/** "light" | "dark" once mounted (the theme is unknown during server render). */
function useIsDark() {
  const { resolvedTheme } = useTheme();
  const mounted = useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
  return mounted ? resolvedTheme === "dark" : false;
}

/** React Bits SpotlightCard that follows the app's light/dark theme. */
export function ThemedSpotlightCard(props: Omit<SpotlightCardProps, "theme">) {
  const dark = useIsDark();
  return <SpotlightCard {...props} theme={dark ? "dark" : "light"} />;
}

/** React Bits ShinyText with colors that stay readable in both themes. */
export function ThemedShinyText(props: Omit<ShinyTextProps, "color" | "shineColor">) {
  const dark = useIsDark();
  return (
    <ShinyText
      {...props}
      color={dark ? "#a3a3a3" : "#525252"}
      shineColor={dark ? "#ffffff" : "#0a0a0a"}
    />
  );
}
