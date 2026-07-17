"use client";

import { AnimatedCard, EmptyState } from "@/components/ui/primitives";
import { Chart } from "@/components/charts/Chart";
import { AnalysisResult } from "@/lib/types";

export function ChartsPanel({ result }: { result: AnalysisResult }) {
  const { eda, feature_importance } = result;
  const firstHist = Object.entries(eda.histograms)[0];
  const firstCat = Object.entries(eda.category_distributions)[0];

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {/* Correlation heatmap */}
      <AnimatedCard>
        <h3 className="mb-3 font-semibold text-slate-800">Correlation Matrix</h3>
        {eda.correlation.columns.length > 1 ? (
          <Chart
            data={[
              {
                type: "heatmap",
                z: eda.correlation.matrix as number[][],
                x: eda.correlation.columns,
                y: eda.correlation.columns,
                colorscale: "RdBu",
                zmid: 0,
                reversescale: true,
              },
            ]}
          />
        ) : (
          <EmptyState title="Not enough numeric columns for correlation." />
        )}
      </AnimatedCard>

      {/* Trend line */}
      <AnimatedCard delay={0.05}>
        <h3 className="mb-3 font-semibold text-slate-800">
          Trend {eda.trend.metric ? `- ${eda.trend.metric}` : ""}
        </h3>
        {eda.trend.available ? (
          <Chart
            data={[
              {
                type: "scatter",
                mode: "lines",
                x: eda.trend.dates,
                y: eda.trend.values,
                fill: "tozeroy",
                line: { color: "#4f46e5", width: 2 },
              },
            ]}
          />
        ) : (
          <EmptyState title="No datetime + metric pair available for trend." />
        )}
      </AnimatedCard>

      {/* Distribution histogram */}
      <AnimatedCard delay={0.1}>
        <h3 className="mb-3 font-semibold text-slate-800">
          Distribution {firstHist ? `- ${firstHist[0]}` : ""}
        </h3>
        {firstHist ? (
          <Chart
            data={[
              {
                type: "bar",
                x: firstHist[1].bins.slice(0, -1),
                y: firstHist[1].counts,
                marker: { color: "#0ea5e9" },
              },
            ]}
          />
        ) : (
          <EmptyState title="No numeric columns to plot." />
        )}
      </AnimatedCard>

      {/* Feature importance */}
      <AnimatedCard delay={0.15}>
        <h3 className="mb-3 font-semibold text-slate-800">
          Feature Importance
          {feature_importance.target ? ` - ${feature_importance.target}` : ""}
        </h3>
        {feature_importance.available && feature_importance.importances ? (
          <Chart
            data={[
              {
                type: "bar",
                orientation: "h",
                x: feature_importance.importances.map((i) => i.importance),
                y: feature_importance.importances.map((i) => i.feature),
                marker: { color: "#10b981" },
              },
            ]}
            layout={{ margin: { l: 120, r: 16, t: 16, b: 40 } }}
          />
        ) : (
          <EmptyState
            title="Feature importance unavailable."
            hint={feature_importance.reason}
          />
        )}
      </AnimatedCard>

      {/* Category distribution */}
      {firstCat && (
        <AnimatedCard delay={0.2} className="lg:col-span-2">
          <h3 className="mb-3 font-semibold text-slate-800">
            Top Categories - {firstCat[0]}
          </h3>
          <Chart
            data={[
              {
                type: "bar",
                x: firstCat[1].labels,
                y: firstCat[1].counts,
                marker: { color: "#8b5cf6" },
              },
            ]}
          />
        </AnimatedCard>
      )}
    </div>
  );
}
