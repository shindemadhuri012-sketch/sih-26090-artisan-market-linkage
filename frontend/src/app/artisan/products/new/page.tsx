"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Sparkles, Check, AlertCircle } from "lucide-react";

interface CraftOption {
  id: string;
  name: string;
  origin_state: string;
  has_gi_tag: boolean;
}

export default function NewProductPage() {
  const router = useRouter();
  const [crafts, setCrafts] = useState<CraftOption[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [craftId, setCraftId] = useState("");
  const [title, setTitle] = useState("");
  const [storytelling, setStorytelling] = useState("");
  const [priceInr, setPriceInr] = useState("");
  const [stockQuantity, setStockQuantity] = useState("1");
  const [monthlyCapacity, setMonthlyCapacity] = useState("10");
  const [minOrderQty, setMinOrderQty] = useState("1");
  const [leadTimeDays, setLeadTimeDays] = useState("7");
  const [materials, setMaterials] = useState("");
  const [technique, setTechnique] = useState("");
  const [dimensions, setDimensions] = useState("");
  const [weightGrams, setWeightGrams] = useState("");
  const [isCustomizable, setIsCustomizable] = useState(false);

  useEffect(() => {
    // Fetch available master crafts
    fetch("/api/v1/crafts?page_size=100")
      .then((res) => res.json())
      .then((data) => {
        if (data.items) {
          setCrafts(data.items);
          if (data.items.length > 0) {
            setCraftId(data.items[0].id);
          }
        }
      })
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    const payload = {
      craft_id: craftId,
      title: title.trim(),
      storytelling_description: storytelling.trim(),
      price_inr: parseFloat(priceInr),
      currency: "INR",
      stock_quantity: parseInt(stockQuantity, 10),
      monthly_production_capacity: parseInt(monthlyCapacity, 10),
      min_order_quantity: parseInt(minOrderQty, 10),
      lead_time_days: parseInt(leadTimeDays, 10),
      materials: materials ? materials.split(",").map((m) => m.trim()).filter(Boolean) : [],
      technique: technique.trim() || undefined,
      dimensions: dimensions.trim() || undefined,
      weight_grams: weightGrams ? parseInt(weightGrams, 10) : undefined,
      is_customizable: isCustomizable
    };

    try {
      const res = await fetch("/api/v1/products", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const prod = await res.json();
        router.push(`/artisan/products/${prod.id}/edit`);
      } else {
        const err = await res.json();
        setErrorMsg(err.detail || "Failed to create product listing.");
      }
    } catch {
      setErrorMsg("Network error during product creation.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <div className="flex items-center gap-3">
          <Link
            href="/artisan/products"
            className="p-2 bg-white rounded-lg border border-stone-200 text-stone-600 hover:text-stone-900 shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-stone-900">Add New Craft Product</h1>
            <p className="text-sm text-stone-500">Provide authentic craft details, inventory, and production parameters.</p>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 space-y-6">
          {/* Craft Selection */}
          <div>
            <label className="block text-sm font-semibold text-stone-800 mb-1">
              Select Craft Tradition <span className="text-rose-500">*</span>
            </label>
            <select
              value={craftId}
              onChange={(e) => setCraftId(e.target.value)}
              required
              className="w-full px-3.5 py-2.5 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
            >
              {crafts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.origin_state}) {c.has_gi_tag ? "— [GI Protected]" : ""}
                </option>
              ))}
            </select>
          </div>

          {/* Product Title */}
          <div>
            <label className="block text-sm font-semibold text-stone-800 mb-1">
              Product Title <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Pure Handloom Chanderi Cotton Silk Saree with Zari Border"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
            />
          </div>

          {/* Storytelling Description */}
          <div>
            <div className="flex justify-between items-center mb-1">
              <label className="block text-sm font-semibold text-stone-800">
                Craft Storytelling & Provenance Narrative <span className="text-rose-500">*</span>
              </label>
              <span className="text-xs text-stone-400">Min. 10 characters</span>
            </div>
            <textarea
              required
              rows={4}
              placeholder="Describe the cultural origin, loom/technique used, time taken to craft, and authentic motifs..."
              value={storytelling}
              onChange={(e) => setStorytelling(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
            />
          </div>

          {/* Pricing & Commercials */}
          <div className="pt-4 border-t border-stone-200">
            <h3 className="text-sm font-bold text-stone-900 uppercase tracking-wider mb-4">
              Pricing, Inventory & Capacity Decoupling
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Price in INR (₹) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  required
                  placeholder="3500.00"
                  value={priceInr}
                  onChange={(e) => setPriceInr(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Immediate Ready Stock (Pieces) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  required
                  value={stockQuantity}
                  onChange={(e) => setStockQuantity(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Monthly Sustainable Production Capacity <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  required
                  value={monthlyCapacity}
                  onChange={(e) => setMonthlyCapacity(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
                <span className="text-[11px] text-stone-400">Used for institutional buyer matching</span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Minimum Order Quantity (MOQ) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  value={minOrderQty}
                  onChange={(e) => setMinOrderQty(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Production Lead Time (Days) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  min="0"
                  required
                  value={leadTimeDays}
                  onChange={(e) => setLeadTimeDays(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
              </div>

              <div className="flex items-center pt-5">
                <label className="flex items-center gap-2 cursor-pointer text-sm font-medium text-stone-800">
                  <input
                    type="checkbox"
                    checked={isCustomizable}
                    onChange={(e) => setIsCustomizable(e.target.checked)}
                    className="w-4 h-4 text-amber-800 rounded border-stone-300 focus:ring-amber-800"
                  />
                  <span>Accepts Custom Orders / Bespoke Motifs</span>
                </label>
              </div>
            </div>
          </div>

          {/* Craft Specifications */}
          <div className="pt-4 border-t border-stone-200">
            <h3 className="text-sm font-bold text-stone-900 uppercase tracking-wider mb-4">
              Material & Craftsmanship Attributes
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Authentic Raw Materials (comma separated)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Mulberry Silk, Cotton Thread, Zari"
                  value={materials}
                  onChange={(e) => setMaterials(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Traditional Technique
                </label>
                <input
                  type="text"
                  placeholder="e.g. Pit Loom Extra-Weft Brocade"
                  value={technique}
                  onChange={(e) => setTechnique(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Dimensions (Length x Width)
                </label>
                <input
                  type="text"
                  placeholder="e.g. 5.5m x 1.15m"
                  value={dimensions}
                  onChange={(e) => setDimensions(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-700 mb-1">
                  Net Weight (Grams)
                </label>
                <input
                  type="number"
                  min="0"
                  placeholder="e.g. 450"
                  value={weightGrams}
                  onChange={(e) => setWeightGrams(e.target.value)}
                  className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* AI Suggestion Placeholder Box */}
          <div className="bg-amber-50/60 border border-amber-200/80 rounded-lg p-4 flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-amber-900 space-y-1">
              <strong className="font-semibold">Future AI Product Studio Integration:</strong>
              <p>
                In Phase 4, our multimodal vision model will automatically recommend SEO titles, authentic material descriptions, and pricing confidence intervals. The data contract is initialized in this phase without running ungrounded inference.
              </p>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex justify-end gap-3 pt-4 border-t border-stone-200">
            <Link
              href="/artisan/products"
              className="px-5 py-2.5 rounded-lg border border-stone-300 text-stone-700 hover:bg-stone-50 text-sm font-medium transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-amber-800 text-white rounded-lg hover:bg-amber-900 text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "Creating Listing..." : "Save Draft & Continue to Media"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
