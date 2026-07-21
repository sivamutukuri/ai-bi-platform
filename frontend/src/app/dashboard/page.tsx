"use client";

import { LogOut, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { ChartsPanel } from "@/components/dashboard/ChartsPanel";
import { InsightsPanel } from "@/components/dashboard/InsightsPanel";
import { KpiCards } from "@/components/dashboard/KpiCards";
import { QueryPanel } from "@/components/dashboard/QueryPanel";
import { ReportButtons } from "@/components/dashboard/ReportButtons";
import { UploadPanel } from "@/components/dashboard/UploadPanel";
import { LiveStreamPanel } from "@/components/dashboard/LiveStreamPanel";
import { EmptyState, Spinner } from "@/components/ui/primitives";
import { api, apiErrorMessage, getToken } from "@/lib/api";
import { AnalysisResult, Dataset } from "@/lib/types";
import { useAuth } from "@/store/auth";

export default function DashboardPage() {
  const { user, fetchMe, logout } = useAuth();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [active, setActive] = useState<Dataset | null>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken() && typeof window !== "undefined") {
      window.location.href = "/login";
      return;
    }
    fetchMe();
    loadDatasets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadDatasets() {
    try {
      const { data } = await api.get<Dataset[]>("/datasets");
      setDatasets(data);
      if (data[0] && !active) selectDataset(data[0]);
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  async function selectDataset(dataset: Dataset) {
    setActive(dataset);
    setResult(null);
    setAnalyzing(true);
    setError(null);
    try {
      const { data } = await api.post<AnalysisResult>(
        `/analysis/${dataset.id}/run`
      );
      setResult(data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setAnalyzing(false);
    }
  }

  function onCreated(dataset: Dataset) {
    setDatasets((prev) => [dataset, ...prev]);
    selectDataset(dataset);
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
          <div>
            <h1 className="text-lg font-bold text-brand-700">AI BI Platform</h1>
            <p className="text-xs text-slate-500">
              {user ? `Signed in as ${user.email}` : "Loading..."}
            </p>
          </div>
          <button className="btn-ghost" onClick={logout}>
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <UploadPanel onCreated={onCreated} />
            <div className="card mt-4">
              <h3 className="mb-3 font-semibold text-slate-800">Your datasets</h3>
              {datasets.length === 0 ? (
                <p className="text-sm text-slate-500">No datasets yet.</p>
              ) : (
                <ul className="space-y-2">
                  {datasets.map((d) => (
                    <li key={d.id}>
                      <button
                        onClick={() => selectDataset(d)}
                        className={`w-full rounded-lg border px-3 py-2 text-left text-sm ${
                          active?.id === d.id
                            ? "border-brand-400 bg-brand-50"
                            : "border-slate-200 hover:bg-slate-50"
                        }`}
                      >
                        <span className="font-medium text-slate-800">{d.name}</span>
                        <span className="ml-2 text-xs text-slate-400">
                          {d.row_count ?? "?"} rows
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="lg:col-span-2">
            {active && <QueryPanel datasetId={active.id} />}
          </div>
        </div>

        {error && (
          <div className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</div>
        )}

        {analyzing && (
          <div className="flex items-center justify-center gap-2 py-12 text-slate-500">
            <Spinner /> Running analysis pipeline...
          </div>
        )}

        {!active && !analyzing && (
          <EmptyState
            title="Upload a dataset to get started"
            hint="CSV, Excel, JSON, or connect a SQL database."
          />
        )}

        {result && active && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-slate-900">{active.name}</h2>
                <p className="text-sm text-slate-500">
                  {result.row_count} rows - {result.column_count} columns
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button className="btn-ghost" onClick={() => selectDataset(active)}>
                  <RefreshCw className="h-4 w-4" /> Re-run
                </button>
                <ReportButtons datasetId={active.id} datasetName={active.name} />
              </div>
            </div>
            <KpiCards kpis={result.kpis} />
            <InsightsPanel result={result} />
            <ChartsPanel result={result} />
          </div>
        )}

        <LiveStreamPanel />
      </main>
    </div>
  );
}
