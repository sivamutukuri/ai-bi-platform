"use client";

import { motion } from "framer-motion";
import { Activity, Radio, Signal, Square } from "lucide-react";
import type { Data } from "plotly.js";
import { useCallback, useEffect, useRef, useState } from "react";

import { Chart } from "@/components/charts/Chart";
import {
  StreamMetrics,
  ingestBatch,
  subscribeToStream,
} from "@/lib/streaming";

interface Point {
  t: number;
  rps: number;
  count: number;
}

const MAX_POINTS = 60;

export function LiveStreamPanel({
  defaultStreamId = "live-demo",
}: {
  defaultStreamId?: string;
}) {
  const [streamId, setStreamId] = useState(defaultStreamId);
  const [connected, setConnected] = useState(false);
  const [metrics, setMetrics] = useState<StreamMetrics | null>(null);
  const [history, setHistory] = useState<Point[]>([]);
  const cleanupRef = useRef<(() => void) | null>(null);
  const demoTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  const handleMetrics = useCallback((m: StreamMetrics) => {
    setMetrics(m);
    setHistory((prev) => {
      const next = [
        ...prev,
        { t: Date.now(), rps: m.records_per_second, count: m.record_count },
      ];
      return next.slice(-MAX_POINTS);
    });
  }, []);

  const connect = useCallback(() => {
    if (cleanupRef.current) cleanupRef.current();
    cleanupRef.current = subscribeToStream(streamId, handleMetrics);
    setConnected(true);
  }, [streamId, handleMetrics]);

  const disconnect = useCallback(() => {
    cleanupRef.current?.();
    cleanupRef.current = null;
    if (demoTimer.current) {
      clearInterval(demoTimer.current);
      demoTimer.current = null;
    }
    setConnected(false);
  }, []);

  // Optional built-in producer so the panel is demonstrable without an
  // external data source. Sends synthetic sensor readings every second.
  const startDemoProducer = useCallback(() => {
    if (demoTimer.current) return;
    if (!connected) connect();
    demoTimer.current = setInterval(() => {
      const batch = Array.from({ length: 5 }).map(() => ({
        temperature: 20 + Math.random() * 10,
        pressure: 1000 + Math.random() * 50,
        revenue: Math.round(Math.random() * 500),
      }));
      void ingestBatch(streamId, batch);
    }, 1000);
  }, [connected, connect, streamId]);

  useEffect(() => {
    return () => disconnect();
  }, [disconnect]);

  const chartData: Data[] = [
    {
      x: history.map((p) => new Date(p.t)),
      y: history.map((p) => p.rps),
      type: "scatter",
      mode: "lines",
      fill: "tozeroy",
      name: "records/sec",
      line: { color: "#4f46e5", width: 2 },
    },
  ];

  return (
    <motion.section
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="card flex flex-col gap-4"
    >
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Radio className="h-5 w-5 text-brand-600" />
          <h2 className="text-lg font-semibold text-slate-900">
            Real-time Streaming
          </h2>
          <span
            className={`ml-2 flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
              connected
                ? "bg-emerald-100 text-emerald-700"
                : "bg-slate-100 text-slate-500"
            }`}
          >
            <Signal className="h-3 w-3" />
            {connected ? "live" : "idle"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <input
            value={streamId}
            onChange={(e) => setStreamId(e.target.value)}
            disabled={connected}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm focus:border-brand-500 focus:outline-none disabled:bg-slate-50"
            placeholder="stream id"
          />
          {connected ? (
            <button
              onClick={disconnect}
              className="flex items-center gap-1 rounded-lg bg-rose-50 px-3 py-1.5 text-sm font-medium text-rose-600 hover:bg-rose-100"
            >
              <Square className="h-4 w-4" /> Stop
            </button>
          ) : (
            <button
              onClick={connect}
              className="flex items-center gap-1 rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              <Activity className="h-4 w-4" /> Connect
            </button>
          )}
          <button
            onClick={startDemoProducer}
            className="rounded-lg border border-brand-200 px-3 py-1.5 text-sm font-medium text-brand-600 hover:bg-brand-50"
          >
            Demo feed
          </button>
        </div>
      </header>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <LiveStat label="Records" value={metrics?.record_count ?? 0} />
        <LiveStat label="Batches" value={metrics?.batch_count ?? 0} />
        <LiveStat
          label="Records/sec"
          value={metrics?.records_per_second ?? 0}
          decimals={2}
        />
        <LiveStat
          label="Fields tracked"
          value={metrics ? Object.keys(metrics.averages).length : 0}
        />
      </div>

      <div className="h-64 w-full">
        <Chart
          data={chartData}
          layout={{
            margin: { l: 40, r: 10, t: 10, b: 30 },
            xaxis: { showgrid: false },
            yaxis: { title: { text: "records/sec" }, rangemode: "tozero" },
          }}
        />
      </div>

      {metrics && Object.keys(metrics.averages).length > 0 && (
        <div className="flex flex-wrap gap-2">
          {Object.entries(metrics.averages).map(([field, avg]) => (
            <span
              key={field}
              className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600"
            >
              {field}: avg {avg.toFixed(2)}
            </span>
          ))}
        </div>
      )}
    </motion.section>
  );
}

function LiveStat({
  label,
  value,
  decimals = 0,
}: {
  label: string;
  value: number;
  decimals?: number;
}) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </div>
      <div className="mt-1 text-xl font-semibold text-slate-900">
        {value.toLocaleString(undefined, { maximumFractionDigits: decimals })}
      </div>
    </div>
  );
}
