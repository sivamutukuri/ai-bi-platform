"use client";

import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { Spinner } from "@/components/ui/primitives";
import { apiErrorMessage } from "@/lib/api";
import { useAuth } from "@/store/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, register, loading } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [form, setForm] = useState({ email: "", password: "", fullName: "" });
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "register") {
        await register(form.email, form.password, form.fullName);
      }
      await login(form.email, form.password);
      router.push("/dashboard");
    } catch (err) {
      setError(apiErrorMessage(err));
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-50 to-slate-100 p-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-brand-700">AI BI Platform</h1>
          <p className="mt-1 text-slate-500">
            Turn raw data into decisions in seconds.
          </p>
        </div>
        <div className="card">
          <div className="mb-4 flex rounded-lg bg-slate-100 p-1">
            {(["login", "register"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`flex-1 rounded-md py-1.5 text-sm font-medium capitalize ${
                  mode === m ? "bg-white shadow-sm" : "text-slate-500"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
          <form onSubmit={onSubmit} className="flex flex-col gap-3">
            {mode === "register" && (
              <div>
                <label className="label">Full name</label>
                <input
                  className="input"
                  value={form.fullName}
                  onChange={(e) => setForm({ ...form, fullName: e.target.value })}
                />
              </div>
            )}
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                required
                className="input"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                required
                minLength={8}
                className="input"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
              />
            </div>
            {error && <p className="text-sm text-rose-600">{error}</p>}
            <button type="submit" className="btn-primary mt-1" disabled={loading}>
              {loading ? (
                <Spinner className="border-white/40 border-t-white" />
              ) : mode === "login" ? (
                "Sign in"
              ) : (
                "Create account"
              )}
            </button>
          </form>
          <p className="mt-4 text-center text-xs text-slate-400">
            Demo login: demo@aibi.dev / demo12345
          </p>
        </div>
      </motion.div>
    </main>
  );
}
