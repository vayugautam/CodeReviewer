import React, { useEffect, useState } from "react";

const STEPS = [
  "Fetching pull request metadata",
  "Parsing changed files",
  "Running deterministic checks",
  "Running semantic AI review",
];

export default function LoadingSpinner() {
  const [step, setStep] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => setStep((current) => Math.min(current + 1, STEPS.length - 1)), 1800);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="max-w-xl mx-auto py-14 text-center">
      <div className="rounded-2xl border border-gray-800 bg-gray-900/40 p-7">
        <div className="mx-auto w-11 h-11 rounded-full border-4 border-gray-800 border-t-violet-500 animate-spin" />
        <p className="text-gray-200 font-medium text-sm mt-5">Analyzing pull request…</p>
        <p className="text-violet-300 text-xs mt-2 transition-all">{STEPS[step]}</p>
        <div className="flex justify-center gap-1.5 mt-5">
          {STEPS.map((_, index) => <span key={index} className={`h-1 rounded-full transition-all duration-500 ${index <= step ? "w-8 bg-violet-500" : "w-3 bg-gray-800"}`} />)}
        </div>
        <p className="text-gray-600 text-[11px] mt-4">The review is read-only and does not modify the repository.</p>
      </div>
    </div>
  );
}
