"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  ShieldCheck, 
  RotateCcw,
  Clock,
  Layers,
  ArrowLeft
} from "lucide-react";

interface QueueItem {
  entity_type: string;
  entity_id: string;
  title: string;
  artisan_id?: string;
  artisan_name?: string;
  craft_name?: string;
  price_inr?: string;
  status: string;
  submitted_at: string;
}

export default function ModerationQueuePage() {
  const [activeTab, setActiveTab] = useState<"PRODUCT" | "VERIFICATION" | "PASSPORT">("PRODUCT");
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedItem, setSelectedItem] = useState<QueueItem | null>(null);

  // Decision Form State
  const [decision, setDecision] = useState<"APPROVE" | "REQUEST_CHANGES" | "REJECT">("APPROVE");
  const [reasonCategory, setReasonCategory] = useState<string>("AUTHENTICITY_VERIFIED");
  const [moderatorNotes, setModeratorNotes] = useState<string>("");
  const [feedbackToUser, setFeedbackToUser] = useState<string>("");
  const [evidenceReference, setEvidenceReference] = useState<string>("");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchQueue = (tab: "PRODUCT" | "VERIFICATION" | "PASSPORT") => {
    setLoading(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

    fetch(`/api/v1/moderation/queue?entity_type=${tab}&page=1&page_size=20`, { headers })
      .then(res => res.ok ? res.json() : { items: [] })
      .then(data => setQueue(data.items || []))
      .catch(err => console.error("Error fetching queue:", err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchQueue(activeTab);
    setSelectedItem(null);
    setActionSuccess(null);
  }, [activeTab]);

  const handleSubmitDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem) return;

    setSubmitting(true);
    setActionSuccess(null);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    };

    // Client idempotency key
    const idempotencyKey = `MOD-${selectedItem.entity_type}-${selectedItem.entity_id}-${Date.now()}`;

    try {
      const res = await fetch("/api/v1/moderation/review", {
        method: "POST",
        headers,
        body: JSON.stringify({
          entity_type: selectedItem.entity_type,
          entity_id: selectedItem.entity_id,
          decision,
          reason_category: reasonCategory,
          moderator_notes: moderatorNotes || null,
          feedback_to_user: feedbackToUser || null,
          evidence_reference: evidenceReference || null,
          idempotency_key: idempotencyKey
        })
      });

      if (res.ok) {
        setActionSuccess(`Successfully recorded decision ${decision} on ${selectedItem.title}.`);
        setSelectedItem(null);
        fetchQueue(activeTab);
      } else {
        const err = await res.json();
        alert(`Error recording decision: ${err.detail || "Submission failed"}`);
      }
    } catch (err) {
      console.error(err);
      alert("Network error processing decision.");
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
              <Layers className="h-6 w-6 text-teal-600" />
              Unified Moderation Console
            </h1>
          </div>
        </div>

        {actionSuccess && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-md text-emerald-800 text-sm flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-emerald-600" />
            {actionSuccess}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 space-x-8">
          {(["PRODUCT", "VERIFICATION", "PASSPORT"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab
                  ? "border-teal-600 text-teal-600"
                  : "border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300"
              }`}
            >
              {tab === "PRODUCT" && "Product Listings"}
              {tab === "VERIFICATION" && "Artisan KYC / Credentials"}
              {tab === "PASSPORT" && "Craft Passports"}
            </button>
          ))}
        </div>

        {/* Layout: Queue List + Decision Panel */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Queue Column */}
          <div className="lg:col-span-7 bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200">
              <h2 className="text-base font-semibold text-slate-900">
                Submissions Awaiting Moderation ({queue.length})
              </h2>
            </div>
            <div className="divide-y divide-slate-200">
              {loading ? (
                <div className="p-8 text-center text-slate-400 text-sm">Loading queue submissions...</div>
              ) : queue.length === 0 ? (
                <div className="p-8 text-center text-slate-400 text-sm">No items pending review in this queue.</div>
              ) : (
                queue.map((item) => (
                  <div
                    key={item.entity_id}
                    onClick={() => setSelectedItem(item)}
                    className={`p-4 cursor-pointer hover:bg-slate-50 transition-colors ${
                      selectedItem?.entity_id === item.entity_id ? "bg-teal-50 border-l-4 border-teal-600" : ""
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-medium text-slate-900 text-sm">{item.title}</p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          By <span className="font-semibold text-slate-700">{item.artisan_name}</span>
                          {item.craft_name && ` • Craft: ${item.craft_name}`}
                          {item.price_inr && ` • ₹${item.price_inr}`}
                        </p>
                      </div>
                      <span className="px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">
                        {item.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-slate-400 mt-2">
                      <Clock className="h-3 w-3" />
                      Submitted {new Date(item.submitted_at).toLocaleString()}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Decision Panel */}
          <div className="lg:col-span-5 bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            {selectedItem ? (
              <form onSubmit={handleSubmitDecision} className="space-y-5">
                <h3 className="text-base font-bold text-slate-900 border-b border-slate-200 pb-2">
                  Review: {selectedItem.title}
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
                      onClick={() => setDecision("REQUEST_CHANGES")}
                      className={`py-2 px-3 text-xs font-semibold rounded border ${
                        decision === "REQUEST_CHANGES"
                          ? "bg-amber-500 text-white border-amber-500"
                          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      Request Changes
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
                    Reason Category
                  </label>
                  <select
                    value={reasonCategory}
                    onChange={(e) => setReasonCategory(e.target.value)}
                    className="w-full text-sm border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500"
                  >
                    <option value="AUTHENTICITY_VERIFIED">Authenticity & Credentials Verified</option>
                    <option value="QUALITY_DEFICIENCY">Quality / Image Deficiency</option>
                    <option value="INCORRECT_ATTRIBUTES">Incorrect Craft or Material Attributes</option>
                    <option value="POLICY_VIOLATION">Commercial / Non-Craft Policy Violation</option>
                    <option value="OTHER">Other Specific Feedback</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 uppercase tracking-wider mb-1">
                    Feedback to Artisan (Public / User-Facing)
                  </label>
                  <textarea
                    rows={2}
                    value={feedbackToUser}
                    onChange={(e) => setFeedbackToUser(e.target.value)}
                    placeholder="Clear instructions explaining what to rectify if changes are requested..."
                    className="w-full text-xs border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 uppercase tracking-wider mb-1">
                    Authoritative Registry Evidence Reference
                  </label>
                  <input
                    type="text"
                    value={evidenceReference}
                    onChange={(e) => setEvidenceReference(e.target.value)}
                    placeholder="e.g. CGPDTM-GI-AU-2026-CHANDERI-042 (Required for AUTHORITY_VERIFIED)"
                    className="w-full text-xs border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500 font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Approval without verified registry evidence grants ADMIN_REVIEWED only.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 uppercase tracking-wider mb-1">
                    Internal Moderator Notes (Private)
                  </label>
                  <textarea
                    rows={2}
                    value={moderatorNotes}
                    onChange={(e) => setModeratorNotes(e.target.value)}
                    placeholder="Audited reviewer observations..."
                    className="w-full text-xs border-slate-300 rounded-md focus:ring-teal-500 focus:border-teal-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="w-full py-2.5 px-4 bg-teal-600 hover:bg-teal-700 text-white font-medium text-sm rounded-md shadow-sm disabled:opacity-50"
                >
                  {submitting ? "Committing Decision..." : "Commit Moderation Decision"}
                </button>
              </form>
            ) : (
              <div className="p-8 text-center text-slate-400 text-sm">
                Select an item from the queue to inspect and moderate.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
