import React, { useState } from "react";
import { analyzePR } from "./services/api";
import PRInputForm from "./components/PRInputForm";
import PRMetaCard from "./components/PRMetaCard";
import ReviewSummary from "./components/ReviewSummary";
import FindingsList from "./components/FindingsList";
import ErrorAlert from "./components/ErrorAlert";
import LoadingSpinner from "./components/LoadingSpinner";
import DiffPreview from "./components/DiffPreview";
import AnalysisWarnings from "./components/AnalysisWarnings";

/**
 * App.jsx — root component and state manager.
 *
 * State machine (simple, no external library needed):
 *   idle → loading → success
 *              ↘ error
 *
 * Why keep state here and not in individual components?
 *   The review result is needed by multiple components (meta card, summary,
 *   findings list). Lifting state to the common ancestor avoids prop-drilling
 *   and keeps the data flow easy to trace in an interview.
 */
export default function App() {
  const [status, setStatus] = useState("idle"); // idle | loading | success | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  async function handleAnalyze(prUrl) {
    setStatus("loading");
    setResult(null);
    setError("");
    try {
      const data = await analyzePR(prUrl);
      setResult(data);
      setStatus("success");
    } catch (err) {
      setError(err.message);
      setStatus("error");
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans">
      {/* ── Header ── */}
      <header className="border-b border-gray-800 bg-gray-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-sm font-bold">
            AI
          </div>
          <span className="font-semibold text-lg tracking-tight">CodeReview</span>
          <span className="ml-auto text-xs text-gray-500 hidden sm:block">
            LLM-powered GitHub PR Analyzer
          </span>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="max-w-5xl mx-auto px-6 py-12 space-y-10">
        {/* Hero */}
        <section className="text-center space-y-4">
          <h1 className="text-4xl sm:text-5xl font-extrabold bg-gradient-to-r from-violet-400 via-indigo-400 to-sky-400 bg-clip-text text-transparent leading-tight">
            AI-Powered Code Review
          </h1>
          <p className="text-gray-400 max-w-xl mx-auto text-base sm:text-lg">
            Paste a public GitHub pull request URL and get an instant, structured
            review combining deterministic static analysis and LLM insights.
          </p>
        </section>

        {/* Input */}
        <PRInputForm onSubmit={handleAnalyze} isLoading={status === "loading"} />

        {/* Loading */}
        {status === "loading" && <LoadingSpinner />}

        {/* Error */}
        {status === "error" && <ErrorAlert message={error} />}

        {/* Results */}
        {status === "success" && result && (
          <div className="space-y-8 animate-fade-in">
            <PRMetaCard data={result} />
            <AnalysisWarnings warnings={result.analysis_warnings} />
            <ReviewSummary review={result.review} />
            <FindingsList findings={result.review.findings} />
            <DiffPreview diff={result.diff_preview} />
          </div>
        )}
      </main>

      {/* ── Footer ── */}
      <footer className="border-t border-gray-800 mt-24">
        <div className="max-w-5xl mx-auto px-6 py-6 text-center text-xs text-gray-600">
          Read-only · Never modifies your repository · Public PRs only
        </div>
      </footer>
    </div>
  );
}
