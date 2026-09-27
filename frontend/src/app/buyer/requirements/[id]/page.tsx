"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Sparkles,
  Search,
  CheckCircle2,
  AlertCircle,
  Package,
  Layers,
  ShieldCheck,
  Calendar,
  Check,
  Clock,
  Send,
  RefreshCw
} from "lucide-react";

export default function BuyerRequirementDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [req, setReq] = useState<any>(null);
  const [understanding, setUnderstanding] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadRequirement();
    }
  }, [id]);

  const loadRequirement = async () => {
    setLoading(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch(`/api/v1/buyer-requirements/${id}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (!res.ok) throw new Error("Failed to load requirement");
      const data = await res.json();
      setReq(data);

      // Check for staged understanding
      const undRes = await fetch(`/api/v1/buyer-requirements/${id}/understand`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (undRes.ok) {
        const undData = await undRes.json();
        setUnderstanding(undData);
      }
    } catch (err: any) {
      setError(err.message || "Error loading requirement");
    } finally {
      setLoading(false);
    }
  };

  const handleExtractAI = async () => {
    setExtracting(true);
    setError(null);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch(`/api/v1/buyer-requirements/${id}/understand`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (!res.ok) throw new Error("Failed to extract AI understanding");
      const data = await res.json();
      setUnderstanding(data);
      setSuccessMsg("AI extracted structured craft parameters into staging layer.");
    } catch (err: any) {
      setError(err.message || "Failed to trigger AI understanding");
    } finally {
      setExtracting(false);
    }
  };

  const handleConfirmUnderstanding = async () => {
    setConfirming(true);
    setError(null);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch(`/api/v1/buyer-requirements/${id}/understand/confirm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({ overrides: {} })
      });
      if (!res.ok) throw new Error("Failed to confirm understanding");
      const updatedReq = await res.json();
      setReq(updatedReq);
      setSuccessMsg("Confirmed parameters adopted into canonical requirement.");
      await loadRequirement();
    } catch (err: any) {
      setError(err.message || "Failed to confirm understanding");
    } finally {
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
      </div>
    );
  }

  if (!req) {
    return (
      <div className="min-h-screen bg-slate-50 p-8 text-center">
        <p className="text-slate-600">Requirement not found.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/buyer/rfqs"
              className="p-2 hover:bg-slate-100 rounded-lg text-slate-500 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-slate-900">{req.title}</h1>
              <p className="text-xs text-slate-500">
                Created: {new Date(req.created_at).toLocaleDateString()} | Status: {req.status}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href={`/buyer/requirements/${id}/matches`}
              className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl transition-colors flex items-center gap-2 shadow-sm"
            >
              <Search className="w-4 h-4" />
              <span>View Match Candidates</span>
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {successMsg && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center gap-3 text-emerald-800 text-sm">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{successMsg}</span>
          </div>
        )}
        {error && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-700 text-sm">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* AI Understanding Staging Card */}
        <div className="bg-white border border-indigo-100 rounded-xl p-6 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-50 rounded-full blur-2xl -mr-10 -mt-10" />
          <div className="flex items-center justify-between mb-4 relative z-10">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              <h2 className="font-semibold text-slate-800 text-base">AI Requirement Understanding</h2>
              <span className="text-xs bg-indigo-50 text-indigo-700 font-medium px-2 py-0.5 rounded-md border border-indigo-200">
                Staged Suggestions
              </span>
            </div>

            <button
              onClick={handleExtractAI}
              disabled={extracting}
              className="text-xs font-semibold px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-lg transition-colors flex items-center gap-1.5"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${extracting ? "animate-spin" : ""}`} />
              <span>{extracting ? "Extracting..." : "Re-Run Extraction"}</span>
            </button>
          </div>

          {understanding ? (
            <div className="space-y-4 relative z-10">
              <div className="p-3 bg-slate-50 rounded-lg text-xs text-slate-600">
                <span className="font-semibold text-slate-700">Model:</span> {understanding.model_name} |{" "}
                <span className="font-semibold text-slate-700">Status:</span>{" "}
                <span className={understanding.is_confirmed_by_buyer ? "text-emerald-600 font-semibold" : "text-amber-600 font-semibold"}>
                  {understanding.status}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3 border border-slate-200 rounded-lg bg-white">
                  <p className="text-xs text-slate-500">Extracted Qty</p>
                  <p className="font-bold text-slate-800 text-sm">
                    {understanding.extracted_fields?.required_quantity || "Not found"}
                  </p>
                </div>
                <div className="p-3 border border-slate-200 rounded-lg bg-white">
                  <p className="text-xs text-slate-500">Target Unit Price</p>
                  <p className="font-bold text-slate-800 text-sm">
                    {understanding.extracted_fields?.target_unit_price_inr ? `₹${understanding.extracted_fields.target_unit_price_inr}` : "Not found"}
                  </p>
                </div>
                <div className="p-3 border border-slate-200 rounded-lg bg-white">
                  <p className="text-xs text-slate-500">GI Certified</p>
                  <p className="font-bold text-slate-800 text-sm">
                    {understanding.extracted_fields?.requires_gi_certification ? "Required" : "Not mandated"}
                  </p>
                </div>
                <div className="p-3 border border-slate-200 rounded-lg bg-white">
                  <p className="text-xs text-slate-500">Craft Name</p>
                  <p className="font-bold text-slate-800 text-sm">
                    {understanding.extracted_fields?.craft_name || "General"}
                  </p>
                </div>
              </div>

              {!understanding.is_confirmed_by_buyer && (
                <div className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs">
                  <span className="text-amber-800">
                    Staged AI suggestions are quarantined. Click below to adopt into canonical requirement.
                  </span>
                  <button
                    onClick={handleConfirmUnderstanding}
                    disabled={confirming}
                    className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded-lg flex items-center gap-1.5 shadow-sm"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{confirming ? "Adopting..." : "Confirm & Adopt Fields"}</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <p className="text-xs text-slate-500">
              No AI extraction generated yet. Click "Re-Run Extraction" to parse this brief into structured fields.
            </p>
          )}
        </div>

        {/* Canonical Specifications */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
          <h2 className="font-semibold text-slate-800 text-base">Canonical Requirement Specifications</h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2">
            <div>
              <p className="text-xs text-slate-400">Required Quantity</p>
              <p className="font-bold text-slate-800 text-base">{req.required_quantity} units</p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Target Unit Price</p>
              <p className="font-bold text-slate-800 text-base">
                {req.target_unit_price_inr ? `₹${req.target_unit_price_inr}` : "Open"}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">GI Certification</p>
              <p className="font-bold text-slate-800 text-base">
                {req.requires_gi_certification ? "Mandatory" : "Optional"}
              </p>
            </div>
            <div>
              <p className="text-xs text-slate-400">Delivery Deadline</p>
              <p className="font-bold text-slate-800 text-base">
                {new Date(req.deadline_date).toLocaleDateString()}
              </p>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100">
            <p className="text-xs text-slate-400 mb-1">Procurement Brief Text</p>
            <p className="text-sm text-slate-700 bg-slate-50 p-4 rounded-xl leading-relaxed">
              {req.raw_text}
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
