import Link from "next/link";

import { Button } from "@/components/ui/button";

type Props = Omit<React.ComponentProps<typeof Button>, "render" | "nativeButton"> & {
  href: string;
};

/** A Next.js link styled as a button (Base UI needs nativeButton={false} for non-<button> roots). */
export function ButtonLink({ href, ...props }: Props) {
  return <Button nativeButton={false} render={<Link href={href} />} {...props} />;
}
