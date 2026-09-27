"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Package,
  Send,
  CheckCircle2,
  Clock,
  AlertCircle,
  Eye,
  ArrowRight,
  RefreshCw,
  Plus
} from "lucide-react";

export default function BuyerSentRFQsPage() {
  const [rfqs, setRfqs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSentRFQs();
  }, []);

  const loadSentRFQs = async () => {
    setLoading(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch("/api/v1/rfqs/sent", {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setRfqs(data);
      }
    } catch (err) {
      console.error("Error loading sent RFQs:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (rfqId: string, action: "ACCEPT" | "DECLINE") => {
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch(`/api/v1/rfqs/${rfqId}/buyer-decision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ action })
      });
      if (res.ok) {
        await loadSentRFQs();
      }
    } catch (err) {
      console.error("Error submitting decision:", err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <span>Sent Procurement RFQs</span>
              <span className="text-xs bg-indigo-50 text-indigo-700 font-semibold px-2 py-0.5 rounded-full border border-indigo-200">
                Commercial Linkage
              </span>
            </h1>
            <p className="text-xs text-slate-500">Track dispatched RFQs, counter-offers, and agreed production terms</p>
          </div>

          <Link
            href="/buyer/requirements/new"
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Plus className="w-4 h-4" />
            <span>Post New Brief</span>
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading sent RFQs...</div>
        ) : rfqs.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3">
            <Package className="w-10 h-10 text-slate-300 mx-auto" />
            <h3 className="font-bold text-slate-800 text-base">No RFQs Sent Yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Post a procurement requirement and find matching artisan candidates to send direct commercial RFQs.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {rfqs.map((rfq) => {
              const statusColors: Record<string, string> = {
                SENT: "bg-blue-100 text-blue-800 border-blue-200",
                VIEWED: "bg-purple-100 text-purple-800 border-purple-200",
                NEGOTIATION: "bg-amber-100 text-amber-800 border-amber-200",
                ACCEPTED: "bg-emerald-100 text-emerald-800 border-emerald-200",
                DECLINED: "bg-rose-100 text-rose-800 border-rose-200"
              };

              return (
                <div key={rfq.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md">
                        {rfq.rfq_reference_number || "RFQ-PENDING"}
                      </span>
                      <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${statusColors[rfq.status] || "bg-slate-100 text-slate-700 border-slate-200"}`}>
                        {rfq.status}
                      </span>
                    </div>
                    <span className="text-xs text-slate-400">
                      Dispatched: {new Date(rfq.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-1">
                    <div>
                      <p className="text-slate-400">Target Artisan</p>
                      <p className="font-bold text-slate-800">{rfq.artisan_name || "Artisan"}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Proposed Quantity</p>
                      <p className="font-bold text-slate-800">{rfq.proposed_quantity} units</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Unit Price</p>
                      <p className="font-bold text-slate-800">₹{rfq.proposed_unit_price}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Total Proposed Value</p>
                      <p className="font-bold text-indigo-600">
                        ₹{(rfq.proposed_quantity * Number(rfq.proposed_unit_price)).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg">
                    "{rfq.message}"
                  </p>

                  {/* Negotiation Block */}
                  {rfq.status === "NEGOTIATION" && (
                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-900">Artisan Submitted Counter-Offer:</span>
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleDecision(rfq.id, "ACCEPT")}
                            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-md shadow-sm"
                          >
                            Accept Counter-Offer
                          </button>
                          <button
                            onClick={() => handleDecision(rfq.id, "DECLINE")}
                            className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white font-semibold rounded-md shadow-sm"
                          >
                            Decline
                          </button>
                        </div>
                      </div>
                      <p className="text-amber-800">
                        Counter Price: <strong>₹{rfq.counter_unit_price}</strong> | Lead Time: <strong>{rfq.counter_lead_time_days} days</strong>
                      </p>
                      {rfq.artisan_response_message && (
                        <p className="text-amber-700 italic">"{rfq.artisan_response_message}"</p>
                      )}
                    </div>
                  )}

                  {rfq.status === "ACCEPTED" && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Commercial agreement reached with artisan at ₹{rfq.proposed_unit_price}/unit. Ready for fulfillment linkage.</span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
