"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Sparkles,
  ArrowLeft,
  Check,
  Edit3,
  X,
  RefreshCw,
  AlertCircle,
  ShieldAlert,
  Clock,
  Layers,
  Image as ImageIcon,
  CheckCircle2,
  XCircle,
  HelpCircle
} from "lucide-react";

interface MediaAsset {
  id: string;
  url: string;
  original_filename: string;
  mime_type: string;
  is_primary: boolean;
}

interface ProductDetails {
  id: string;
  sku: string;
  title: string;
  storytelling_description: string;
  materials: string[];
  technique?: string;
  status: string;
  media: MediaAsset[];
}

interface AISuggestion {
  id: string;
  analysis_id: string;
  product_id: string;
  field_name: string;
  suggested_value: any;
  confidence: number | null;
  source_type: string;
  human_confirmed: boolean;
  confirmed_value: any;
  status: string;
  artisan_notes?: string;
}

interface AIAnalysis {
  id: string;
  product_id: string;
  media_id?: string;
  provider: string;
  model_name: string;
  prompt_version: string;
  status: string;
  error_message?: string;
  processing_duration_ms?: number;
  created_at: string;
  suggestions: AISuggestion[];
}

export default function AIProductStudioPage() {
  const params = useParams();
  const router = useRouter();
  const productId = params?.id as string;

  const [product, setProduct] = useState<ProductDetails | null>(null);
  const [analyses, setAnalyses] = useState<AIAnalysis[]>([]);
  const [selectedMediaId, setSelectedMediaId] = useState<string>("");
  const [activeAnalysis, setActiveAnalysis] = useState<AIAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [applying, setApplying] = useState(false);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>("");
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const fetchProductAndAnalyses = async () => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const headers = { Authorization: `Bearer ${token}` };

      // 1. Fetch Product
      const prodRes = await fetch("/api/v1/artisans/me/products", { headers });
      if (prodRes.ok) {
        const list: ProductDetails[] = await prodRes.json();
        const found = list.find((p) => p.id === productId);
        if (found) {
          setProduct(found);
          const images = (found.media || []).filter((m) => m.mime_type.startsWith("image/"));
          if (images.length > 0 && !selectedMediaId) {
            const primary = images.find((m) => m.is_primary) || images[0];
            setSelectedMediaId(primary.id);
          }
        }
      }

      // 2. Fetch Analyses
      const analysesRes = await fetch(`/api/v1/products/${productId}/ai/analyses`, { headers });
      if (analysesRes.ok) {
        const data: AIAnalysis[] = await analysesRes.json();
        setAnalyses(data);
        if (data.length > 0) {
          setActiveAnalysis(data[0]);
        }
      }
    } catch {
      setStatusMsg({ type: "error", text: "Failed to connect to AI Product Studio." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (productId) fetchProductAndAnalyses();
  }, [productId]);

  const handleStartAnalysis = async () => {
    if (!selectedMediaId) {
      setStatusMsg({ type: "error", text: "Please attach or select a product photograph first." });
      return;
    }

    setAnalyzing(true);
    setStatusMsg(null);
    const token = localStorage.getItem("access_token");

    try {
      const res = await fetch(`/api/v1/products/${productId}/ai/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          media_id: selectedMediaId,
          force_reanalyze: true
        })
      });

      if (res.ok) {
        const data: AIAnalysis = await res.json();
        setActiveAnalysis(data);
        setStatusMsg({
          type: "success",
          text: "AI analysis completed. Review suggestions below before confirming."
        });
        fetchProductAndAnalyses();
      } else {
        const err = await res.json();
        setStatusMsg({ type: "error", text: err.detail || "Analysis failed." });
      }
    } catch {
      setStatusMsg({ type: "error", text: "Network error during analysis." });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleFieldDecision = async (
    fieldName: string,
    action: "ACCEPT" | "EDIT" | "REJECT",
    customVal?: any
  ) => {
    if (!activeAnalysis) return;
    const token = localStorage.getItem("access_token");

    const payload = {
      confirmations: [
        {
          field_name: fieldName,
          action: action,
          custom_value: customVal,
          notes: action === "EDIT" ? "Artisan adjusted value" : undefined
        }
      ],
      apply_to_product: false
    };

    try {
      const res = await fetch(`/api/v1/products/${productId}/ai/analyses/${activeAnalysis.id}/confirm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const updated: AIAnalysis = await res.json();
        setActiveAnalysis(updated);
        setEditingField(null);
      } else {
        const err = await res.json();
        setStatusMsg({ type: "error", text: err.detail || "Decision failed." });
      }
    } catch {
      setStatusMsg({ type: "error", text: "Network error saving decision." });
    }
  };

  const handleApplyConfirmedToProduct = async () => {
    if (!activeAnalysis) return;
    setApplying(true);
    setStatusMsg(null);
    const token = localStorage.getItem("access_token");

    // Collect all confirmed suggestions
    const confirmedItems = activeAnalysis.suggestions
      .filter((s) => s.status === "HUMAN_CONFIRMED")
      .map((s) => ({
        field_name: s.field_name,
        action: "ACCEPT",
        custom_value: s.confirmed_value
      }));

    if (confirmedItems.length === 0) {
      setStatusMsg({
        type: "error",
        text: "No suggestions have been accepted or edited yet. Please review and accept suggestions first."
      });
      setApplying(false);
      return;
    }

    try {
      const res = await fetch(`/api/v1/products/${productId}/ai/analyses/${activeAnalysis.id}/confirm`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          confirmations: confirmedItems,
          apply_to_product: true
        })
      });

      if (res.ok) {
        setStatusMsg({
          type: "success",
          text: "Confirmed attributes applied to canonical product listing! (If published, listing reset to Draft for re-moderation)."
        });
        fetchProductAndAnalyses();
      } else {
        const err = await res.json();
        setStatusMsg({ type: "error", text: err.detail || "Failed to apply attributes." });
      }
    } catch {
      setStatusMsg({ type: "error", text: "Network error applying attributes." });
    } finally {
      setApplying(false);
    }
  };

  if (loading) {
    return <div className="min-h-screen bg-stone-50 p-12 text-center text-stone-500">Loading AI Product Studio...</div>;
  }

  const imageMedia = (product?.media || []).filter((m) => m.mime_type.startsWith("image/"));

  return (
    <div className="min-h-screen bg-stone-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link
              href={`/artisan/products/${productId}/edit`}
              className="p-2 bg-white rounded-lg border border-stone-200 text-stone-600 hover:text-stone-900 shadow-sm"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold text-amber-800 uppercase tracking-wider">
                <Sparkles className="w-4 h-4" /> AI Product Studio • Multimodal Ingestion
              </div>
              <h1 className="text-2xl font-bold text-stone-900 mt-0.5">
                AI Image Understanding & Suggestions
              </h1>
              <p className="text-xs text-stone-500 font-mono mt-0.5">Product SKU: {product?.sku}</p>
            </div>
          </div>
          <Link
            href={`/artisan/products/${productId}/edit`}
            className="px-3.5 py-1.5 border border-stone-300 rounded-lg text-xs font-medium text-stone-700 bg-white hover:bg-stone-50 shadow-sm"
          >
            Back to Editor
          </Link>
        </div>

        {/* AI Honesty Governance Alert */}
        <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-800 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 space-y-1">
            <strong className="font-semibold block">Strict AI Honesty & Provenance Charter:</strong>
            <p>
              AI outputs are <em>assistive suggestions only</em> (tagged <code>AI_SUGGESTED</code>). They do <strong>not</strong> directly overwrite product data and never represent government certifications or verified GI facts. You retain complete authority to accept, edit, or reject each suggestion.
            </p>
          </div>
        </div>

        {statusMsg && (
          <div
            className={`p-4 rounded-lg text-sm flex items-center justify-between ${
              statusMsg.type === "success"
                ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
                : "bg-rose-50 text-rose-800 border border-rose-200"
            }`}
          >
            <span>{statusMsg.text}</span>
            <button onClick={() => setStatusMsg(null)}>✕</button>
          </div>
        )}

        {/* Media Selector & Trigger Card */}
        <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 space-y-4">
          <h2 className="text-sm font-bold text-stone-900 uppercase tracking-wider">
            1. Select Product Photograph for AI Analysis
          </h2>

          {imageMedia.length === 0 ? (
            <div className="text-center p-8 bg-stone-50 rounded-lg border border-dashed border-stone-300 space-y-2">
              <ImageIcon className="w-10 h-10 text-stone-400 mx-auto" />
              <p className="text-xs text-stone-600 font-medium">No image assets attached to this product.</p>
              <Link
                href={`/artisan/products/${productId}/edit`}
                className="inline-block text-xs text-amber-800 font-semibold underline"
              >
                Go to Product Editor to attach photos
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
              {imageMedia.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setSelectedMediaId(m.id)}
                  className={`relative rounded-lg overflow-hidden border-2 p-1 transition-all ${
                    selectedMediaId === m.id
                      ? "border-amber-800 ring-2 ring-amber-800/20 bg-amber-50/50"
                      : "border-stone-200 hover:border-stone-300 bg-stone-50"
                  }`}
                >
                  <img src={m.url} alt={m.original_filename} className="w-full h-24 object-cover rounded" />
                  <span className="block text-[10px] truncate text-stone-600 mt-1 font-medium text-center">
                    {m.original_filename}
                  </span>
                  {selectedMediaId === m.id && (
                    <div className="absolute top-2 right-2 bg-amber-800 text-white rounded-full p-0.5">
                      <Check className="w-3 h-3" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          )}

          <div className="pt-2 flex justify-end">
            <button
              onClick={handleStartAnalysis}
              disabled={analyzing || !selectedMediaId}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-800 hover:bg-amber-900 text-white rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 shadow-sm"
            >
              <Sparkles className="w-4 h-4" />
              {analyzing ? "Analyzing Photograph..." : "Analyze with AI Studio"}
            </button>
          </div>
        </div>

        {/* Suggestions Staging & Human Confirmation Section */}
        {activeAnalysis && (
          <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 space-y-6">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-stone-100 pb-4">
              <div>
                <h2 className="text-base font-bold text-stone-900">
                  2. Review & Confirm Attribute Suggestions
                </h2>
                <div className="flex items-center gap-3 text-xs text-stone-500 mt-1">
                  <span>Model: <strong className="text-stone-700">{activeAnalysis.model_name}</strong></span>
                  <span>•</span>
                  <span>Prompt Version: <strong className="text-stone-700">{activeAnalysis.prompt_version}</strong></span>
                  <span>•</span>
                  <span>Duration: <strong className="text-stone-700">{activeAnalysis.processing_duration_ms || 0}ms</strong></span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleApplyConfirmedToProduct}
                  disabled={applying}
                  className="px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 shadow-sm disabled:opacity-50"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  {applying ? "Applying to Product..." : "Apply Confirmed Attributes to Product"}
                </button>
              </div>
            </div>

            {/* Field Suggestions Grid */}
            <div className="space-y-4">
              {activeAnalysis.suggestions.map((sug) => {
                const isConfirmed = sug.status === "HUMAN_CONFIRMED";
                const isRejected = sug.status === "REJECTED";
                const isEditing = editingField === sug.field_name;

                return (
                  <div
                    key={sug.id}
                    className={`p-4 rounded-xl border transition-colors ${
                      isConfirmed
                        ? "bg-emerald-50/40 border-emerald-200"
                        : isRejected
                        ? "bg-stone-50/80 border-stone-200 opacity-60"
                        : "bg-white border-stone-200 hover:border-amber-200"
                    }`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold uppercase tracking-wider text-stone-800">
                            {sug.field_name.replace(/_/g, " ")}
                          </span>

                          {/* Honest Provenance Badge */}
                          {isConfirmed ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                              <CheckCircle2 className="w-3 h-3" /> Human Confirmed
                            </span>
                          ) : isRejected ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-200 text-stone-700">
                              <XCircle className="w-3 h-3" /> Rejected
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 border border-amber-200">
                              <Sparkles className="w-3 h-3" /> AI Suggested
                            </span>
                          )}

                          {/* Honest Confidence Metric */}
                          <span className="text-[11px] text-stone-400">
                            {sug.confidence !== null && sug.confidence !== undefined
                              ? `Confidence: ${(sug.confidence * 100).toFixed(1)}%`
                              : "Uncalibrated confidence (vision model)"}
                          </span>
                        </div>

                        {/* Value Display */}
                        <div className="mt-2 text-sm text-stone-800">
                          {isEditing ? (
                            <div className="space-y-2 mt-1">
                              <input
                                type="text"
                                value={editValue}
                                onChange={(e) => setEditValue(e.target.value)}
                                className="w-full px-3 py-1.5 border border-stone-300 rounded text-xs text-stone-900 bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                              />
                              <div className="flex gap-2">
                                <button
                                  onClick={() => {
                                    let parsed: any = editValue;
                                    if (Array.isArray(sug.suggested_value)) {
                                      parsed = editValue.split(",").map((v) => v.trim()).filter(Boolean);
                                    }
                                    handleFieldDecision(sug.field_name, "EDIT", parsed);
                                  }}
                                  className="px-3 py-1 bg-amber-800 text-white rounded text-xs font-semibold"
                                >
                                  Save & Confirm
                                </button>
                                <button
                                  onClick={() => setEditingField(null)}
                                  className="px-3 py-1 bg-stone-100 text-stone-600 rounded text-xs"
                                >
                                  Cancel
                                </button>
                              </div>
                            </div>
                          ) : (
                            <div>
                              <div className="font-medium text-stone-900">
                                {isConfirmed && sug.confirmed_value !== null
                                  ? Array.isArray(sug.confirmed_value)
                                    ? sug.confirmed_value.join(", ")
                                    : String(sug.confirmed_value)
                                  : Array.isArray(sug.suggested_value)
                                  ? sug.suggested_value.join(", ")
                                  : String(sug.suggested_value)}
                              </div>
                              {isConfirmed && sug.confirmed_value !== sug.suggested_value && (
                                <div className="text-[11px] text-stone-500 mt-0.5 italic">
                                  Original AI suggestion:{" "}
                                  {Array.isArray(sug.suggested_value)
                                    ? sug.suggested_value.join(", ")
                                    : String(sug.suggested_value)}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Decision Controls */}
                      {!isEditing && (
                        <div className="flex items-center gap-1.5 flex-shrink-0 pt-1">
                          <button
                            onClick={() => handleFieldDecision(sug.field_name, "ACCEPT")}
                            title="Accept AI suggestion"
                            className={`p-1.5 rounded-lg text-xs font-medium transition-colors ${
                              isConfirmed && sug.confirmed_value === sug.suggested_value
                                ? "bg-emerald-600 text-white"
                                : "bg-stone-100 hover:bg-emerald-50 text-stone-700 hover:text-emerald-700"
                            }`}
                          >
                            <Check className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => {
                              setEditingField(sug.field_name);
                              setEditValue(
                                Array.isArray(sug.suggested_value)
                                  ? sug.suggested_value.join(", ")
                                  : String(sug.suggested_value || "")
                              );
                            }}
                            title="Edit value before confirming"
                            className="p-1.5 rounded-lg text-xs font-medium bg-stone-100 hover:bg-amber-50 text-stone-700 hover:text-amber-800 transition-colors"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleFieldDecision(sug.field_name, "REJECT")}
                            title="Reject suggestion"
                            className={`p-1.5 rounded-lg text-xs font-medium transition-colors ${
                              isRejected
                                ? "bg-rose-600 text-white"
                                : "bg-stone-100 hover:bg-rose-50 text-stone-700 hover:text-rose-700"
                            }`}
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
