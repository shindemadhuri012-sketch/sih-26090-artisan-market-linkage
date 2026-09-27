"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Sparkles,
  Send,
  Calendar,
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Package,
  MapPin,
  Clock,
  IndianRupee
} from "lucide-react";

export default function NewBuyerRequirementPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState("");
  const [requiredQuantity, setRequiredQuantity] = useState<number>(100);
  const [targetUnitPrice, setTargetUnitPrice] = useState<string>("1500");
  const [maxBudget, setMaxBudget] = useState<string>("150000");
  const [deadlineDate, setDeadlineDate] = useState<string>(
    new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0]
  );
  const [requiresGI, setRequiresGI] = useState(false);
  const [requiresCustomization, setRequiresCustomization] = useState(false);
  const [desiredMaterials, setDesiredMaterials] = useState<string>("Silk, Zari");
  const [desiredTechniques, setDesiredTechniques] = useState<string>("Handloom");
  const [preferredRegion, setPreferredRegion] = useState<string>("Madhya Pradesh");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const materialsArray = desiredMaterials.split(",").map((s) => s.trim()).filter(Boolean);
    const techniquesArray = desiredTechniques.split(",").map((s) => s.trim()).filter(Boolean);

    try {
      const res = await fetch("/api/v1/buyer-requirements", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify({
          title,
          raw_text: rawText,
          required_quantity: Number(requiredQuantity),
          target_unit_price_inr: targetUnitPrice ? Number(targetUnitPrice) : null,
          max_budget_inr: maxBudget ? Number(maxBudget) : null,
          deadline_date: new Date(deadlineDate).toISOString(),
          requires_gi_certification: requiresGI,
          requires_customization: requiresCustomization,
          desired_materials: materialsArray,
          desired_techniques: techniquesArray,
          preferred_region: preferredRegion || null
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to create requirement");
      }

      const created = await res.json();
      router.push(`/buyer/requirements/${created.id}`);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred");
    } finally {
      setLoading(false);
    }
  };

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
              <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <span>Post Procurement Brief / RFQ</span>
                <span className="text-xs bg-indigo-100 text-indigo-800 font-semibold px-2 py-0.5 rounded-full">
                  Phase 6 Match Linkage
                </span>
              </h1>
              <p className="text-xs text-slate-500">
                Define your craft specifications for AI understanding and explainable artisan matching
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-3 text-rose-700 text-sm">
              <AlertCircle className="w-5 h-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Section 1: Natural Language Brief */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              <h2 className="font-semibold text-slate-800 text-base">1. Procurement Brief & Description</h2>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Describe your procurement need in plain English or local language. You can also review AI-extracted parameters after posting.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Requirement Title <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 500 Handloom Chanderi Silk Stoles for Annual Summit Gifting"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Detailed Brief / RFQ Text <span className="text-rose-500">*</span>
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="Describe desired materials, craft traditions, dimensions, custom packaging, and delivery requirements..."
                  value={rawText}
                  onChange={(e) => setRawText(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Section 2: Commercial Constraints */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Package className="w-5 h-5 text-emerald-600" />
              <h2 className="font-semibold text-slate-800 text-base">2. Commercial & Volume Parameters</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Required Order Volume (Units) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  required
                  min={1}
                  value={requiredQuantity}
                  onChange={(e) => setRequiredQuantity(Number(e.target.value))}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Unit Price (₹ / unit)
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-slate-400 text-sm font-semibold">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="1500.00"
                    value={targetUnitPrice}
                    onChange={(e) => setTargetUnitPrice(e.target.value)}
                    className="w-full pl-8 pr-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Maximum Total Budget (₹)
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-slate-400 text-sm font-semibold">₹</span>
                  <input
                    type="number"
                    step="0.01"
                    placeholder="150000.00"
                    value={maxBudget}
                    onChange={(e) => setMaxBudget(e.target.value)}
                    className="w-full pl-8 pr-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Section 3: Craft & Quality Preferences */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-3">
              <Layers className="w-5 h-5 text-amber-600" />
              <h2 className="font-semibold text-slate-800 text-base">3. Craft & Quality Specifications</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Desired Raw Materials (comma-separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Silk, Zari, Cotton"
                  value={desiredMaterials}
                  onChange={(e) => setDesiredMaterials(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Desired Craft Technique
                </label>
                <input
                  type="text"
                  placeholder="e.g. Handloom Weaving, Extra-Weft"
                  value={desiredTechniques}
                  onChange={(e) => setDesiredTechniques(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Preferred Craft Origin Region
                </label>
                <input
                  type="text"
                  placeholder="e.g. Madhya Pradesh, Maharashtra, Gujarat"
                  value={preferredRegion}
                  onChange={(e) => setPreferredRegion(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Required Delivery Deadline <span className="text-rose-500">*</span>
                </label>
                <input
                  type="date"
                  required
                  value={deadlineDate}
                  onChange={(e) => setDeadlineDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 pt-2 border-t border-slate-100">
              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={requiresGI}
                  onChange={(e) => setRequiresGI(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                />
                <span>Mandate Official Geographical Indication (GI) Certification</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer text-xs font-medium text-slate-700">
                <input
                  type="checkbox"
                  checked={requiresCustomization}
                  onChange={(e) => setRequiresCustomization(e.target.checked)}
                  className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 h-4 w-4"
                />
                <span>Requires Custom Motif or Corporate Branding</span>
              </label>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <Link
              href="/buyer/rfqs"
              className="px-5 py-2.5 bg-white border border-slate-200 text-slate-700 text-sm font-medium rounded-xl hover:bg-slate-50 transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl transition-colors flex items-center gap-2 shadow-sm disabled:opacity-50"
            >
              {loading ? (
                <>Saving & Generating Vector Embedding...</>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Submit Requirement & Find Matches</span>
                </>
              )}
            </button>
          </div>
        </form>
      </main>
    </div>
  );
}
