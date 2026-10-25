"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "motion/react";
import {
  FlaskConicalIcon,
  HistoryIcon,
  HouseIcon,
  LogOutIcon,
  MenuIcon,
  MessageSquareTextIcon,
  PlayIcon,
  XIcon,
} from "lucide-react";

import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";

const LINKS = [
  { href: "/", label: "Home", icon: HouseIcon },
  { href: "/ask", label: "Ask", icon: MessageSquareTextIcon },
  { href: "/evaluate", label: "Evaluate", icon: PlayIcon },
  { href: "/runs", label: "Past runs", icon: HistoryIcon },
] as const;

const isActive = (pathname: string | null, href: string) =>
  pathname !== null &&
  (href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`));

/** Small dot showing whether the FastAPI backend answers. */
function ApiStatus() {
  const [online, setOnline] = useState<boolean | null>(null);
  const [storage, setStorage] = useState<string | null>(null);
  useEffect(() => {
    let alive = true;
    const check = () =>
      api
        .health()
        .then((h) => {
          if (!alive) return;
          setOnline(true);
          setStorage(h.storage ?? null);
        })
        .catch(() => alive && setOnline(false));
    check();
    const id = setInterval(check, 15000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const label = online === null ? "Checking API…" : online ? "API online" : "API offline";
  const usingMongo = storage?.startsWith("mongodb");
  const detail = online && storage ? `${label} · data stored in ${storage}` : label;
  return (
    <span className="hidden items-center gap-1.5 text-xs text-muted-foreground sm:flex" title={detail}>
      <span className="relative flex size-2">
        {online && (
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-emerald-500 opacity-60" />
        )}
        <span
          className={cn(
            "relative inline-flex size-2 rounded-full",
            online === null ? "bg-muted-foreground/40" : online ? "bg-emerald-500" : "bg-destructive",
          )}
        />
      </span>
      {label}
      {online && storage && (
        <span
          className={cn(
            "rounded-full border px-1.5 py-px text-[10px] font-medium",
            usingMongo ? "text-foreground" : "text-amber-700 dark:text-amber-400",
          )}
        >
          {usingMongo ? "MongoDB" : "Files"}
        </span>
      )}
    </span>
  );
}

/** Shown only when login is enabled and this browser is logged in. */
function LogoutButton() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    fetch("/api/auth/status")
      .then((r) => r.json())
      .then((s: { enabled: boolean; authenticated: boolean }) => setShow(s.enabled && s.authenticated))
      .catch(() => {});
  }, []);
  if (!show) return null;
  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Log out"
      title="Log out"
      onClick={async () => {
        await fetch("/api/auth/logout", { method: "POST" });
        // A full reload on purpose: it drops every page's data held in memory.
        // eslint-disable-next-line @next/next/no-location-assign-relative-destination
        window.location.assign("/login");
      }}
    >
      <LogOutIcon />
    </Button>
  );
}

/**
 * The nav highlights the current page, which means reading the URL. With cacheComponents on,
 * that read must sit inside <Suspense> on pages whose URL isn't known at build time
 * (e.g. /runs/[id]), so the fallback is the same bar with no link highlighted.
 */
export function SiteNav() {
  return (
    <Suspense fallback={<NavBar pathname={null} />}>
      <NavWithPathname />
    </Suspense>
  );
}

function NavWithPathname() {
  return <NavBar pathname={usePathname()} />;
}

function NavBar({ pathname }: { pathname: string | null }) {
  const [open, setOpen] = useState(false);
  // The login page shows just the logo and theme toggle: nothing else works before login.
  const onLogin = pathname === "/login";
  const [lastPath, setLastPath] = useState(pathname);

  // Close the mobile menu whenever the route changes.
  if (pathname !== lastPath) {
    setLastPath(pathname);
    setOpen(false);
  }

  return (
    <header className="sticky top-0 z-40 border-b bg-background/75 backdrop-blur-lg supports-[backdrop-filter]:bg-background/60">
      <nav className="mx-auto flex h-14 max-w-7xl items-center gap-4 px-4 sm:px-6" aria-label="Main">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <motion.span
            className="grid size-8 place-items-center rounded-lg bg-primary text-primary-foreground"
            whileHover={{ rotate: -12, scale: 1.08 }}
            transition={{ type: "spring", stiffness: 400, damping: 15 }}
          >
            <FlaskConicalIcon className="size-4" />
          </motion.span>
          <span className="hidden sm:inline">Agent Eval</span>
        </Link>

        {/* Desktop links: the highlight pill slides between links (shared layoutId). */}
        <ul className={cn("ml-2 hidden items-center gap-1", !onLogin && "md:flex")}>
          {LINKS.map(({ href, label, icon: Icon }) => {
            const active = isActive(pathname, href);
            return (
              <li key={href}>
                <Link
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "relative flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-sm transition-colors",
                    active ? "text-foreground" : "text-muted-foreground hover:text-foreground",
                  )}
                >
                  {active && (
                    <motion.span
                      layoutId="nav-pill"
                      className="absolute inset-0 -z-10 rounded-full bg-muted"
                      transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    />
                  )}
                  <Icon className="size-4" />
                  {label}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="ml-auto flex items-center gap-2">
          {!onLogin && <ApiStatus />}
          <ThemeToggle />
          {!onLogin && <LogoutButton />}
          <Button
            variant="ghost"
            size="icon"
            className={cn("md:hidden", onLogin && "hidden")}
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            onClick={() => setOpen((o) => !o)}
          >
            {open ? <XIcon /> : <MenuIcon />}
          </Button>
        </div>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.ul
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden border-t px-4 md:hidden"
          >
            {LINKS.map(({ href, label, icon: Icon }, i) => (
              <motion.li
                key={href}
                initial={{ x: -12, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                transition={{ delay: 0.04 * i }}
              >
                <Link
                  href={href}
                  aria-current={isActive(pathname, href) ? "page" : undefined}
                  className={cn(
                    "flex items-center gap-2 rounded-md px-2 py-3 text-sm",
                    isActive(pathname, href) ? "font-medium text-foreground" : "text-muted-foreground",
                  )}
                >
                  <Icon className="size-4" />
                  {label}
                </Link>
              </motion.li>
            ))}
          </motion.ul>
        )}
      </AnimatePresence>
    </header>
  );
}
