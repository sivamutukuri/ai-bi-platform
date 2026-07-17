"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  Columns3,
  Copy,
  Gauge,
  Rows3,
  Waves,
} from "lucide-react";
import { ReactNode } from "react";

import { Kpi } from "@/lib/types";

const iconMap: Record<string, ReactNode> = {
  rows: <Rows3 className="h-5 w-5" />,
  cols: <Columns3 className="h-5 w-5" />,
  quality: <Gauge className="h-5 w-5" />,
  missing: <AlertTriangle className="h-5 w-5" />,
  dup: <Copy className="h-5 w-5" />,
  corr: <Waves className="h-5 w-5" />,
};

export function KpiCards({ kpis }: { kpis: Kpi[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
      {kpis.map((kpi, index) => (
        <motion.div
          key={kpi.label}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: index * 0.05 }}
          className="card flex flex-col gap-2"
        >
          <div className="flex items-center justify-between text-brand-600">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
              {kpi.label}
            </span>
            {iconMap[kpi.icon] ?? <Gauge className="h-5 w-5" />}
          </div>
          <div className="text-2xl font-semibold text-slate-900">
            {kpi.value.toLocaleString()}
            {kpi.suffix && (
              <span className="ml-0.5 text-sm text-slate-400">{kpi.suffix}</span>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}
