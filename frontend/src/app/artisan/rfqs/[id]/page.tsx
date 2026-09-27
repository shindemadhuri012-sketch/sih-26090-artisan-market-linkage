"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Package,
  Send,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  Check,
  X,
  RefreshCw
} from "lucide-react";

export default function ArtisanRFQDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [rfq, setRfq] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [responseAction, setResponseAction] = useState<"ACCEPT" | "DECLINE" | "COUNTER_OFFER" | null>(null);

  // Counter offer state
  const [counterPrice, setCounterPrice] = useState<string>("");
  const [counterLeadDays, setCounterLeadDays] = useState<number>(21);
  const [responseMessage, setResponseMessage] = useState<string>("");
  const [declineReason, setDeclineReason] = useState<string>("Production capacity currently committed");

  useEffect(() => {
    if (id) {
      loadAndMarkViewed();
    }
  }, [id]);

  const loadAndMarkViewed = async () => {
    setLoading(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      // 1. Get RFQ detail
      const res = await fetch(`/api/v1/rfqs/${id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (!res.ok) throw new Error("Failed to load RFQ");
      const data = await res.json();
      setRfq(data);
      setCounterPrice(String(data.proposed_unit_price));

      // 2. Mark viewed if SENT
      if (data.status === "SENT") {
        await fetch(`/api/v1/rfqs/${id}/view`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
      }
    } catch (err) {
      console.error("Error loading RFQ:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!responseAction) return;
    setSubmitting(true);

    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch(`/api/v1/rfqs/${id}/respond`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          action: responseAction,
          counter_unit_price: responseAction === "COUNTER_OFFER" ? Number(counterPrice) : null,
          counter_lead_time_days: responseAction === "COUNTER_OFFER" ? Number(counterLeadDays) : null,
          artisan_response_message: responseMessage,
          decline_reason: responseAction === "DECLINE" ? declineReason : null
        })
      });

      if (!res.ok) throw new Error("Failed to submit response");
      const updated = await res.json();
      setRfq(updated);
      setResponseAction(null);
    } catch (err: any) {
      alert(err.message || "Failed to submit response");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!rfq) {
    return (
      <div className="min-h-screen bg-slate-50 p-8 text-center">
        <p className="text-slate-600">RFQ not found.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/artisan/rfqs"
              className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <span>{rfq.rfq_reference_number || "RFQ Details"}</span>
                <span className="text-xs bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded-full">
                  Status: {rfq.status}
                </span>
              </h1>
              <p className="text-xs text-slate-500">
                From: {rfq.buyer_company_name || "Institutional Buyer"} | Received: {new Date(rfq.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* RFQ Terms Summary */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <h2 className="font-semibold text-slate-800 text-base">Buyer's Commercial Procurement Terms</h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-50 rounded-xl">
            <div>
              <p className="text-xs text-slate-400">Order Volume</p>
              <p className="font-bold text-slate-800 text-lg">{rfq.proposed_quantity} units</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Offered Unit Price</p>
              <p className="font-bold text-slate-800 text-lg">₹{rfq.proposed_unit_price}</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Total Order Value</p>
              <p className="font-bold text-emerald-700 text-lg">
                ₹{(rfq.proposed_quantity * Number(rfq.proposed_unit_price)).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Currency</p>
              <p className="font-bold text-slate-800 text-lg">{rfq.currency || "INR"}</p>
            </div>
          </div>

          <div>
            <p className="text-xs text-slate-400 mb-1">Buyer Message & Specifications</p>
            <p className="text-sm text-slate-700 bg-white border border-slate-200 p-4 rounded-xl leading-relaxed">
              "{rfq.message}"
            </p>
          </div>
        </div>

        {/* Status Actions */}
        {rfq.status === "ACCEPTED" ? (
          <div className="p-6 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3 text-emerald-800">
            <CheckCircle2 className="w-6 h-6 text-emerald-600 shrink-0" />
            <div>
              <h3 className="font-bold text-sm">Agreement Confirmed!</h3>
              <p className="text-xs text-emerald-700">
                You have accepted this commercial order at ₹{rfq.proposed_unit_price} / unit for {rfq.proposed_quantity} units.
              </p>
            </div>
          </div>
        ) : rfq.status === "DECLINED" ? (
          <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
            <h3 className="font-bold text-sm mb-1">RFQ Declined</h3>
            <p>Reason: {rfq.decline_reason}</p>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
            <h2 className="font-semibold text-slate-800 text-base">Respond to Buyer</h2>

            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setResponseAction("ACCEPT")}
                className={`px-5 py-2.5 rounded-xl font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-sm ${
                  responseAction === "ACCEPT" ? "bg-emerald-600 text-white" : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                }`}
              >
                <Check className="w-4 h-4" />
                <span>Accept Stated Terms</span>
              </button>

              <button
                type="button"
                onClick={() => setResponseAction("COUNTER_OFFER")}
                className={`px-5 py-2.5 rounded-xl font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-sm ${
                  responseAction === "COUNTER_OFFER" ? "bg-amber-600 text-white" : "bg-amber-50 text-amber-700 hover:bg-amber-100"
                }`}
              >
                <span>Propose Counter-Offer</span>
              </button>

              <button
                type="button"
                onClick={() => setResponseAction("DECLINE")}
                className={`px-5 py-2.5 rounded-xl font-semibold text-xs transition-colors flex items-center gap-1.5 shadow-sm ${
                  responseAction === "DECLINE" ? "bg-rose-600 text-white" : "bg-rose-50 text-rose-700 hover:bg-rose-100"
                }`}
              >
                <X className="w-4 h-4" />
                <span>Decline Order</span>
              </button>
            </div>

            {responseAction && (
              <form onSubmit={handleRespond} className="space-y-4 pt-4 border-t border-slate-100">
                {responseAction === "COUNTER_OFFER" && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Your Counter Unit Price (₹ / unit)
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        required
                        value={counterPrice}
                        onChange={(e) => setCounterPrice(e.target.value)}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 mb-1">
                        Turnaround Delivery Lead Time (Days)
                      </label>
                      <input
                        type="number"
                        required
                        min={1}
                        value={counterLeadDays}
                        onChange={(e) => setCounterLeadDays(Number(e.target.value))}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                      />
                    </div>
                  </div>
                )}

                {responseAction === "DECLINE" && (
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Reason for Declining</label>
                    <select
                      value={declineReason}
                      onChange={(e) => setDeclineReason(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                    >
                      <option value="Production capacity currently committed">Production capacity currently committed</option>
                      <option value="Raw material unavailable in required quantity">Raw material unavailable in required quantity</option>
                      <option value="Offered price below sustainable production cost">Offered price below sustainable production cost</option>
                      <option value="Requested lead time infeasible">Requested lead time infeasible</option>
                    </select>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Response Message to Buyer</label>
                  <textarea
                    rows={3}
                    placeholder="Enter any notes, clarification, or shipping considerations..."
                    value={responseMessage}
                    onChange={(e) => setResponseMessage(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                  />
                </div>

                <div className="flex justify-end gap-2">
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm"
                  >
                    {submitting ? "Transmitting..." : "Submit Response to Buyer"}
                  </button>
                </div>
              </form>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
