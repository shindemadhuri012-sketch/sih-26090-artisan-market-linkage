"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  FileCheck, 
  ShieldCheck, 
  ExternalLink, 
  Clock, 
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertTriangle
} from "lucide-react";

interface VerificationItem {
  id: string;
  artisan_id: string;
  verifier_user_id?: string;
  document_type: string;
  document_url: string;
  verification_status: string;
  rejection_reason?: string;
  admin_notes?: string;
  decision_date?: string;
  verified_at?: string;
  created_at: string;
}

export default function VerificationReviewPage() {
  const [verifications, setVerifications] = useState<VerificationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedVerif, setSelectedVerif] = useState<VerificationItem | null>(null);

  // Review Form
  const [decision, setDecision] = useState<"APPROVE" | "REQUEST_CORRECTION" | "REJECT">("APPROVE");
  const [adminNotes, setAdminNotes] = useState<string>("");
  const [rejectionReason, setRejectionReason] = useState<string>("");
  const [authoritativeReference, setAuthoritativeReference] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fetchPending = () => {
    setLoading(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    fetch("/api/v1/verifications/admin/pending", { headers })
      .then(res => res.ok ? res.json() : [])
      .then(data => setVerifications(data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedVerif) return;

    setSubmitting(true);
    setSuccessMsg(null);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    };

    try {
      const res = await fetch(`/api/v1/verifications/admin/${selectedVerif.id}/review`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          decision,
          admin_notes: adminNotes,
          rejection_reason: rejectionReason || null,
          authoritative_registry_reference: authoritativeReference || null
        })
      });

      if (res.ok) {
        setSuccessMsg(`Successfully processed verification ${selectedVerif.document_type}.`);
        setSelectedVerif(null);
        fetchPending();
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail || "Submission failed"}`);
      }
    } catch (err) {
      console.error(err);
      alert("Network error.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 pb-4">
          <div>
            <div className="flex items-center gap-2 text-sm text-slate-500 mb-1">
              <Link href="/admin/governance" className="hover:text-slate-700 flex items-center gap-1">
                <ArrowLeft className="h-4 w-4" /> Governance
              </Link>
            </div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <FileCheck className="h-6 w-6 text-teal-600" />
              Credential & Verification Review Console
            </h1>
          </div>
        </div>

        {successMsg && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 text-sm flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-emerald-600" />
            {successMsg}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* List Column */}
          <div className="lg:col-span-7 bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200">
              <h2 className="text-base font-semibold text-slate-900">
                Submissions Pending Verification ({verifications.length})
              </h2>
            </div>
            <div className="divide-y divide-slate-200">
              {loading ? (
                <div className="p-8 text-center text-slate-400 text-sm">Loading submissions...</div>
              ) : verifications.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-sm">No verification documents pending review.</div>
              ) : (
                verifications.map((v) => (
                  <div
                    key={v.id}
                    onClick={() => setSelectedVerif(v)}
                    className={`p-4 cursor-pointer hover:bg-slate-50 transition-colors ${
                      selectedVerif?.id === v.id ? "bg-teal-50 border-l-4 border-teal-600" : ""
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold text-slate-900 text-sm">{v.document_type}</p>
                        <p className="text-xs text-slate-500 font-mono mt-0.5">Artisan ID: {v.artisan_id.slice(0, 13)}...</p>
                      </div>
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
                        {v.verification_status}
                      </span>
                    </div>
                    <div className="flex items-center justify-between text-xs text-slate-400 mt-2">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" /> Submitted {new Date(v.created_at).toLocaleDateString()}
                      </span>
                      <a
                        href={v.document_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-teal-600 hover:text-teal-800 flex items-center gap-1 font-medium"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Inspect Proof <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Form Column */}
          <div className="lg:col-span-5 bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            {selectedVerif ? (
              <form onSubmit={handleReviewSubmit} className="space-y-5">
                <h3 className="text-base font-bold text-slate-900 border-b border-slate-200 pb-2">
                  Review Submission: {selectedVerif.document_type}
                </h3>

                <div>
                  <label className="block text-xs font-medium text-slate-700 uppercase tracking-wider mb-1">
                    Decision
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    <button
                      type="button"
                      onClick={() => setDecision("APPROVE")}
                      className={`py-2 px-3 text-xs font-semibold rounded border ${
                        decision === "APPROVE"
                          ? "bg-emerald-600 text-white border-emerald-600"
                          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      onClick={() => setDecision("REQUEST_CORRECTION")}
                      className={`py-2 px-3 text-xs font-semibold rounded border ${
                        decision === "REQUEST_CORRECTION"
                          ? "bg-amber-500 text-white border-amber-500"
                          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      Request Fix
                    </button>
                    <button
                      type="button"
                      onClick={() => setDecision("REJECT")}
                      className={`py-2 px-3 text-xs font-semibold rounded border ${
                        decision === "REJECT"
                          ? "bg-rose-600 text-white border-rose-600"
                          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      Reject
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 uppercase tracking-wider mb-1">
                    Authoritative Registry Reference (Optional)
                  </label>
                  <input
                    type="text"
                    value={authoritativeReference}
                    onChange={(e) => setAuthoritativeReference(e.target.value)}
                    placeholder="e.g. CGPDTM-GI-AU-2026-CHANDERI-042"
                    className="w-full text-xs border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Required to grant AUTHORITY_VERIFIED. Without reference, approval grants ADMIN_REVIEWED.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 uppercase tracking-wider mb-1">
                    Audited Admin Commentary (Required, min 5 chars)
                  </label>
                  <textarea
                    rows={3}
                    required
                    value={adminNotes}
                    onChange={(e) => setAdminNotes(e.target.value)}
                    placeholder="Details of registry verification check or inspected document details..."
                    className="w-full text-xs border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500"
                  />
                </div>

                {decision !== "APPROVE" && (
                  <div>
                    <label className="block text-xs font-medium text-slate-700 uppercase tracking-wider mb-1">
                      Reason for Rejection / Correction Request
                    </label>
                    <textarea
                      rows={2}
                      value={rejectionReason}
                      onChange={(e) => setRejectionReason(e.target.value)}
                      placeholder="Feedback delivered to artisan..."
                      className="w-full text-xs border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500"
                    />
                  </div>
                )}

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm rounded-md shadow-sm disabled:opacity-50"
                >
                  {submitting ? "Committing Review..." : "Commit Verification Decision"}
                </button>
              </form>
            ) : (
              <div className="p-8 text-center text-slate-400 text-sm">
                Select a verification submission to inspect and review.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
