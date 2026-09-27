"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { Package, Plus, AlertCircle, CheckCircle, Clock, XCircle, ArrowRight } from "lucide-react";

interface Product {
  id: string;
  sku: string;
  title: string;
  craft_name?: string;
  price_inr: number;
  stock_quantity: number;
  monthly_production_capacity: number;
  min_order_quantity: number;
  lead_time_days: number;
  status: string;
  provenance_status: string;
  created_at: string;
  admin_feedback?: string;
}

export default function ArtisanProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [submittingId, setSubmittingId] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchProducts = async () => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      const res = await fetch("/api/v1/artisans/me/products", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      } else {
        setStatusMessage("Failed to load products. Ensure you have created your artisan profile.");
      }
    } catch {
      setStatusMessage("Error connecting to server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleSubmitForReview = async (id: string) => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    setSubmittingId(id);
    try {
      const res = await fetch(`/api/v1/products/${id}/submit`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setStatusMessage("Product submitted for administrative moderation.");
        fetchProducts();
      } else {
        const err = await res.json();
        setStatusMessage(err.detail || "Submission failed.");
      }
    } catch {
      setStatusMessage("Network error during submission.");
    } finally {
      setSubmittingId(null);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "PUBLISHED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <CheckCircle className="w-3.5 h-3.5" /> Published
          </span>
        );
      case "PENDING_REVIEW":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            <Clock className="w-3.5 h-3.5" /> Pending Review
          </span>
        );
      case "REJECTED":
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            <XCircle className="w-3.5 h-3.5" /> Rejected
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-stone-100 text-stone-700 border border-stone-200">
            Draft
          </span>
        );
    }
  };

  return (
    <div className="min-h-screen bg-stone-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm text-stone-500">
              <Link href="/artisan/profile" className="hover:text-amber-800">Artisan Workspace</Link>
              <span>/</span>
              <span className="text-stone-900 font-medium">Product Catalogue</span>
            </div>
            <h1 className="text-2xl font-bold text-stone-900 mt-1">My Craft Products</h1>
          </div>
          <Link
            href="/artisan/products/new"
            className="inline-flex items-center gap-2 px-4 py-2 bg-amber-800 text-white rounded-lg hover:bg-amber-900 transition-colors shadow-sm text-sm font-medium"
          >
            <Plus className="w-4 h-4" /> Add New Craft Listing
          </Link>
        </div>

        {statusMessage && (
          <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-700" />
              <span>{statusMessage}</span>
            </div>
            <button onClick={() => setStatusMessage(null)} className="text-amber-700 hover:text-amber-900 font-bold">✕</button>
          </div>
        )}

        {/* Product List */}
        {loading ? (
          <div className="bg-white rounded-xl p-12 text-center text-stone-500 shadow-sm border border-stone-200">
            Loading products...
          </div>
        ) : products.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center shadow-sm border border-stone-200 space-y-4">
            <Package className="w-12 h-12 text-stone-300 mx-auto" />
            <h3 className="text-lg font-semibold text-stone-800">No craft listings yet</h3>
            <p className="text-stone-500 text-sm max-w-md mx-auto">
              Digitize your handmade craft items with transparent provenance, stock quantities, and sustainable monthly production capacity.
            </p>
            <Link
              href="/artisan/products/new"
              className="inline-flex items-center gap-2 px-4 py-2 bg-amber-800 text-white rounded-lg hover:bg-amber-900 transition-colors text-sm font-medium"
            >
              <Plus className="w-4 h-4" /> Create First Product
            </Link>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-stone-600">
                <thead className="bg-stone-50 text-stone-700 font-semibold border-b border-stone-200 uppercase text-xs tracking-wider">
                  <tr>
                    <th className="py-3.5 px-4">Product / SKU</th>
                    <th className="py-3.5 px-4">Craft Tradition</th>
                    <th className="py-3.5 px-4">Price (INR)</th>
                    <th className="py-3.5 px-4">Stock vs Capacity</th>
                    <th className="py-3.5 px-4">Lead Time / MOQ</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {products.map((p) => (
                    <tr key={p.id} className="hover:bg-stone-50/75 transition-colors">
                      <td className="py-4 px-4 font-medium text-stone-900">
                        <div>{p.title}</div>
                        <div className="text-xs text-stone-400 font-mono mt-0.5">{p.sku}</div>
                      </td>
                      <td className="py-4 px-4 text-stone-700">
                        {p.craft_name || "Unassigned Craft"}
                      </td>
                      <td className="py-4 px-4 font-semibold text-stone-900">
                        ₹{p.price_inr.toLocaleString("en-IN")}
                      </td>
                      <td className="py-4 px-4">
                        <div className="text-stone-800">
                          <span className="font-medium text-emerald-700">{p.stock_quantity}</span> in stock
                        </div>
                        <div className="text-xs text-stone-500">
                          {p.monthly_production_capacity}/month capacity
                        </div>
                      </td>
                      <td className="py-4 px-4 text-stone-700">
                        <div>{p.lead_time_days} days lead</div>
                        <div className="text-xs text-stone-500">MOQ: {p.min_order_quantity}</div>
                      </td>
                      <td className="py-4 px-4">
                        <div>{getStatusBadge(p.status)}</div>
                        {p.admin_feedback && (
                          <div className="text-xs text-rose-600 mt-1 max-w-xs truncate" title={p.admin_feedback}>
                            Feedback: {p.admin_feedback}
                          </div>
                        )}
                      </td>
                      <td className="py-4 px-4 text-right space-x-2 whitespace-nowrap">
                        <Link
                          href={`/artisan/products/${p.id}/pricing`}
                          className="px-2.5 py-1 text-xs font-semibold text-amber-900 bg-amber-50 hover:bg-amber-100 border border-amber-200 rounded transition-colors inline-block"
                        >
                          Fair Price
                        </Link>
                        <Link
                          href={`/artisan/products/${p.id}/ai-studio`}
                          className="px-2.5 py-1 text-xs font-medium text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 rounded transition-colors inline-block"
                        >
                          AI Studio
                        </Link>
                        <Link
                          href={`/artisan/products/${p.id}/edit`}
                          className="px-2.5 py-1 text-xs font-medium text-stone-700 bg-stone-100 hover:bg-stone-200 rounded transition-colors inline-block"
                        >
                          Edit
                        </Link>
                        {(p.status === "DRAFT" || p.status === "REJECTED") && (
                          <button
                            onClick={() => handleSubmitForReview(p.id)}
                            disabled={submittingId === p.id}
                            className="px-2.5 py-1 text-xs font-medium text-stone-700 bg-stone-100 hover:bg-stone-200 rounded transition-colors disabled:opacity-50"
                          >
                            {submittingId === p.id ? "Submitting..." : "Submit"}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
