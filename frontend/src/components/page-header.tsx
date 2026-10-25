"use client";

import { motion } from "motion/react";

type Props = {
  title: string;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
};

export function PageHeader({ title, description, icon, actions }: Props) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div className="flex items-start gap-3">
        {icon && (
          <motion.span
            initial={{ scale: 0.6, rotate: -20, opacity: 0 }}
            animate={{ scale: 1, rotate: 0, opacity: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 16 }}
            className="mt-1 grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-foreground ring-1 ring-foreground/10 [&_svg]:size-5"
          >
            {icon}
          </motion.span>
        )}
        <div>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
          {description && <p className="mt-1 max-w-2xl text-muted-foreground">{description}</p>}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
