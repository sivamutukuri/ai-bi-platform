"use client";

import dynamic from "next/dynamic";
import type { Data, Layout } from "plotly.js";

import { Spinner } from "@/components/ui/primitives";

// Plotly relies on the DOM, so it must be loaded client-side only.
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="flex h-64 items-center justify-center">
      <Spinner />
    </div>
  ),
});

const baseLayout: Partial<Layout> = {
  margin: { l: 48, r: 16, t: 32, b: 40 },
  font: { family: "Inter, system-ui, sans-serif", size: 12, color: "#334155" },
  paper_bgcolor: "transparent",
  plot_bgcolor: "transparent",
  colorway: ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6"],
  autosize: true,
};

export function Chart({
  data,
  layout,
  height = 320,
}: {
  data: Data[];
  layout?: Partial<Layout>;
  height?: number;
}) {
  return (
    <Plot
      data={data}
      layout={{ ...baseLayout, ...layout, height }}
      config={{ displayModeBar: false, responsive: true }}
      style={{ width: "100%", height }}
      useResizeHandler
    />
  );
}
