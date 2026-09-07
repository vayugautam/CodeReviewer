import React from "react";

export default function AnalysisWarnings({ warnings }) {
  if (!warnings?.length) return null;
  return (
    <section className="rounded-xl border border-amber-800 bg-amber-950/40 px-5 py-4">
      <h3 className="text-sm font-semibold text-amber-200">Analysis scope notice</h3>
      <ul className="mt-2 space-y-1 text-xs leading-relaxed text-amber-100/80">
        {warnings.map((warning) => <li key={warning}>{warning}</li>)}
      </ul>
    </section>
  );
}
