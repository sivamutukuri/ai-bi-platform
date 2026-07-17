"use client";

import { Database, Upload } from "lucide-react";
import { useRef, useState } from "react";

import { Card, Spinner } from "@/components/ui/primitives";
import { api, apiErrorMessage } from "@/lib/api";
import { Dataset } from "@/lib/types";

export function UploadPanel({
  onCreated,
}: {
  onCreated: (dataset: Dataset) => void;
}) {
  const [tab, setTab] = useState<"file" | "sql">("file");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const [sql, setSql] = useState({ name: "", connection_uri: "", query: "" });

  async function uploadFile(file: File) {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("name", file.name);
      const { data } = await api.post<Dataset>("/datasets/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onCreated(data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function connectSql() {
    setBusy(true);
    setError(null);
    try {
      const { data } = await api.post<Dataset>("/datasets/connect-sql", sql);
      onCreated(data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card>
      <div className="mb-4 flex gap-2">
        <button
          className={tab === "file" ? "btn-primary" : "btn-ghost"}
          onClick={() => setTab("file")}
        >
          <Upload className="h-4 w-4" /> Upload file
        </button>
        <button
          className={tab === "sql" ? "btn-primary" : "btn-ghost"}
          onClick={() => setTab("sql")}
        >
          <Database className="h-4 w-4" /> Connect SQL
        </button>
      </div>

      {tab === "file" ? (
        <div
          className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 p-8 text-center hover:border-brand-400"
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]);
          }}
        >
          <Upload className="mb-2 h-8 w-8 text-brand-500" />
          <p className="font-medium text-slate-700">
            Drop a CSV, Excel, or JSON file here
          </p>
          <p className="text-sm text-slate-500">or click to browse</p>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.xlsx,.xls,.json"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && uploadFile(e.target.files[0])}
          />
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <div>
            <label className="label">Dataset name</label>
            <input
              className="input"
              value={sql.name}
              onChange={(e) => setSql({ ...sql, name: e.target.value })}
            />
          </div>
          <div>
            <label className="label">Connection URI</label>
            <input
              className="input"
              placeholder="postgresql+psycopg2://user:pass@host:5432/db"
              value={sql.connection_uri}
              onChange={(e) =>
                setSql({ ...sql, connection_uri: e.target.value })
              }
            />
          </div>
          <div>
            <label className="label">Read-only SQL query</label>
            <textarea
              className="input h-24"
              placeholder="SELECT * FROM sales LIMIT 1000"
              value={sql.query}
              onChange={(e) => setSql({ ...sql, query: e.target.value })}
            />
          </div>
          <button className="btn-primary" onClick={connectSql} disabled={busy}>
            {busy ? <Spinner className="border-white/40 border-t-white" /> : "Connect"}
          </button>
        </div>
      )}

      {busy && tab === "file" && (
        <div className="mt-3 flex items-center gap-2 text-sm text-slate-500">
          <Spinner /> Uploading and profiling...
        </div>
      )}
      {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}
    </Card>
  );
}
