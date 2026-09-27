"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Search,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Send,
  RefreshCw,
  Sliders,
  Package,
  Layers,
  Clock,
  IndianRupee,
  ChevronRight,
  ExternalLink,
  X
} from "lucide-react";

export default function BuyerRequirementMatchesPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [selectedMatch, setSelectedMatch] = useState<any | null>(null);
  const [rfqModalOpen, setRfqModalOpen] = useState(false);

  // RFQ form state
  const [rfqQuantity, setRfqQuantity] = useState<number>(50);
  const [rfqUnitPrice, setRfqUnitPrice] = useState<string>("1500");
  const [rfqMessage, setRfqMessage] = useState<string>("");
  const [submittingRfq, setSubmittingRfq] = useState(false);
  const [rfqSuccess, setRfqSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadMatches();
    }
  }, [id]);

  const loadMatches = async () => {
    setLoading(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch(`/api/v1/matches/requirements/${id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setMatches(data);
      }
    } catch (err) {
      console.error("Error loading matches:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunMatches = async () => {
    setRunning(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch(`/api/v1/matches/requirements/${id}/run`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setMatches(data);
      }
    } catch (err) {
      console.error("Error running matching engine:", err);
    } finally {
      setRunning(false);
    }
  };

  const openRfqModal = (match: any) => {
    setSelectedMatch(match);
    setRfqUnitPrice(match.product_price_inr ? String(match.product_price_inr) : "1500");
    setRfqMessage(`Interested in initiating commercial procurement based on Match #${match.rank} evaluation.`);
    setRfqModalOpen(true);
    setRfqSuccess(null);
  };

  const handleSendRfq = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedMatch) return;
    setSubmittingRfq(true);

    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch("/api/v1/rfqs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          requirement_id: id,
          artisan_id: selectedMatch.artisan_id,
          product_id: selectedMatch.product_id,
          match_id: selectedMatch.id,
          proposed_quantity: Number(rfqQuantity),
          proposed_unit_price: Number(rfqUnitPrice),
          message: rfqMessage
        })
      });

      if (!res.ok) throw new Error("Failed to dispatch RFQ");
      const rfqData = await res.json();
      setRfqSuccess(`RFQ successfully dispatched (${rfqData.rfq_reference_number}).`);
      setTimeout(() => {
        setRfqModalOpen(false);
        router.push("/buyer/rfqs");
      }, 1500);
    } catch (err: any) {
      alert(err.message || "Error sending RFQ");
    } finally {
      setSubmittingRfq(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href={`/buyer/requirements/${id}`}
              className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <span>Explainable Match Candidates</span>
                <span className="text-xs bg-indigo-50 text-indigo-700 font-semibold px-2 py-0.5 rounded-full border border-indigo-200">
                  MATCHING_ENGINE_V1
                </span>
              </h1>
              <p className="text-xs text-slate-500">
                Ranked by multi-criteria compatibility, vector semantics, and verified artisan credentials
              </p>
            </div>
          </div>

          <button
            onClick={handleRunMatches}
            disabled={running}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl transition-colors flex items-center gap-2 shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${running ? "animate-spin" : ""}`} />
            <span>{running ? "Scoring Candidates..." : "Re-Run Matching Engine"}</span>
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading match candidates...</div>
        ) : matches.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-4">
            <Search className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="font-bold text-slate-800 text-lg">No Matching Candidates Found Yet</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Run the matching engine to evaluate published artisan products against this brief.
            </p>
            <button
              onClick={handleRunMatches}
              disabled={running}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl shadow-sm"
            >
              Run Matching Pipeline Now
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Matches List */}
            <div className="lg:col-span-2 space-y-4">
              {matches.map((m) => {
                const scorePct = Math.round(m.composite_score * 100);
                const isTop = m.rank === 1;

                return (
                  <div
                    key={m.id}
                    className={`bg-white border rounded-xl p-5 shadow-sm transition-all hover:border-indigo-300 ${
                      isTop ? "border-indigo-200 bg-gradient-to-r from-indigo-50/30 to-transparent" : "border-slate-200"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4 mb-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                            Rank #{m.rank}
                          </span>
                          <span
                            className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${
                              scorePct >= 85
                                ? "bg-emerald-100 text-emerald-800"
                                : scorePct >= 70
                                ? "bg-indigo-100 text-indigo-800"
                                : "bg-amber-100 text-amber-800"
                            }`}
                          >
                            {scorePct}% Match Score
                          </span>
                          <span className="text-xs text-slate-400 font-medium">
                            {m.data_sufficiency_state}
                          </span>
                        </div>
                        <h3 className="font-bold text-slate-900 text-base">
                          {m.product_title || "Artisan Capacity Profile"}
                        </h3>
                        <p className="text-xs text-slate-500">
                          {m.artisan_name} | {m.artisan_district}, {m.artisan_state}
                        </p>
                      </div>

                      <button
                        onClick={() => openRfqModal(m)}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shrink-0 shadow-sm"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>Send RFQ</span>
                      </button>
                    </div>

                    {/* Score Breakdown Sliders */}
                    <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 my-3 p-3 bg-slate-50 rounded-lg text-center text-xs">
                      <div>
                        <p className="text-slate-400 text-[10px]">Semantic</p>
                        <p className="font-bold text-slate-700">{Math.round(m.semantic_similarity * 100)}%</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-[10px]">Craft</p>
                        <p className="font-bold text-slate-700">{Math.round(m.craft_compatibility * 100)}%</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-[10px]">Material</p>
                        <p className="font-bold text-slate-700">{Math.round(m.material_compatibility * 100)}%</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-[10px]">Capacity</p>
                        <p className="font-bold text-slate-700">{Math.round(m.capacity_compatibility * 100)}%</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-[10px]">Price</p>
                        <p className="font-bold text-slate-700">{Math.round(m.price_compatibility * 100)}%</p>
                      </div>
                      <div>
                        <p className="text-slate-400 text-[10px]">Lead Time</p>
                        <p className="font-bold text-slate-700">{Math.round(m.lead_time_compatibility * 100)}%</p>
                      </div>
                    </div>

                    {/* Explanations Preview */}
                    <div className="space-y-1.5 text-xs">
                      {m.positive_reasons?.slice(0, 2).map((r: string, i: number) => (
                        <p key={i} className="text-emerald-700 flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                          <span>{r}</span>
                        </p>
                      ))}
                      {m.limitations?.slice(0, 1).map((l: string, i: number) => (
                        <p key={i} className="text-amber-700 flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                          <span>{l}</span>
                        </p>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Explainability Sidebar */}
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm h-fit space-y-4">
              <div className="flex items-center gap-2">
                <Sliders className="w-5 h-5 text-indigo-600" />
                <h3 className="font-semibold text-slate-800 text-sm">Matching Methodology</h3>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                The SIH 26090 engine calculates a multi-criteria <strong>MATCH SCORE</strong> using transparent weights:
              </p>
              <ul className="text-xs text-slate-500 space-y-2 border-t border-slate-100 pt-3">
                <li className="flex justify-between">
                  <span>Semantic Vector (768-dim)</span>
                  <span className="font-bold text-slate-700">25%</span>
                </li>
                <li className="flex justify-between">
                  <span>Craft & Taxonomy Proximity</span>
                  <span className="font-bold text-slate-700">20%</span>
                </li>
                <li className="flex justify-between">
                  <span>Material & Technique Overlap</span>
                  <span className="font-bold text-slate-700">15%</span>
                </li>
                <li className="flex justify-between">
                  <span>Production Capacity Fit</span>
                  <span className="font-bold text-slate-700">15%</span>
                </li>
                <li className="flex justify-between">
                  <span>Target Budget Compatibility</span>
                  <span className="font-bold text-slate-700">15%</span>
                </li>
                <li className="flex justify-between">
                  <span>Lead Time Delivery Buffer</span>
                  <span className="font-bold text-slate-700">10%</span>
                </li>
                <li className="flex justify-between text-indigo-600 font-semibold border-t border-slate-100 pt-1">
                  <span>GI & Pehchan Provenance Bonus</span>
                  <span>+5%</span>
                </li>
              </ul>
              <p className="text-[11px] text-slate-400 bg-slate-50 p-2.5 rounded-lg">
                Notice: Match scores represent structural and aesthetic attribute compatibility, not guaranteed purchase probability.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* RFQ Trigger Modal */}
      {rfqModalOpen && selectedMatch && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base">Initiate RFQ Enquiry</h3>
                <p className="text-xs text-slate-500">
                  To: {selectedMatch.artisan_name} (Rank #{selectedMatch.rank})
                </p>
              </div>
              <button
                onClick={() => setRfqModalOpen(false)}
                className="p-1 hover:bg-slate-100 rounded-lg text-slate-400"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {rfqSuccess ? (
              <div className="p-4 bg-emerald-50 text-emerald-800 text-xs rounded-xl flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <span>{rfqSuccess}</span>
              </div>
            ) : (
              <form onSubmit={handleSendRfq} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Quantity (Units)</label>
                    <input
                      type="number"
                      required
                      min={1}
                      value={rfqQuantity}
                      onChange={(e) => setRfqQuantity(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">Proposed Unit Price (₹)</label>
                    <input
                      type="number"
                      required
                      step="0.01"
                      value={rfqUnitPrice}
                      onChange={(e) => setRfqUnitPrice(e.target.value)}
                      className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Message to Artisan</label>
                  <textarea
                    required
                    rows={3}
                    value={rfqMessage}
                    onChange={(e) => setRfqMessage(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setRfqModalOpen(false)}
                    className="px-4 py-2 border border-slate-200 text-slate-600 text-xs font-medium rounded-lg"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingRfq}
                    className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-sm"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{submittingRfq ? "Sending..." : "Dispatch RFQ"}</span>
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
