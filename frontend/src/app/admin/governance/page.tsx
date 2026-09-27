"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  ShieldAlert, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  FileText, 
  Sparkles, 
  Database,
  ArrowRight,
  Filter
} from "lucide-react";

interface GovernanceMetrics {
  pending_product_reviews: number;
  pending_verification_reviews: number;
  pending_passport_reviews: number;
  open_flags_total: number;
  open_flags_by_severity: {
    HIGH: number;
    MEDIUM: number;
    LOW: number;
  };
  ai_suggestions_awaiting_review: number;
  active_demo_records_count: number;
}

interface GovernanceFlag {
  id: string;
  entity_type: string;
  entity_id: string;
  flag_type: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  status: string;
  details_json: Record<string, any>;
  created_at: string;
}

export default function GovernanceDashboardPage() {
  const [metrics, setMetrics] = useState<GovernanceMetrics | null>(null);
  const [flags, setFlags] = useState<GovernanceFlag[]>([]);
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Initial fetch of factual metrics and flags
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    Promise.all([
      fetch("/api/v1/governance/dashboard", { headers }).then(res => res.ok ? res.json() : null),
      fetch("/api/v1/governance/flags?page=1&page_size=20", { headers }).then(res => res.ok ? res.json() : null)
    ])
      .then(([metricsData, flagsData]) => {
        if (metricsData) setMetrics(metricsData);
        if (flagsData && flagsData.items) setFlags(flagsData.items);
      })
      .catch(err => console.error("Error loading governance data:", err))
      .finally(() => setLoading(false));
  }, []);

  const filteredFlags = selectedSeverity === "ALL" 
    ? flags 
    : flags.filter(f => f.severity === selectedSeverity);

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between border-b border-slate-200 pb-5">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <ShieldAlert className="h-7 w-7 text-teal-600" />
              Governance & Provenance Command Center
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Auditable platform integrity, neutral review signals, and real-data governance.
            </p>
          </div>
          <div className="mt-4 md:mt-0 flex gap-3">
            <Link
              href="/admin/moderation"
              className="inline-flex items-center px-4 py-2 border border-slate-300 rounded-md shadow-sm text-sm font-medium text-slate-700 bg-white hover:bg-slate-50"
            >
              Moderation Backlog
            </Link>
            <Link
              href="/admin/provenance"
              className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-teal-600 hover:bg-teal-700"
            >
              Provenance Inspector
            </Link>
          </div>
        </div>

        {/* Real Factual Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-amber-50 rounded-md text-amber-600">
              <Clock className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pending Moderation</p>
              <p className="text-2xl font-bold text-slate-900">
                {metrics ? metrics.pending_product_reviews + metrics.pending_verification_reviews + metrics.pending_passport_reviews : "--"}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                {metrics ? `${metrics.pending_product_reviews} products, ${metrics.pending_verification_reviews} KYC` : "Loading..."}
              </p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-rose-50 rounded-md text-rose-600">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Review Signals</p>
              <p className="text-2xl font-bold text-slate-900">
                {metrics ? metrics.open_flags_total : "--"}
              </p>
              <p className="text-xs text-rose-600 font-medium mt-1">
                {metrics ? `${metrics.open_flags_by_severity.HIGH} High Severity` : ""}
              </p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-indigo-50 rounded-md text-indigo-600">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Staged AI Suggestions</p>
              <p className="text-2xl font-bold text-slate-900">
                {metrics ? metrics.ai_suggestions_awaiting_review : "--"}
              </p>
              <p className="text-xs text-slate-400 mt-1">Awaiting human confirmation</p>
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex items-center gap-4">
            <div className="p-3 bg-slate-100 rounded-md text-slate-600">
              <Database className="h-6 w-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Demo / Sample Records</p>
              <p className="text-2xl font-bold text-slate-900">
                {metrics ? metrics.active_demo_records_count : "--"}
              </p>
              <p className="text-xs text-slate-400 mt-1">Isolated from cluster metrics</p>
            </div>
          </div>
        </div>

        {/* Information States Taxonomy Banner */}
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
            Governance Information States (Strictly Segregated — Zero Conflation)
          </p>
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-700 font-medium">ARTISAN_PROVIDED</span>
            <span className="px-2.5 py-1 rounded bg-blue-100 text-blue-700 font-medium">SOURCE_BACKED</span>
            <span className="px-2.5 py-1 rounded bg-purple-100 text-purple-700 font-medium">AI_SUGGESTED (Staged)</span>
            <span className="px-2.5 py-1 rounded bg-emerald-100 text-emerald-700 font-medium">CALCULATED</span>
            <span className="px-2.5 py-1 rounded bg-teal-100 text-teal-800 font-medium">HUMAN_CONFIRMED</span>
            <span className="px-2.5 py-1 rounded bg-sky-100 text-sky-800 font-medium">ADMIN_REVIEWED</span>
            <span className="px-2.5 py-1 rounded bg-amber-100 text-amber-900 font-medium">AUTHORITY_VERIFIED (Official Registry)</span>
          </div>
        </div>

        {/* Review Signals / Governance Flags Table */}
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Neutral Review Signals (Review Triggers Only)</h2>
              <p className="text-xs text-slate-500">Flags indicate items needing administrative inspection, not definitive fraud.</p>
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="text-xs border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500"
              >
                <option value="ALL">All Severities</option>
                <option value="HIGH">High Severity</option>
                <option value="MEDIUM">Medium Severity</option>
                <option value="LOW">Low Severity</option>
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider text-left">
                <tr>
                  <th className="px-6 py-3">Flag Type</th>
                  <th className="px-6 py-3">Target Entity</th>
                  <th className="px-6 py-3">Severity</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Logged At</th>
                  <th className="px-6 py-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filteredFlags.length > 0 ? (
                  filteredFlags.map((flag) => (
                    <tr key={flag.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-slate-900">
                        {flag.flag_type}
                      </td>
                      <td className="px-6 py-4 text-slate-500">
                        <span className="font-mono text-xs">{flag.entity_type}:{flag.entity_id.slice(0, 8)}...</span>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${
                          flag.severity === "HIGH" ? "bg-rose-100 text-rose-700" :
                          flag.severity === "MEDIUM" ? "bg-amber-100 text-amber-700" :
                          "bg-slate-100 text-slate-700"
                        }`}>
                          {flag.severity}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-500">
                        <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                          {flag.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-slate-500 text-xs">
                        {new Date(flag.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link
                          href={`/admin/provenance?entity_type=${flag.entity_type}&entity_id=${flag.entity_id}`}
                          className="text-teal-600 hover:text-teal-900 text-xs font-medium inline-flex items-center gap-1"
                        >
                          Audit Lineage <ArrowRight className="h-3 w-3" />
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-slate-400">
                      {loading ? "Loading review signals..." : "No active review signals matching selection."}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
