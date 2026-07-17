"use client";

import { Sparkles } from "lucide-react";
import { FormEvent, useState } from "react";

import { Card, Spinner } from "@/components/ui/primitives";
import { api, apiErrorMessage } from "@/lib/api";
import { NLQueryResponse } from "@/lib/types";

const SUGGESTIONS = [
  "How many rows are there?",
  "What is the average revenue?",
  "What is the maximum price?",
  "What is the total profit?",
];

export function QueryPanel({ datasetId }: { datasetId: string }) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<NLQueryResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function ask(q: string) {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post<NLQueryResponse>("/analysis/query", {
        dataset_id: datasetId,
        question: q,
      });
      setAnswer(data);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (question.trim().length >= 3) ask(question.trim());
  }

  return (
    <Card>
      <div className="mb-3 flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-brand-600" />
        <h3 className="font-semibold text-slate-800">Ask your data</h3>
      </div>
      <form onSubmit={onSubmit} className="flex flex-col gap-2 sm:flex-row">
        <input
          className="input"
          placeholder="e.g. What is the average revenue?"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? <Spinner className="border-white/40 border-t-white" /> : "Ask"}
        </button>
      </form>

      <div className="mt-2 flex flex-wrap gap-2">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => {
              setQuestion(s);
              ask(s);
            }}
            className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 hover:bg-slate-200"
          >
            {s}
          </button>
        ))}
      </div>

      {error && <p className="mt-3 text-sm text-rose-600">{error}</p>}

      {answer && (
        <div className="mt-4 rounded-lg bg-brand-50 p-4">
          <p className="font-medium text-slate-800">{answer.answer}</p>
          {answer.generated_code && (
            <pre className="mt-2 overflow-x-auto rounded bg-slate-900 p-3 text-xs text-slate-100">
              {answer.generated_code}
            </pre>
          )}
          <p className="mt-2 text-xs text-slate-500">
            {answer.used_llm ? "Answered with LLM" : "Answered with rule-based engine"}
          </p>
        </div>
      )}
    </Card>
  );
}
