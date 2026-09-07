import React from "react";

/**
 * ReviewSummary — shows the LLM-generated prose summary of the PR.
 */
export default function ReviewSummary({ review }) {
  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/50 p-6">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
        AI Summary
      </h3>
      <p className="text-gray-300 leading-relaxed text-sm">{review.summary}</p>
    </div>
  );
}
