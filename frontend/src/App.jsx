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

const FEATURES = [
  { number: "01", title: "Deterministic checks", description: "Fast rules catch common quality, debugging and security issues before the LLM review." },
  { number: "02", title: "Semantic review", description: "The LLM reasons about logic, error handling and suspicious changes that patterns can miss." },
  { number: "03", title: "Actionable findings", description: "Every finding includes severity, file location and a concrete suggestion for the developer." },
];

export default function App() {
  const [status, setStatus] = useState("idle");
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
      setError(err.message || "Something went wrong while analyzing the PR.");
      setStatus("error");
    }
  }

  const resetReview = () => {
    setStatus("idle");
    setResult(null);
    setError("");
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white font-sans selection:bg-violet-500/30">
      <header className="border-b border-gray-800/80 bg-gray-950/85 backdrop-blur-xl sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-5 sm:px-6 py-4 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-xs font-black shadow-lg shadow-violet-950/40">CR</div>
          <div><div className="font-semibold tracking-tight">CodeReviewer</div><div className="text-[10px] uppercase tracking-widest text-gray-600 hidden sm:block">AI-assisted pull request review</div></div>
          <div className="ml-auto hidden sm:flex items-center gap-2 text-xs text-gray-500"><span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Read-only analysis</div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-5 sm:px-6 py-12 sm:py-16">
        {status !== "success" ? (
          <>
            <section className="text-center max-w-3xl mx-auto">
              <div className="inline-flex items-center gap-2 rounded-full border border-violet-900/70 bg-violet-950/30 px-3 py-1.5 text-[11px] font-medium text-violet-300 mb-6"><span className="w-1.5 h-1.5 rounded-full bg-violet-400 animate-pulse" /> Static analysis + LLM reasoning</div>
              <h1 className="text-4xl sm:text-6xl font-black tracking-tight leading-[1.05]">Review pull requests with<span className="block bg-gradient-to-r from-violet-400 via-indigo-400 to-sky-400 bg-clip-text text-transparent">more than pattern matching.</span></h1>
              <p className="mt-5 text-gray-400 max-w-2xl mx-auto text-base sm:text-lg leading-relaxed">Paste a public GitHub pull request and get a structured review combining deterministic rules with semantic AI analysis.</p>
            </section>

            <section className="max-w-4xl mx-auto mt-10">
              <div className="rounded-2xl border border-gray-800 bg-gray-900/60 p-3 sm:p-4 shadow-2xl shadow-black/20">
                <PRInputForm onSubmit={handleAnalyze} isLoading={status === "loading"} />
                <div className="flex flex-wrap items-center gap-x-5 gap-y-2 px-2 pt-3 text-[11px] text-gray-600"><span>✓ Public GitHub PRs</span><span>✓ Read-only</span><span>✓ No repository changes</span></div>
              </div>
            </section>

            {status === "loading" && <LoadingSpinner />}
            {status === "error" && <div className="max-w-4xl mx-auto mt-6"><ErrorAlert message={error} /></div>}

            {status === "idle" && <section className="grid md:grid-cols-3 gap-4 max-w-5xl mx-auto mt-14">{FEATURES.map((feature) => <div key={feature.number} className="rounded-2xl border border-gray-800 bg-gray-900/35 p-5 hover:border-gray-700 hover:bg-gray-900/55 transition-colors"><div className="text-xs font-mono text-violet-400 mb-4">{feature.number}</div><h2 className="font-semibold text-gray-100">{feature.title}</h2><p className="text-sm text-gray-500 leading-relaxed mt-2">{feature.description}</p></div>)}</section>}
          </>
        ) : (
          <div className="animate-fade-in space-y-8">
            <div className="flex flex-wrap items-end justify-between gap-4"><div><p className="text-xs uppercase tracking-widest text-violet-400 font-semibold">Review complete</p><h1 className="text-3xl sm:text-4xl font-bold mt-2">Pull request analysis</h1></div><button type="button" onClick={resetReview} className="rounded-xl border border-gray-700 bg-gray-900 px-4 py-2.5 text-sm text-gray-300 hover:text-white hover:border-gray-600 transition">Analyze another PR</button></div>
            <PRMetaCard data={result} /><AnalysisWarnings warnings={result.analysis_warnings} /><ReviewSummary review={result.review} /><FindingsList findings={result.review.findings} /><DiffPreview diff={result.diff_preview} />
          </div>
        )}
      </main>

      <footer className="border-t border-gray-800/80 mt-8"><div className="max-w-6xl mx-auto px-5 sm:px-6 py-7 flex flex-col sm:flex-row gap-2 justify-between text-xs text-gray-600"><span>CodeReviewer · AI-assisted PR analysis</span><span>Read-only · Public PRs only</span></div></footer>
    </div>
  );
}
