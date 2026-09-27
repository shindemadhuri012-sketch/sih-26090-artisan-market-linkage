"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Calculator,
  Scale,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Info,
  Layers,
  Plus,
  Trash2,
  FileCheck,
  DollarSign,
  HelpCircle,
  ExternalLink,
  Save,
  Check,
  RefreshCw,
  Sparkles
} from "lucide-react";

interface MaterialItem {
  material_name: string;
  quantity: number | string;
  unit: string;
  unit_cost_inr: number | string;
  source_type: string;
  source_reference?: string;
}

interface ProductDetails {
  id: string;
  sku: string;
  title: string;
  craft_id: string;
  price_inr: number;
  materials: string[];
  status: string;
}

interface PriceAnalysis {
  id: string;
  product_id: string;
  engine_version: string;
  currency: string;
  evidence_status: string;
  cost_baseline: {
    total_material_cost: number | string;
    total_labor_cost: number | string;
    packaging_cost?: number | string;
    transport_cost?: number | string;
    overhead_cost: number | string;
    total_production_cost: number | string;
    unit_production_cost: number | string;
    desired_margin_percentage: number | string;
    cost_baseline_price: number | string;
    currency: string;
  };
  market_evidence: {
    status: string;
    observation_count: number;
    median_inr: number | null;
    min_inr: number | null;
    max_inr: number | null;
    iqr_low_inr: number | null;
    iqr_high_inr: number | null;
    quality_rating: string;
    sources_used?: string[];
    benchmark_reference?: string;
  };
  fair_price_analysis: {
    status: string;
    floor_price: number;
    recommended_price: number;
    price_range_min: number;
    price_range_max: number;
  };
  explanation_steps: Array<{
    step_number: number;
    title: string;
    detail: string;
    mathematical_formula?: string;
    inputs_used?: Record<string, any>;
  }>;
  limitations_notes: string[];
  provenance_state: string;
  is_confirmed_by_artisan: boolean;
  confirmed_price_inr: number | null;
  artisan_notes?: string;
  created_at: string;
}

