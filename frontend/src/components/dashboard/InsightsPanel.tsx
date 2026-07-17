"use client";

import { motion } from "framer-motion";

import { AnimatedCard, Badge } from "@/components/ui/primitives";
import { AnalysisResult } from "@/lib/types";

export function InsightsPanel({ result }: { result: AnalysisResult }) {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <AnimatedCard className="lg:col-span-2">
        <h3 className="mb-3 font-semibold text-slate-800">Automatic Insights</h3>
        <ul className="space-y-3">
          {result.insights.map((insight, index) => (
            <motion.li
              key={insight.title}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.04 }}
              className="flex flex-col gap-1 rounded-lg border border-slate-100 p-3"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-slate-800">{insight.title}</span>
                <Badge variant={insight.severity}>{insight.severity}</Badge>
              </div>
              <p className="text-sm text-slate-600">{insight.detail}</p>
            </motion.li>
          ))}
        </ul>
      </AnimatedCard>

      <AnimatedCard delay={0.1}>
        <h3 className="mb-3 font-semibold text-slate-800">Executive Summary</h3>
        <p className="text-sm leading-relaxed text-slate-600">
          {result.executive_summary.summary}
        </p>
        <p className="mt-3 text-xs text-slate-400">
          {result.executive_summary.used_llm
            ? "Generated with LLM"
            : "Generated with rule-based engine"}
        </p>
      </AnimatedCard>

      <AnimatedCard delay={0.15} className="lg:col-span-3">
        <h3 className="mb-3 font-semibold text-slate-800">Data Quality Issues</h3>
        <ul className="grid grid-cols-1 gap-2 md:grid-cols-2">
          {result.quality.issues.map((issue) => (
            <li
              key={issue}
              className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600"
            >
              {issue}
            </li>
          ))}
        </ul>
      </AnimatedCard>
    </div>
  );
}
