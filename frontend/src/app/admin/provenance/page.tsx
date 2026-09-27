"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  GitCommit, 
  ShieldCheck, 
  ShieldAlert, 
  Search, 
  ArrowLeft,
  CheckCircle,
  Hash,
  UserCheck,
  Clock
} from "lucide-react";

interface ProvenanceEventItem {
  id: string;
  field_name: string;
  previous_value_json: any;
  new_value_json: any;
  provenance_state: string;
  actor_user_id?: string;
  actor_role: string;
  change_reason?: string;
  evidence_reference?: string;
  human_confirmation_status: boolean;
  event_hash: string;
  previous_event_hash: string;
  sequence_number: number;
  created_at: string;
}

interface VerificationResult {
  is_valid: boolean;
  total_events: number;
  latest_sequence?: number;
  tampered_event_id?: string;
  tamper_reason?: string;
  message: string;
}

export default function ProvenanceInspectorPage() {
  const [entityType, setEntityType] = useState<string>("Product");
  const [entityId, setEntityId] = useState<string>("");
  const [events, setEvents] = useState<ProvenanceEventItem[]>([]);
  const [verifyResult, setVerifyResult] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [verifying, setVerifying] = useState<boolean>(false);

  const fetchTimeline = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!entityId.trim()) return;

    setLoading(true);
    setVerifyResult(null);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    try {
      const res = await fetch(`/api/v1/governance/provenance/timeline/${entityType}/${entityId.trim()}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      } else {
        setEvents([]);
      }
    } catch (err) {
      console.error(err);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const verifyChain = async () => {
    if (!entityId.trim()) return;
    setVerifying(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    try {
      const res = await fetch(`/api/v1/governance/provenance/verify-chain/${entityType}/${entityId.trim()}`, { headers });
      if (res.ok) {
        const result = await res.json();
        setVerifyResult(result);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
              <Link href="/admin/governance" className="hover:text-slate-700 flex items-center gap-1">
                <ArrowLeft className="h-4 w-4" /> Governance
              </Link>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <GitCommit className="h-6 w-6 text-teal-600" />
              Cryptographic Provenance Inspector
            </h1>
          </div>
        </div>

        {/* Search Bar */}
        <form onSubmit={fetchTimeline} className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3">
          <select
            value={entityType}
            onChange={(e) => setEntityType(e.target.value)}
            className="text-sm border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500"
          >
            <option value="Product">Product</option>
            <option value="ArtisanProfile">ArtisanProfile</option>
            <option value="CraftPassport">CraftPassport</option>
            <option value="Verification">Verification</option>
          </select>
          <input
            type="text"
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            placeholder="Enter Entity UUID (e.g. 550e8400-e29b-41d4-a716-446655440000)"
            className="flex-1 text-sm border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500 font-mono"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm rounded-md shadow-sm flex items-center gap-2 justify-center"
          >
            <Search className="h-4 w-4" />
            {loading ? "Searching..." : "Inspect Lineage"}
          </button>
        </form>

        {/* Cryptographic Verification Banner */}
        {events.length > 0 && (
          <div className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-slate-900">
                Ledger Contains {events.length} Hash-Chained Revisions
              </p>
              <p className="text-xs text-slate-500">
                Validates sequential integrity, non-repudiation, and SHA-256 signatures.
              </p>
            </div>
            <button
              onClick={verifyChain}
              disabled={verifying}
              className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white font-medium text-xs rounded-md shadow-sm flex items-center gap-2 self-start sm:self-auto"
            >
              <ShieldCheck className="h-4 w-4 text-emerald-400" />
              {verifying ? "Verifying SHA-256 Chain..." : "Verify Hash Chain"}
            </button>
          </div>
        )}

        {/* Verification Result Alert */}
        {verifyResult && (
          <div className={`p-4 rounded-md border text-sm flex items-start gap-3 ${
            verifyResult.is_valid
              ? "bg-emerald-50 border-emerald-200 text-emerald-900"
              : "bg-rose-50 border-rose-200 text-rose-900"
          }`}>
            {verifyResult.is_valid ? (
              <CheckCircle className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <ShieldAlert className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
            )}
            <div>
              <p className="font-semibold">{verifyResult.is_valid ? "Cryptographic Chain Intact" : "Tamper Alert: Chain Broken"}</p>
              <p className="text-xs mt-0.5">{verifyResult.message}</p>
              {verifyResult.tamper_reason && (
                <p className="text-xs font-mono mt-1 text-rose-700 bg-rose-100 p-1.5 rounded">
                  {verifyResult.tamper_reason}
                </p>
              )}
            </div>
          </div>
        )}

        {/* Events Timeline */}
        {events.length > 0 ? (
          <div className="space-y-4">
            {events.map((ev) => (
              <div key={ev.id} className="bg-white p-5 rounded-lg border border-slate-200 shadow-sm relative">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
                  <div className="flex items-center gap-2">
                    <span className="h-6 w-6 rounded-full bg-teal-100 text-teal-800 font-bold text-xs flex items-center justify-center">
                      #{ev.sequence_number}
                    </span>
                    <span className="font-semibold text-sm text-slate-900">
                      Modified field: <code className="text-teal-700 bg-teal-50 px-1 rounded">{ev.field_name}</code>
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 text-slate-700">
                      {ev.provenance_state}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-xs text-slate-400">
                    <Clock className="h-3 w-3" />
                    {new Date(ev.created_at).toLocaleString()}
                  </div>
                </div>

                {/* Diff Viewer */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 my-3 text-xs font-mono">
                  <div className="p-3 bg-rose-50 border border-rose-100 rounded text-rose-900">
                    <p className="font-sans font-bold text-[10px] text-rose-700 uppercase mb-1">Previous Value</p>
                    <pre className="whitespace-pre-wrap break-all">{JSON.stringify(ev.previous_value_json, null, 2) || "null"}</pre>
                  </div>
                  <div className="p-3 bg-emerald-50 border border-emerald-100 rounded text-emerald-900">
                    <p className="font-sans font-bold text-[10px] text-emerald-700 uppercase mb-1">New Value</p>
                    <pre className="whitespace-pre-wrap break-all">{JSON.stringify(ev.new_value_json, null, 2)}</pre>
                  </div>
                </div>

                {/* Metadata Footer */}
                <div className="pt-2 border-t border-slate-100 flex flex-wrap items-center justify-between text-xs text-slate-500 gap-2">
                  <div className="flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <UserCheck className="h-3.5 w-3.5 text-slate-400" />
                      Actor: <span className="font-semibold">{ev.actor_role}</span>
                    </span>
                    {ev.change_reason && (
                      <span>Reason: {ev.change_reason}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 font-mono text-[10px] text-slate-400">
                    <Hash className="h-3 w-3" />
                    Hash: {ev.event_hash.slice(0, 16)}...
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          !loading && entityId && (
            <div className="bg-white p-8 rounded-lg border border-slate-200 text-center text-slate-400 text-sm">
              No historical provenance records found for this entity ID.
            </div>
          )
        )}
      </div>
    </div>
  );
}
