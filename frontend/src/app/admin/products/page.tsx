"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ShieldCheck, CheckCircle2, XCircle, AlertTriangle, Clock, RefreshCw } from "lucide-react";

interface PendingProduct {
  id: string;
  sku: string;
  title: string;
  craft_name?: string;
  category_name?: string;
  price_inr: number;
  stock_quantity: number;
  monthly_production_capacity: number;
  min_order_quantity: number;
  lead_time_days: number;
  storytelling_description: string;
  materials: string[];
  technique?: string;
  provenance_status: string;
  created_at: string;
}

export default function AdminProductModerationPage() {
  const [products, setProducts] = useState<PendingProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [actingId, setActingId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{ [id: string]: string }>({});
  const [alert, setAlert] = useState<{ type: "success" | "error"; msg: string } | null>(null);

  const fetchPending = async () => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      const res = await fetch("/api/v1/products/admin/pending", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      } else if (res.status === 403) {
        setAlert({ type: "error", msg: "Access denied: Administrator privileges required." });
      } else {
        setAlert({ type: "error", msg: "Failed to fetch pending queue." });
      }
    } catch {
      setAlert({ type: "error", msg: "Network error connecting to moderation API." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const handleModeration = async (productId: string, decision: "APPROVE" | "REJECT" | "REQUEST_CORRECTION") => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    setActingId(productId);
    const reason = feedback[productId] || "";

    try {
      const res = await fetch(`/api/v1/products/admin/${productId}/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          decision: decision,
          admin_notes: reason,
          rejection_reason: decision === "REJECT" ? reason : undefined
        })
      });

      if (res.ok) {
        setAlert({
          type: "success",
          msg: `Product ${decision === "APPROVE" ? "Approved & Published" : decision === "REJECT" ? "Rejected" : "Returned for corrections"}.`
        });
        fetchPending();
      } else {
        const err = await res.json();
        setAlert({ type: "error", msg: err.detail || "Moderation action failed." });
      }
    } catch {
      setAlert({ type: "error", msg: "Network error during moderation." });
    } finally {
      setActingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-800">
              <ShieldCheck className="w-4 h-4" /> Administrative Compliance & Moderation
            </div>
            <h1 className="text-2xl font-bold text-stone-900 mt-1">Pending Product Moderation Queue</h1>
            <p className="text-sm text-stone-500">
              Review submitted artisan products for GI compliance, authentic materials, and reasonable capacity claims.
            </p>
          </div>
          <button
            onClick={fetchPending}
            className="p-2 bg-white rounded-lg border border-stone-200 text-stone-600 hover:text-stone-900 shadow-sm"
            title="Refresh Queue"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {alert && (
          <div
            className={`p-4 rounded-lg text-sm flex items-center justify-between ${
              alert.type === "success"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-rose-50 text-rose-800 border border-rose-200"
            }`}
          >
            <span>{alert.msg}</span>
            <button onClick={() => setAlert(null)}>✕</button>
          </div>
        )}

        {loading ? (
          <div className="bg-white rounded-xl p-16 text-center text-stone-500 border border-stone-200 shadow-sm">
            Loading moderation queue...
          </div>
        ) : products.length === 0 ? (
          <div className="bg-white rounded-xl p-16 text-center border border-stone-200 shadow-sm space-y-3">
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
            <h3 className="text-lg font-semibold text-stone-800">No Pending Products</h3>
            <p className="text-stone-500 text-sm">All artisan submissions have been reviewed and adjudicated.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {products.map((p) => (
              <div key={p.id} className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 space-y-4">
                <div className="flex flex-wrap items-start justify-between gap-4 border-b border-stone-100 pb-4">
                  <div>
                    <div className="text-xs font-mono text-stone-400">SKU: {p.sku}</div>
                    <h3 className="text-lg font-bold text-stone-900 mt-0.5">{p.title}</h3>
                    <div className="flex items-center gap-2 text-xs text-stone-500 mt-1">
                      <span>Craft: <strong className="text-stone-700">{p.craft_name}</strong></span>
                      <span>•</span>
                      <span>Category: {p.category_name || "General"}</span>
                      <span>•</span>
                      <span>Provenance Level: <strong className="text-amber-800">{p.provenance_status}</strong></span>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-xs text-stone-400">Declared Price</div>
                    <div className="text-xl font-bold text-stone-900">₹{p.price_inr.toLocaleString("en-IN")}</div>
                    <div className="text-xs text-stone-500">Stock: {p.stock_quantity} | Cap: {p.monthly_production_capacity}/mo</div>
                  </div>
                </div>

                {/* Narrative & Specifications */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 text-xs">
                  <div className="lg:col-span-2 bg-stone-50 p-4 rounded-lg border border-stone-100 space-y-2">
                    <span className="font-semibold text-stone-700 block">Artisan Storytelling & Heritage Statement</span>
                    <p className="text-stone-600 leading-relaxed">{p.storytelling_description}</p>
                  </div>

                  <div className="bg-stone-50 p-4 rounded-lg border border-stone-100 space-y-2">
                    <span className="font-semibold text-stone-700 block">Craft Parameters</span>
                    <div>Materials: <span className="text-stone-800 font-medium">{p.materials ? p.materials.join(", ") : "None declared"}</span></div>
                    {p.technique && <div>Technique: <span className="text-stone-800 font-medium">{p.technique}</span></div>}
                    <div>MOQ: <span className="text-stone-800 font-medium">{p.min_order_quantity}</span></div>
                    <div>Lead Time: <span className="text-stone-800 font-medium">{p.lead_time_days} days</span></div>
                  </div>
                </div>

                {/* Moderation Controls */}
                <div className="pt-2 border-t border-stone-100 space-y-3">
                  <input
                    type="text"
                    placeholder="Admin review notes or rejection explanation (optional for approve, required for corrections)..."
                    value={feedback[p.id] || ""}
                    onChange={(e) => setFeedback({ ...feedback, [p.id]: e.target.value })}
                    className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-xs text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                  />

                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => handleModeration(p.id, "REQUEST_CORRECTION")}
                      disabled={actingId === p.id}
                      className="px-3.5 py-1.5 rounded-lg border border-amber-300 text-amber-800 bg-amber-50 hover:bg-amber-100 text-xs font-semibold transition-colors disabled:opacity-50"
                    >
                      Request Corrections
                    </button>
                    <button
                      onClick={() => handleModeration(p.id, "REJECT")}
                      disabled={actingId === p.id}
                      className="px-3.5 py-1.5 rounded-lg border border-rose-300 text-rose-700 bg-rose-50 hover:bg-rose-100 text-xs font-semibold transition-colors disabled:opacity-50"
                    >
                      Reject Listing
                    </button>
                    <button
                      onClick={() => handleModeration(p.id, "APPROVE")}
                      disabled={actingId === p.id}
                      className="px-4 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold transition-colors disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" /> Approve & Publish
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
