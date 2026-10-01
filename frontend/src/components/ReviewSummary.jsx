import React, { useMemo, useState } from "react";

const STATUS_STYLES = {
  approve: "bg-emerald-950 text-emerald-300 border-emerald-800",
  needs_changes: "bg-red-950 text-red-300 border-red-800",
  review: "bg-amber-950 text-amber-300 border-amber-800",
};

/**
 * ReviewSummary — shows the LLM summary plus a compact review health snapshot.
 *
 * Keeping the counts next to the summary makes the first screen useful for a
 * recruiter/developer without requiring them to scan the entire findings list.
 */
export default function ReviewSummary({ review }) {
  const [copied, setCopied] = useState(false);

  const counts = useMemo(() => {
    const findings = review?.findings || [];
    return {
      total: findings.length,
      critical: findings.filter((f) => f.severity === "critical").length,
      high: findings.filter((f) => f.severity === "high").length,
      medium: findings.filter((f) => f.severity === "medium").length,
      low: findings.filter((f) => f.severity === "low").length,
    };
  }, [review]);

  async function copySummary() {
    try {
      await navigator.clipboard.writeText(review.summary || "");
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard permissions can be unavailable in some browsers/contexts.
    }
  }

  const status = review?.overall_status || "review";
  const statusLabel = status.replace("_", " ");

  return (
    <section className="rounded-2xl border border-gray-800 bg-gray-900/50 p-6 space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
          AI Summary
        </h3>
        <span className={`px-2.5 py-1 rounded-full border text-[11px] font-semibold uppercase tracking-wide ${STATUS_STYLES[status] || STATUS_STYLES.review}`}>
          {statusLabel}
        </span>
        <button
          type="button"
          onClick={copySummary}
          className="ml-auto text-xs text-gray-500 hover:text-gray-200 transition"
        >
          {copied ? "Copied ✓" : "Copy summary"}
        </button>
      </div>

      <p className="text-gray-300 leading-relaxed text-sm">{review.summary}</p>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-1">
        <Stat label="Total" value={counts.total} />
        <Stat label="Critical" value={counts.critical} />
        <Stat label="High" value={counts.high} />
        <Stat label="Medium" value={counts.medium} />
        <Stat label="Low" value={counts.low} />
      </div>
    </section>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-950/60 px-3 py-2">
      <div className="text-lg font-semibold text-white">{value}</div>
      <div className="text-[10px] uppercase tracking-wider text-gray-600">{label}</div>
    </div>
  );
}
