import React from "react";

const STAT_COLOR = {
  approve: "text-emerald-400 bg-emerald-950 border-emerald-800",
  needs_changes: "text-red-400 bg-red-950 border-red-800",
  review: "text-amber-400 bg-amber-950 border-amber-800",
};

const STAT_LABEL = {
  approve: "✓ Approve",
  needs_changes: "✗ Needs Changes",
  review: "⚑ Needs Review",
};

/**
 * PRMetaCard — displays the PR metadata at the top of results.
 * Shows title, author, branches, and the overall status badge.
 */
export default function PRMetaCard({ data }) {
  const status = data.review.overall_status;

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-900/50 p-6 space-y-4">
      {/* Title row */}
      <div className="flex flex-wrap items-start gap-3">
        <div className="flex-1 min-w-0">
          <h2 className="text-lg font-semibold text-white leading-snug truncate">
            {data.pr_title}
          </h2>
          <p className="text-sm text-gray-400 mt-0.5">
            by{" "}
            <span className="text-gray-300 font-medium">@{data.pr_author}</span>
            {" · "}
            <code className="text-indigo-400 text-xs">{data.base_branch}</code>
            {" ← "}
            <code className="text-violet-400 text-xs">{data.head_branch}</code>
          </p>
        </div>
        <span
          className={`shrink-0 px-3 py-1 rounded-full text-xs font-semibold border ${STAT_COLOR[status]}`}
        >
          {STAT_LABEL[status]}
        </span>
      </div>

      {/* Stats row */}
      <div className="flex flex-wrap gap-4 text-sm text-gray-400 border-t border-gray-800 pt-4">
        <StatItem label="Files changed" value={data.changed_files} />
        <StatItem label="Additions" value={`+${data.additions}`} color="text-emerald-400" />
        <StatItem label="Deletions" value={`-${data.deletions}`} color="text-red-400" />
      </div>
    </div>
  );
}

function StatItem({ label, value, color = "text-white" }) {
  return (
    <div className="flex flex-col">
      <span className={`font-semibold ${color}`}>{value}</span>
      <span className="text-xs text-gray-600">{label}</span>
    </div>
  );
}
