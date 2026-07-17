"use client";

import { FileSpreadsheet, FileText } from "lucide-react";
import { useState } from "react";

import { Spinner } from "@/components/ui/primitives";
import { api, apiErrorMessage } from "@/lib/api";

export function ReportButtons({
  datasetId,
  datasetName,
}: {
  datasetId: string;
  datasetName: string;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function download(fmt: "pdf" | "excel") {
    setBusy(fmt);
    setError(null);
    try {
      const { data } = await api.post(
        "/reports/generate",
        { dataset_id: datasetId, fmt },
        { responseType: "blob" }
      );
      const ext = fmt === "pdf" ? "pdf" : "xlsx";
      const url = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `${datasetName}_report.${ext}`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex gap-2">
        <button
          className="btn-ghost"
          onClick={() => download("pdf")}
          disabled={busy !== null}
        >
          {busy === "pdf" ? <Spinner /> : <FileText className="h-4 w-4" />}
          PDF
        </button>
        <button
          className="btn-ghost"
          onClick={() => download("excel")}
          disabled={busy !== null}
        >
          {busy === "excel" ? (
            <Spinner />
          ) : (
            <FileSpreadsheet className="h-4 w-4" />
          )}
          Excel
        </button>
      </div>
      {error && <p className="text-xs text-rose-600">{error}</p>}
    </div>
  );
}
