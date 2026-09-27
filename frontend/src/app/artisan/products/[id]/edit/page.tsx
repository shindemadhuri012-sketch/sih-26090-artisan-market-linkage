"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Trash2, ImagePlus, CheckCircle, Clock, AlertCircle, Sparkles } from "lucide-react";

interface MediaAsset {
  id: string;
  url: string;
  thumbnail_url?: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  is_primary: boolean;
}

interface ProductDetails {
  id: string;
  sku: string;
  title: string;
  storytelling_description: string;
  price_inr: number;
  stock_quantity: number;
  monthly_production_capacity: number;
  min_order_quantity: number;
  lead_time_days: number;
  availability_status: string;
  region?: string;
  materials: string[];
  primary_color?: string;
  dimensions?: string;
  weight_grams?: number;
  technique?: string;
  style?: string;
  is_customizable: boolean;
  status: string;
  provenance_status: string;
  admin_feedback?: string;
  media: MediaAsset[];
}

export default function EditProductPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params?.id as string;

  const [product, setProduct] = useState<ProductDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Form Fields
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

  // Media Form State
  const [newMediaUrl, setNewMediaUrl] = useState("");
  const [newMediaFilename, setNewMediaFilename] = useState("");
  const [newMediaMime, setNewMediaMime] = useState("image/jpeg");
  const [newMediaIsPrimary, setNewMediaIsPrimary] = useState(false);

  const fetchProduct = async () => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const res = await fetch(`/api/v1/artisans/me/products`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const list: ProductDetails[] = await res.json();
        const found = list.find((p) => p.id === productId);
        if (found) {
          setProduct(found);
          setTitle(found.title);
          setStorytelling(found.storytelling_description);
          setPriceInr(found.price_inr.toString());
          setStockQuantity(found.stock_quantity.toString());
          setMonthlyCapacity(found.monthly_production_capacity.toString());
          setMinOrderQty(found.min_order_quantity.toString());
          setLeadTimeDays(found.lead_time_days.toString());
          setMaterials(found.materials ? found.materials.join(", ") : "");
          setTechnique(found.technique || "");
          setDimensions(found.dimensions || "");
          setWeightGrams(found.weight_grams ? found.weight_grams.toString() : "");
          setIsCustomizable(found.is_customizable);
        } else {
          setErr("Product not found or access denied.");
        }
      } else {
        setErr("Failed to retrieve product details.");
      }
    } catch {
      setErr("Network error.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) fetchProduct();
  }, [productId]);

  const handleSaveDetails = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMsg(null);
    setErr(null);

    const token = localStorage.getItem("access_token");
    if (!token) return;

    const payload = {
      title: title.trim(),
      storytelling_description: storytelling.trim(),
      price_inr: parseFloat(priceInr),
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
      const res = await fetch(`/api/v1/products/${productId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        setMsg("Product listing updated successfully. (Note: Published items revert to Draft for re-moderation).");
        fetchProduct();
      } else {
        const error = await res.json();
        setErr(error.detail || "Update failed.");
      }
    } catch {
      setErr("Error updating product.");
    } finally {
      setSaving(false);
    }
  };

  const handleAddMedia = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const res = await fetch(`/api/v1/products/${productId}/media`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          media_type: "IMAGE",
          url: newMediaUrl.trim(),
          original_filename: newMediaFilename.trim(),
          file_size_bytes: 512000,
          mime_type: newMediaMime,
          is_primary: newMediaIsPrimary
        })
      });

      if (res.ok) {
        setNewMediaUrl("");
        setNewMediaFilename("");
        setMsg("Media asset attached.");
        fetchProduct();
      } else {
        const error = await res.json();
        setErr(error.detail || "Failed to attach media.");
      }
    } catch {
      setErr("Network error while adding media.");
    }
  };

  const handleDeleteMedia = async (mediaId: string) => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const res = await fetch(`/api/v1/products/${productId}/media/${mediaId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setMsg("Media asset removed.");
        fetchProduct();
      } else {
        setErr("Could not remove media asset.");
      }
    } catch {
      setErr("Network error.");
    }
  };

  const handleSubmitForReview = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const res = await fetch(`/api/v1/products/${productId}/submit`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setMsg("Product submitted for review!");
        fetchProduct();
      } else {
        const error = await res.json();
        setErr(error.detail || "Submission failed.");
      }
    } catch {
      setErr("Network error during submission.");
    }
  };

  if (loading) {
    return <div className="min-h-screen bg-stone-50 p-12 text-center text-stone-500">Loading product...</div>;
  }

  return (
    <div className="min-h-screen bg-stone-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href="/artisan/products"
              className="p-2 bg-white rounded-lg border border-stone-200 text-stone-600 hover:text-stone-900 shadow-sm"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-stone-900">Manage Product: {product?.sku}</h1>
              <p className="text-sm text-stone-500">Status: <span className="font-semibold text-amber-900">{product?.status}</span> | Provenance: {product?.provenance_status}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href={`/artisan/products/${productId}/ai-studio`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-800" /> AI Product Studio
            </Link>
            {(product?.status === "DRAFT" || product?.status === "REJECTED") && (
              <button
                onClick={handleSubmitForReview}
                className="px-4 py-2 bg-amber-800 text-white rounded-lg hover:bg-amber-900 text-xs font-semibold transition-colors"
              >
                Submit for Admin Review
              </button>
            )}
          </div>
        </div>

        {/* AI Studio Callout Banner */}
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 text-amber-800 rounded-lg">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-stone-900 uppercase tracking-wide">
                Need Help Cataloguing Your Craft?
              </h3>
              <p className="text-xs text-stone-600">
                Let our AI Product Studio analyze your craft photographs to extract weave techniques, materials, and cultural storytelling suggestions.
              </p>
            </div>
          </div>
          <Link
            href={`/artisan/products/${productId}/ai-studio`}
            className="px-3.5 py-1.5 bg-amber-800 hover:bg-amber-900 text-white rounded-lg text-xs font-semibold transition-colors shadow-sm whitespace-nowrap"
          >
            Launch AI Studio &rarr;
          </Link>
        </div>

        {msg && (
          <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
            <span>{msg}</span>
            <button onClick={() => setMsg(null)}>✕</button>
          </div>
        )}
        {err && (
          <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center justify-between">
            <span>{err}</span>
            <button onClick={() => setErr(null)}>✕</button>
          </div>
        )}

        {/* Product Details Form */}
        <form onSubmit={handleSaveDetails} className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 space-y-6">
          <h2 className="text-base font-bold text-stone-900 border-b border-stone-100 pb-3">Product Specifications</h2>

          <div>
            <label className="block text-sm font-semibold text-stone-800 mb-1">Listing Title</label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-stone-800 mb-1">Storytelling & Provenance Description</label>
            <textarea
              rows={3}
              required
              value={storytelling}
              onChange={(e) => setStorytelling(e.target.value)}
              className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Price (₹ INR)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                required
                value={priceInr}
                onChange={(e) => setPriceInr(e.target.value)}
                className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Stock Quantity</label>
              <input
                type="number"
                min="0"
                required
                value={stockQuantity}
                onChange={(e) => setStockQuantity(e.target.value)}
                className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Monthly Capacity</label>
              <input
                type="number"
                min="0"
                required
                value={monthlyCapacity}
                onChange={(e) => setMonthlyCapacity(e.target.value)}
                className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">MOQ</label>
              <input
                type="number"
                min="1"
                required
                value={minOrderQty}
                onChange={(e) => setMinOrderQty(e.target.value)}
                className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Lead Time (Days)</label>
              <input
                type="number"
                min="0"
                required
                value={leadTimeDays}
                onChange={(e) => setLeadTimeDays(e.target.value)}
                className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Materials (comma separated)</label>
              <input
                type="text"
                value={materials}
                onChange={(e) => setMaterials(e.target.value)}
                className="w-full px-3.5 py-2 bg-stone-50 border border-stone-300 rounded-lg text-sm"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 bg-amber-800 text-white rounded-lg text-sm font-medium hover:bg-amber-900 disabled:opacity-50"
            >
              {saving ? "Saving Changes..." : "Save Product Details"}
            </button>
          </div>
        </form>

        {/* Media Assets Section */}
        <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 space-y-6">
          <h2 className="text-base font-bold text-stone-900 border-b border-stone-100 pb-3">Attached Media Assets</h2>

          {product?.media && product.media.length > 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {product.media.map((m) => (
                <div key={m.id} className="relative group border border-stone-200 rounded-lg overflow-hidden bg-stone-50 p-2 text-center">
                  <div className="h-28 flex items-center justify-center bg-stone-100 rounded text-xs text-stone-500 overflow-hidden">
                    <img src={m.url} alt={m.original_filename} className="h-full w-full object-cover" />
                  </div>
                  <div className="mt-2 text-xs truncate font-medium text-stone-800">{m.original_filename}</div>
                  <div className="text-[10px] text-stone-400 uppercase">{m.mime_type}</div>
                  {m.is_primary && (
                    <span className="inline-block mt-1 text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-semibold">
                      Primary
                    </span>
                  )}
                  <button
                    onClick={() => handleDeleteMedia(m.id)}
                    className="mt-2 w-full flex items-center justify-center gap-1 text-xs text-rose-600 hover:text-rose-800 py-1 bg-rose-50 hover:bg-rose-100 rounded transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Delete
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-stone-500 italic">No media assets attached yet.</p>
          )}

          {/* Add Media Form */}
          <form onSubmit={handleAddMedia} className="pt-4 border-t border-stone-100 space-y-3">
            <h3 className="text-sm font-semibold text-stone-800 flex items-center gap-2">
              <ImagePlus className="w-4 h-4 text-amber-800" /> Attach Media Asset Metadata
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <input
                  type="url"
                  required
                  placeholder="HTTPS URL (e.g. https://...)"
                  value={newMediaUrl}
                  onChange={(e) => setNewMediaUrl(e.target.value)}
                  className="w-full px-3 py-1.5 bg-stone-50 border border-stone-300 rounded text-xs text-stone-900"
                />
              </div>
              <div>
                <input
                  type="text"
                  required
                  placeholder="Original Filename (e.g. saree_pallu.jpg)"
                  value={newMediaFilename}
                  onChange={(e) => setNewMediaFilename(e.target.value)}
                  className="w-full px-3 py-1.5 bg-stone-50 border border-stone-300 rounded text-xs text-stone-900"
                />
              </div>
              <div className="flex gap-2">
                <select
                  value={newMediaMime}
                  onChange={(e) => setNewMediaMime(e.target.value)}
                  className="w-full px-2 py-1.5 bg-stone-50 border border-stone-300 rounded text-xs text-stone-900"
                >
                  <option value="image/jpeg">image/jpeg</option>
                  <option value="image/png">image/png</option>
                  <option value="image/webp">image/webp</option>
                </select>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-stone-800 text-white text-xs font-semibold rounded hover:bg-stone-900 whitespace-nowrap"
                >
                  Attach
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
