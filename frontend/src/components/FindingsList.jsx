import React, { useState } from "react";

// ── Styling maps ──────────────────────────────────────────────────────────────

const SEVERITY_STYLES = {
  critical: "bg-red-950 border-red-700 text-red-300",
  high:     "bg-orange-950 border-orange-700 text-orange-300",
  medium:   "bg-amber-950 border-amber-700 text-amber-300",
  low:      "bg-gray-900 border-gray-700 text-gray-400",
};

const SEVERITY_BADGE = {
  critical: "bg-red-900 text-red-200",
  high:     "bg-orange-900 text-orange-200",
  medium:   "bg-amber-900 text-amber-200",
  low:      "bg-gray-800 text-gray-400",
};

const CATEGORY_BADGE = {
  security:        "bg-red-900/50 text-red-300",
  bug:             "bg-orange-900/50 text-orange-300",
  performance:     "bg-blue-900/50 text-blue-300",
  maintainability: "bg-purple-900/50 text-purple-300",
  quality:         "bg-gray-800 text-gray-400",
};

const SEVERITY_ORDER = ["critical", "high", "medium", "low"];

/**
 * FindingsList — groups findings by severity and renders each as a card.
 *
 * Grouping by severity helps the reviewer immediately see the most critical
 * issues at the top without scanning through a flat list.
 */
export default function FindingsList({ findings }) {
  if (!findings || findings.length === 0) {
    return (
      <div className="rounded-2xl border border-gray-800 bg-gray-900/50 p-10 text-center text-gray-500 text-sm">
        No findings — the code looks clean! 🎉
      </div>
    );
  }

  // Group by severity, respecting the severity order
  const grouped = SEVERITY_ORDER.reduce((acc, sev) => {
    const items = findings.filter((f) => f.severity === sev);
    if (items.length > 0) acc[sev] = items;
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-widest">
        Findings · {findings.length} total
      </h3>
      {Object.entries(grouped).map(([severity, items]) => (
        <SeverityGroup key={severity} severity={severity} items={items} />
      ))}
    </div>
  );
}

function SeverityGroup({ severity, items }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 rounded text-xs font-bold uppercase ${SEVERITY_BADGE[severity]}`}>
          {severity}
        </span>
        <span className="text-xs text-gray-600">{items.length} finding{items.length > 1 ? "s" : ""}</span>
      </div>
      {items.map((finding, idx) => (
        <FindingCard key={idx} finding={finding} />
      ))}
    </div>
  );
}

function FindingCard({ finding }) {
  const [expanded, setExpanded] = useState(false);
  const borderStyle = SEVERITY_STYLES[finding.severity] || SEVERITY_STYLES.low;

  return (
    <div className={`rounded-xl border p-4 space-y-2 transition-all ${borderStyle}`}>
      {/* Top row */}
      <div className="flex flex-wrap items-start gap-2">
        <span className={`px-2 py-0.5 rounded text-xs font-medium ${CATEGORY_BADGE[finding.category] || ""}`}>
          {finding.category}
        </span>
        {finding.source === "static" && (
          <span className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-950 text-indigo-300">
            static rule
          </span>
        )}
        <code className="ml-auto text-xs text-gray-500 font-mono truncate max-w-xs">
          {finding.file}{finding.line ? `:${finding.line}` : ""}
        </code>
      </div>

      {/* Message */}
      <p className="text-sm font-medium text-white">{finding.message}</p>

      {/* Suggestion (collapsible) */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-indigo-400 hover:text-indigo-300 transition"
      >
        {expanded ? "▲ Hide suggestion" : "▼ Show suggestion"}
      </button>
      {expanded && (
        <p className="text-xs text-gray-300 bg-black/20 rounded-lg p-3 leading-relaxed">
          {finding.suggestion}
        </p>
      )}
    </div>
  );
}