export default function FairPriceIntelligencePage() {
  const params = useParams();
  const router = useRouter();
  const productId = params?.id as string;

  const [product, setProduct] = useState<ProductDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [savingCosts, setSavingCosts] = useState(false);
  const [confirmingPrice, setConfirmingPrice] = useState(false);
  const [statusMsg, setStatusMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Form State
  const [materials, setMaterials] = useState<MaterialItem[]>([
    { material_name: "Raw Material", quantity: 1, unit: "units", unit_cost_inr: 500, source_type: "ARTISAN_ENTERED" }
  ]);
  const [laborMethod, setLaborMethod] = useState<"HOURLY_RATE" | "TOTAL_STATED">("HOURLY_RATE");
  const [laborHours, setLaborHours] = useState<number | string>(8);
  const [laborRate, setLaborRate] = useState<number | string>(150);
  const [totalLaborStated, setTotalLaborStated] = useState<number | string>(1200);
  const [packagingCost, setPackagingCost] = useState<number | string>(80);
  const [transportCost, setTransportCost] = useState<number | string>(120);
  const [overheadCost, setOverheadCost] = useState<number | string>(150);
  const [overheadBasis, setOverheadBasis] = useState<string>("PER_PRODUCT");
  const [otherCosts, setOtherCosts] = useState<number | string>(0);
  const [batchQuantity, setBatchQuantity] = useState<number>(1);
  const [desiredMargin, setDesiredMargin] = useState<number | string>(25);
  const [currentSellingPrice, setCurrentSellingPrice] = useState<number | string>(0);

  // Results State
  const [latestAnalysis, setLatestAnalysis] = useState<PriceAnalysis | null>(null);
  const [confirmedNotes, setConfirmedNotes] = useState<string>("");

  useEffect(() => {
    fetchProductAndPricing();
  }, [productId]);

  const fetchProductAndPricing = async () => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.push("/login");
      return;
    }

    try {
      const headers = { Authorization: `Bearer ${token}` };

      // 1. Fetch Product details
      const prodRes = await fetch(`/api/v1/products/${productId}`, { headers });
      if (prodRes.ok) {
        const prodData = await prodRes.json();
        setProduct(prodData);
        setCurrentSellingPrice(prodData.price_inr);
      }

      // 2. Fetch existing cost breakdown if available
      const costRes = await fetch(`/api/v1/products/${productId}/pricing/costs`, { headers });
      if (costRes.ok) {
        const costData = await costRes.json();
        if (costData.materials && costData.materials.length > 0) {
          setMaterials(costData.materials);
        }
        setLaborMethod(costData.labor_calculation_method);
        if (costData.labor_hours !== null) setLaborHours(costData.labor_hours);
        if (costData.hourly_labor_rate !== null) setLaborRate(costData.hourly_labor_rate);
        if (costData.total_labor_cost !== null) setTotalLaborStated(costData.total_labor_cost);
        setPackagingCost(costData.packaging_cost);
        setTransportCost(costData.transport_cost);
        setOverheadCost(costData.overhead_cost);
        setOverheadBasis(costData.overhead_allocation_basis);
        setOtherCosts(costData.other_costs);
        setBatchQuantity(costData.batch_quantity || 1);
        setDesiredMargin(costData.desired_margin_percentage);
        if (costData.current_selling_price) setCurrentSellingPrice(costData.current_selling_price);
      }

      // 3. Fetch latest Price Analysis if available
      const anaRes = await fetch(`/api/v1/products/${productId}/pricing/analysis`, { headers });
      if (anaRes.ok) {
        const anaData = await anaRes.json();
        setLatestAnalysis(anaData);
      }
    } catch (err: any) {
      console.error("Error loading pricing data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMaterial = () => {
    setMaterials([
      ...materials,
      { material_name: "", quantity: 1, unit: "meters", unit_cost_inr: 0, source_type: "ARTISAN_ENTERED" }
    ]);
  };

  const handleRemoveMaterial = (index: number) => {
    setMaterials(materials.filter((_, idx) => idx !== index));
  };

  const handleMaterialChange = (index: number, field: keyof MaterialItem, val: any) => {
    const updated = [...materials];
    updated[index] = { ...updated[index], [field]: val };
    setMaterials(updated);
  };

  const handleSaveCosts = async () => {
    setSavingCosts(true);
    setStatusMsg(null);
    const token = localStorage.getItem("access_token");

    const payload = {
      materials: materials.map(m => ({
        material_name: m.material_name || "Material",
        quantity: parseFloat(String(m.quantity)) || 1,
        unit: m.unit || "units",
        unit_cost_inr: parseFloat(String(m.unit_cost_inr)) || 0,
        source_type: m.source_type || "ARTISAN_ENTERED",
        source_reference: m.source_reference || null
      })),
      labor_calculation_method: laborMethod,
      labor_hours: laborMethod === "HOURLY_RATE" ? (parseFloat(String(laborHours)) || 0) : null,
      hourly_labor_rate: laborMethod === "HOURLY_RATE" ? (parseFloat(String(laborRate)) || 0) : null,
      total_labor_cost: laborMethod === "TOTAL_STATED" ? (parseFloat(String(totalLaborStated)) || 0) : null,
      packaging_cost: parseFloat(String(packagingCost)) || 0,
      transport_cost: parseFloat(String(transportCost)) || 0,
      overhead_cost: parseFloat(String(overheadCost)) || 0,
      overhead_allocation_basis: overheadBasis,
      other_costs: parseFloat(String(otherCosts)) || 0,
      batch_quantity: parseInt(String(batchQuantity)) || 1,
      currency: "INR",
      current_selling_price: parseFloat(String(currentSellingPrice)) || null,
      desired_margin_percentage: parseFloat(String(desiredMargin)) || 25
    };

    try {
      const res = await fetch(`/api/v1/products/${productId}/pricing/costs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to save production costs.");
      }

      setStatusMsg({ type: "success", text: "Production cost structure saved successfully." });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message });
    } finally {
      setSavingCosts(false);
    }
  };

  const handleRunAnalysis = async () => {
    setAnalyzing(true);
    setStatusMsg(null);
    const token = localStorage.getItem("access_token");

    try {
      // First save costs
      await handleSaveCosts();

      const res = await fetch(`/api/v1/products/${productId}/pricing/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(null)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to calculate fair price analysis.");
      }

      const data = await res.json();
      setLatestAnalysis(data);
      setStatusMsg({ type: "success", text: "Fair price analysis computed successfully using FAIR_PRICE_ENGINE_V1." });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message });
    } finally {
      setAnalyzing(false);
    }
  };

  const handleConfirmPrice = async () => {
    if (!latestAnalysis) return;
    setConfirmingPrice(true);
    setStatusMsg(null);
    const token = localStorage.getItem("access_token");

    try {
      const res = await fetch(`/api/v1/products/${productId}/pricing/confirm?analysis_id=${latestAnalysis.id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          confirmed_price_inr: latestAnalysis.fair_price_analysis.recommended_price,
          artisan_notes: confirmedNotes || "Confirmed fair price applied to product catalogue.",
          apply_to_product: true
        })
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Failed to confirm fair price.");
      }

      const updated = await res.json();
      setLatestAnalysis(updated);
      if (product) {
        setProduct({ ...product, price_inr: updated.confirmed_price_inr });
      }
      setStatusMsg({ type: "success", text: `Confirmed fair price of ₹${updated.confirmed_price_inr} applied to your product listing!` });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message });
    } finally {
      setConfirmingPrice(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6">
        <div className="flex items-center gap-3 text-slate-600">
          <RefreshCw className="w-5 h-5 animate-spin text-amber-600" />
          <span>Loading Fair-Price Intelligence Studio...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 pb-16">
      {/* Header Bar */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <Link
              href="/artisan/products"
              className="p-2 text-slate-500 hover:text-slate-900 rounded-lg hover:bg-slate-100 transition"
              title="Back to products"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-slate-900">{product?.title || "Craft Product"}</h1>
                <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-600 border border-slate-200">
                  {product?.sku}
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Fair-Price Intelligence Engine (FAIR_PRICE_ENGINE_V1) • Cost Breakdown & Market Evidence
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href={`/artisan/products/${productId}/ai-studio`}
              className="px-3 py-1.5 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg border border-slate-300 flex items-center gap-1.5 transition"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              AI Studio
            </Link>
            <div className="text-right">
              <span className="text-xs text-slate-500 block">Current Listed Price</span>
              <span className="text-base font-bold text-slate-900">₹{product?.price_inr ?? "—"}</span>
            </div>
          </div>
        </div>

        {/* Provenance Explainer Strip */}
        <div className="bg-slate-100/80 border-t border-slate-200/80 px-4 py-2 text-xs text-slate-600">
          <div className="max-w-7xl mx-auto flex flex-wrap items-center gap-4 justify-between">
            <div className="flex items-center gap-1.5 font-medium text-slate-700">
              <Scale className="w-4 h-4 text-amber-700" />
              <span>Transparent Information States:</span>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-mono text-[11px] border border-blue-200">
                ARTISAN_PROVIDED
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-mono text-[11px] border border-emerald-200">
                SOURCE_BACKED
              </span>
              <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-mono text-[11px] border border-purple-200">
                CALCULATED
              </span>
              <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-mono text-[11px] border border-amber-200">
                HUMAN_CONFIRMED
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
        {statusMsg && (
          <div
            className={`mb-6 p-4 rounded-xl border flex items-start gap-3 ${
              statusMsg.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-emerald-900"
                : "bg-red-50 border-red-200 text-red-900"
            }`}
          >
            {statusMsg.type === "success" ? (
              <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
            )}
            <p className="text-sm">{statusMsg.text}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* ========================================================= */}
          {/* LEFT: PRODUCTION COST BREAKDOWN FORM (ARTISAN INPUTS) */}
          {/* ========================================================= */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
              <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
                <div className="flex items-center gap-2">
                  <Calculator className="w-5 h-5 text-amber-700" />
                  <h2 className="text-base font-semibold text-slate-900">Production Cost Structure</h2>
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                  ARTISAN_PROVIDED
                </span>
              </div>

              {/* 1. Itemized Raw Materials */}
              <div className="space-y-3 mb-6">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                    1. Raw Materials ({materials.length})
                  </label>
                  <button
                    type="button"
                    onClick={handleAddMaterial}
                    className="text-xs text-amber-800 hover:text-amber-900 font-medium flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" /> Add Material
                  </button>
                </div>

                <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
                  {materials.map((m, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2">
                      <div className="flex items-center justify-between gap-2">
                        <input
                          type="text"
                          placeholder="Material name (e.g. Silk yarn)"
                          value={m.material_name}
                          onChange={(e) => handleMaterialChange(idx, "material_name", e.target.value)}
                          className="w-full text-xs font-medium px-2 py-1 bg-white border border-slate-300 rounded focus:ring-1 focus:ring-amber-500"
                        />
                        {materials.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveMaterial(idx)}
                            className="text-slate-400 hover:text-red-600 p-1"
                            title="Remove line"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        )}
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div>
                          <label className="text-[10px] text-slate-500 block">Quantity</label>
                          <input
                            type="number"
                            step="0.1"
                            min="0.01"
                            value={m.quantity}
                            onChange={(e) => handleMaterialChange(idx, "quantity", e.target.value)}
                            className="w-full px-2 py-1 bg-white border border-slate-300 rounded text-xs"
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-500 block">Unit</label>
                          <input
                            type="text"
                            placeholder="m, kg, pc"
                            value={m.unit}
                            onChange={(e) => handleMaterialChange(idx, "unit", e.target.value)}
                            className="w-full px-2 py-1 bg-white border border-slate-300 rounded text-xs"
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-500 block">Unit Cost (₹)</label>
                          <input
                            type="number"
                            step="1"
                            min="0"
                            value={m.unit_cost_inr}
                            onChange={(e) => handleMaterialChange(idx, "unit_cost_inr", e.target.value)}
                            className="w-full px-2 py-1 bg-white border border-slate-300 rounded text-xs font-mono"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 2. Labor Calculations */}
              <div className="space-y-3 mb-6 pt-4 border-t border-slate-100">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">
                  2. Skilled Artisan Labor
                </label>
                <div className="flex gap-4 text-xs mb-2">
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="labor_mode"
                      checked={laborMethod === "HOURLY_RATE"}
                      onChange={() => setLaborMethod("HOURLY_RATE")}
                      className="text-amber-600 focus:ring-amber-500"
                    />
                    <span>Hourly Wage Rate</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      name="labor_mode"
                      checked={laborMethod === "TOTAL_STATED"}
                      onChange={() => setLaborMethod("TOTAL_STATED")}
                      className="text-amber-600 focus:ring-amber-500"
                    />
                    <span>Stated Total Labor Cost</span>
                  </label>
                </div>

                {laborMethod === "HOURLY_RATE" ? (
                  <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                    <div>
                      <label className="text-slate-600 block mb-1">Production Hours</label>
                      <input
                        type="number"
                        step="0.5"
                        min="0"
                        value={laborHours}
                        onChange={(e) => setLaborHours(e.target.value)}
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs"
                      />
                    </div>
                    <div>
                      <label className="text-slate-600 block mb-1">Hourly Rate (₹/hr)</label>
                      <input
                        type="number"
                        step="5"
                        min="0"
                        value={laborRate}
                        onChange={(e) => setLaborRate(e.target.value)}
                        className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs font-mono"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs">
                    <label className="text-slate-600 block mb-1">Total Labor Cost for Batch (₹)</label>
                    <input
                      type="number"
                      step="50"
                      min="0"
                      value={totalLaborStated}
                      onChange={(e) => setTotalLaborStated(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-white border border-slate-300 rounded text-xs font-mono"
                    />
                  </div>
                )}
              </div>

              {/* 3. Direct Costs: Packaging & Transport */}
              <div className="space-y-3 mb-6 pt-4 border-t border-slate-100">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">
                  3. Packaging & Logistics (₹)
                </label>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="text-slate-600 block mb-1">Packaging Cost (₹)</label>
                    <input
                      type="number"
                      min="0"
                      value={packagingCost}
                      onChange={(e) => setPackagingCost(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-600 block mb-1">Transport / Freight (₹)</label>
                    <input
                      type="number"
                      min="0"
                      value={transportCost}
                      onChange={(e) => setTransportCost(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* 4. Overhead Allocation */}
              <div className="space-y-3 mb-6 pt-4 border-t border-slate-100">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">
                  4. Overhead & Workspace Costs
                </label>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="text-slate-600 block mb-1">Overhead Amount (₹)</label>
                    <input
                      type="number"
                      min="0"
                      value={overheadCost}
                      onChange={(e) => setOverheadCost(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-600 block mb-1">Allocation Basis</label>
                    <select
                      value={overheadBasis}
                      onChange={(e) => setOverheadBasis(e.target.value)}
                      className="w-full px-2 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs"
                    >
                      <option value="PER_PRODUCT">Per Single Product</option>
                      <option value="PER_BATCH">Per Entire Batch</option>
                      <option value="MONTHLY_ALLOCATION">Monthly Allocation</option>
                      <option value="DOCUMENTED_PERCENTAGE">Documented Direct</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* 5. Batch & Margin Settings */}
              <div className="space-y-3 mb-6 pt-4 border-t border-slate-100">
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wide block">
                  5. Quantity & Desired Profit Margin
                </label>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <label className="text-slate-600 block mb-1">Batch Quantity (units)</label>
                    <input
                      type="number"
                      min="1"
                      value={batchQuantity}
                      onChange={(e) => setBatchQuantity(parseInt(e.target.value) || 1)}
                      className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs font-mono"
                    />
                  </div>
                  <div>
                    <label className="text-slate-600 block mb-1">Desired Profit Margin (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="200"
                      value={desiredMargin}
                      onChange={(e) => setDesiredMargin(e.target.value)}
                      className="w-full px-2.5 py-1.5 bg-slate-50 border border-slate-300 rounded text-xs font-mono"
                    />
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-col gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleSaveCosts}
                  disabled={savingCosts}
                  className="w-full py-2.5 px-4 bg-slate-800 hover:bg-slate-900 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition"
                >
                  {savingCosts ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  Save Production Costs
                </button>

                <button
                  type="button"
                  onClick={handleRunAnalysis}
                  disabled={analyzing}
                  className="w-full py-2.5 px-4 bg-amber-700 hover:bg-amber-800 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition"
                >
                  {analyzing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Calculator className="w-4 h-4" />}
                  Run Evidence-Based Price Analysis
                </button>
              </div>
            </div>
          </div>

          {/* ========================================================= */}
          {/* RIGHT: FAIR PRICE INTELLIGENCE ANALYSIS & EXPLANATION */}
          {/* ========================================================= */}
          <div className="lg:col-span-7 space-y-6">
            {!latestAnalysis ? (
              <div className="bg-white rounded-xl border border-dashed border-slate-300 p-12 text-center">
                <Scale className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <h3 className="text-sm font-semibold text-slate-800">No Fair-Price Analysis Generated Yet</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1 mb-6">
                  Complete the production cost structure on the left and click "Run Evidence-Based Price Analysis" to synthesize cost economics with documented market benchmarks.
                </p>
                <button
                  type="button"
                  onClick={handleRunAnalysis}
                  disabled={analyzing}
                  className="py-2 px-4 bg-amber-700 hover:bg-amber-800 text-white rounded-lg text-xs font-semibold inline-flex items-center gap-2"
                >
                  <Calculator className="w-4 h-4" /> Calculate Price Analysis
                </button>
              </div>
            ) : (
              <div className="space-y-6">
                {/* CARD A: COST BASELINE */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-800 font-bold text-xs flex items-center justify-center">
                        A
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">Cost-Based Production Baseline</h3>
                    </div>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                      CALCULATED
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <span className="text-[10px] text-slate-500 block">Unit Production Cost</span>
                      <span className="text-base font-bold text-slate-900 font-mono">
                        ₹{latestAnalysis.cost_baseline.unit_production_cost}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <span className="text-[10px] text-slate-500 block">Total Batch Cost</span>
                      <span className="text-base font-bold text-slate-900 font-mono">
                        ₹{latestAnalysis.cost_baseline.total_production_cost}
                      </span>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-lg">
                      <span className="text-[10px] text-slate-500 block">Stated Margin</span>
                      <span className="text-base font-bold text-slate-900 font-mono">
                        {latestAnalysis.cost_baseline.desired_margin_percentage}%
                      </span>
                    </div>
                    <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg">
                      <span className="text-[10px] text-blue-700 block font-medium">Cost Baseline Price</span>
                      <span className="text-base font-extrabold text-blue-900 font-mono">
                        ₹{latestAnalysis.cost_baseline.cost_baseline_price}
                      </span>
                    </div>
                  </div>
                </div>

                {/* CARD B: MARKET EVIDENCE */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 font-bold text-xs flex items-center justify-center">
                        B
                      </span>
                      <h3 className="text-sm font-bold text-slate-900">Documented Market Evidence</h3>
                    </div>
                    <span
                      className={`text-[11px] font-mono px-2 py-0.5 rounded border ${
                        latestAnalysis.evidence_status === "SUFFICIENT_MARKET_EVIDENCE"
                          ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                          : "bg-amber-50 text-amber-800 border-amber-200"
                      }`}
                    >
                      {latestAnalysis.evidence_status}
                    </span>
                  </div>

                  {latestAnalysis.evidence_status === "INSUFFICIENT_MARKET_EVIDENCE" ? (
                    <div className="p-4 bg-amber-50/70 border border-amber-200 rounded-lg flex items-start gap-3 text-xs text-amber-900">
                      <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                      <div>
                        <p className="font-semibold mb-0.5">Insufficient Market Evidence ({latestAnalysis.market_evidence.observation_count} observations found)</p>
                        <p className="text-amber-800">
                          The system strictly requires at least 3 comparable documented market observations to calculate a defensible market price range. In accordance with the project's strict no-fabrication policy, no synthetic market prices or averages have been invented.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-xs">
                        <div className="p-2.5 bg-slate-50 rounded-lg">
                          <span className="text-[10px] text-slate-500 block">Comparable Records</span>
                          <span className="text-sm font-bold text-slate-900">{latestAnalysis.market_evidence.observation_count}</span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-lg">
                          <span className="text-[10px] text-slate-500 block">Observed Median</span>
                          <span className="text-sm font-bold text-slate-900 font-mono">₹{latestAnalysis.market_evidence.median_inr}</span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-lg">
                          <span className="text-[10px] text-slate-500 block">Full Range</span>
                          <span className="text-sm font-bold text-slate-900 font-mono">
                            ₹{latestAnalysis.market_evidence.min_inr} – ₹{latestAnalysis.market_evidence.max_inr}
                          </span>
                        </div>
                        <div className="p-2.5 bg-slate-50 rounded-lg">
                          <span className="text-[10px] text-slate-500 block">Quality Rating</span>
                          <span className="text-sm font-bold text-emerald-700">{latestAnalysis.market_evidence.quality_rating}</span>
                        </div>
                      </div>

                      {latestAnalysis.market_evidence.sources_used && latestAnalysis.market_evidence.sources_used.length > 0 && (
                        <div className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                          <span className="font-medium text-slate-700">Sources Referenced: </span>
                          <span>{latestAnalysis.market_evidence.sources_used.join(" • ")}</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* CARD C: FAIR PRICE ANALYSIS */}
                <div className="bg-white rounded-xl border-2 border-amber-500/30 shadow-md p-6 relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-amber-600 text-white text-[10px] font-bold px-3 py-1 rounded-bl-lg font-mono">
                    {latestAnalysis.engine_version}
                  </div>

                  <div className="flex items-center gap-2 mb-4">
                    <span className="w-6 h-6 rounded-full bg-amber-100 text-amber-900 font-bold text-xs flex items-center justify-center">
                      C
                    </span>
                    <h3 className="text-base font-bold text-slate-900">Evidence-Based Fair Price Range</h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6 text-center">
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <span className="text-xs text-slate-500 block mb-1">Recommended Floor Price</span>
                      <span className="text-lg font-bold text-slate-900 font-mono">
                        ₹{latestAnalysis.fair_price_analysis.floor_price}
                      </span>
                      <span className="text-[10px] text-slate-400 block mt-1">Guarantees no loss on unit cost</span>
                    </div>

                    <div className="p-4 bg-amber-50 border-2 border-amber-600/30 rounded-xl">
                      <span className="text-xs text-amber-800 font-medium block mb-1">Recommended Fair Retail Price</span>
                      <span className="text-2xl font-black text-amber-900 font-mono">
                        ₹{latestAnalysis.fair_price_analysis.recommended_price}
                      </span>
                      <span className="text-[10px] text-amber-700 block mt-1">Defensible market position</span>
                    </div>

                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <span className="text-xs text-slate-500 block mb-1">Suggested Fair Retail Range</span>
                      <span className="text-lg font-bold text-slate-900 font-mono">
                        ₹{latestAnalysis.fair_price_analysis.price_range_min} – ₹{latestAnalysis.fair_price_analysis.price_range_max}
                      </span>
                      <span className="text-[10px] text-slate-400 block mt-1">Based on IQR / margin tier</span>
                    </div>
                  </div>

                  {/* Confirmation Section */}
                  <div className="pt-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="text-xs text-slate-600">
                      {latestAnalysis.is_confirmed_by_artisan ? (
                        <div className="flex items-center gap-1.5 text-emerald-700 font-medium">
                          <CheckCircle2 className="w-4 h-4" />
                          <span>Confirmed by artisan: ₹{latestAnalysis.confirmed_price_inr} (HUMAN_CONFIRMED)</span>
                        </div>
                      ) : (
                        <span>You can apply this recommended fair price directly to your product listing.</span>
                      )}
                    </div>

                    <button
                      type="button"
                      onClick={handleConfirmPrice}
                      disabled={confirmingPrice}
                      className="w-full sm:w-auto px-5 py-2.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition"
                    >
                      {confirmingPrice ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                      Confirm & Apply Fair Price (₹{latestAnalysis.fair_price_analysis.recommended_price})
                    </button>
                  </div>
                </div>

                {/* CARD D: STEP-BY-STEP EXPLANATION */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                  <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-4">
                    <span className="w-6 h-6 rounded-full bg-purple-100 text-purple-800 font-bold text-xs flex items-center justify-center">
                      D
                    </span>
                    <h3 className="text-sm font-bold text-slate-900">Traceable Step-by-Step Explanation</h3>
                  </div>

                  <div className="space-y-3">
                    {latestAnalysis.explanation_steps.map((step, idx) => (
                      <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between font-semibold text-slate-800">
                          <span>{step.step_number}. {step.title}</span>
                        </div>
                        <p className="text-slate-600 leading-relaxed">{step.detail}</p>
                        {step.mathematical_formula && (
                          <div className="mt-1 font-mono text-[11px] text-amber-900 bg-amber-50/60 px-2 py-0.5 rounded border border-amber-200/50">
                            {step.mathematical_formula}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* CARD E: LIMITATIONS & ECONOMIC REALITIES */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-5">
                  <div className="flex items-center gap-2 pb-3 border-b border-slate-100 mb-3">
                    <span className="w-6 h-6 rounded-full bg-slate-100 text-slate-800 font-bold text-xs flex items-center justify-center">
                      E
                    </span>
                    <h3 className="text-sm font-bold text-slate-900">Evidence Limitations & Assumptions</h3>
                  </div>

                  <ul className="space-y-1.5 text-xs text-slate-600 list-disc list-inside">
                    {latestAnalysis.limitations_notes.map((note, idx) => (
                      <li key={idx} className="leading-relaxed">{note}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
