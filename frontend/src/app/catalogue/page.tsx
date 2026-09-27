"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Search, Filter, ShieldCheck, Tag, ArrowRight, MapPin, Layers } from "lucide-react";

interface PublicProduct {
  id: string;
  sku: string;
  title: string;
  storytelling_description: string;
  price_inr: number;
  currency: string;
  stock_quantity: number;
  monthly_production_capacity: number;
  min_order_quantity: number;
  lead_time_days: number;
  region?: string;
  materials: string[];
  technique?: string;
  provenance_status: string;
  craft_name?: string;
  artisan_public_name?: string;
  artisan_district?: string;
  artisan_state?: string;
  has_gi_tag: boolean;
  gi_tag_number?: string;
}

export default function PublicCataloguePage() {
  const [products, setProducts] = useState<PublicProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [minCapacity, setMinCapacity] = useState("");
  const [maxMoq, setMaxMoq] = useState("");
  const [regionFilter, setRegionFilter] = useState("");

  const fetchCatalogue = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (searchQuery) params.append("query", searchQuery);
    if (minPrice) params.append("min_price", minPrice);
    if (maxPrice) params.append("max_price", maxPrice);
    if (minCapacity) params.append("min_capacity", minCapacity);
    if (maxMoq) params.append("max_moq", maxMoq);
    if (regionFilter) params.append("region", regionFilter);

    try {
      const res = await fetch(`/api/v1/products?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setProducts(data.items || []);
        setTotal(data.total || 0);
      }
    } catch {
      // fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalogue();
  }, []);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCatalogue();
  };

  const handleResetFilters = () => {
    setSearchQuery("");
    setMinPrice("");
    setMaxPrice("");
    setMinCapacity("");
    setMaxMoq("");
    setRegionFilter("");
    setTimeout(() => {
      fetch("/api/v1/products")
        .then((res) => res.json())
        .then((data) => {
          setProducts(data.items || []);
          setTotal(data.total || 0);
        });
    }, 50);
  };

  return (
    <div className="min-h-screen bg-stone-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-200">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-800" />
            Verified Indian Craft Heritage & Provenance
          </span>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight">
            Indian Artisanal Craft Catalogue
          </h1>
          <p className="text-stone-600 max-w-2xl mx-auto text-sm sm:text-base">
            Discover authentic handcrafted goods from registered master artisans. Direct market linkage with transparent production capacity, lead times, and GI certification.
          </p>
        </div>

        {/* Filter Bar */}
        <form onSubmit={handleFilterSubmit} className="bg-white p-5 rounded-xl shadow-sm border border-stone-200 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-3">
            <div className="lg:col-span-2">
              <label className="block text-xs font-semibold text-stone-700 mb-1">Search Keyword</label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Craft name, technique, motif..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-stone-50 border border-stone-300 rounded-lg text-xs text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
                />
                <Search className="w-4 h-4 text-stone-400 absolute left-3 top-2.5" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Region / State</label>
              <input
                type="text"
                placeholder="e.g. Madhya Pradesh"
                value={regionFilter}
                onChange={(e) => setRegionFilter(e.target.value)}
                className="w-full px-3 py-2 bg-stone-50 border border-stone-300 rounded-lg text-xs text-stone-900 focus:bg-white focus:ring-2 focus:ring-amber-800 focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Price Range (₹)</label>
              <div className="flex items-center gap-1">
                <input
                  type="number"
                  placeholder="Min"
                  value={minPrice}
                  onChange={(e) => setMinPrice(e.target.value)}
                  className="w-full px-2 py-2 bg-stone-50 border border-stone-300 rounded-lg text-xs text-stone-900"
                />
                <span className="text-stone-400">-</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  className="w-full px-2 py-2 bg-stone-50 border border-stone-300 rounded-lg text-xs text-stone-900"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Min Monthly Capacity</label>
              <input
                type="number"
                placeholder="e.g. 20 pcs/mo"
                value={minCapacity}
                onChange={(e) => setMinCapacity(e.target.value)}
                className="w-full px-3 py-2 bg-stone-50 border border-stone-300 rounded-lg text-xs text-stone-900"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">Max MOQ</label>
              <input
                type="number"
                placeholder="e.g. 5"
                value={maxMoq}
                onChange={(e) => setMaxMoq(e.target.value)}
                className="w-full px-3 py-2 bg-stone-50 border border-stone-300 rounded-lg text-xs text-stone-900"
              />
            </div>
          </div>

          <div className="flex justify-between items-center pt-2 border-t border-stone-100">
            <span className="text-xs text-stone-500 font-medium">
              Showing {products.length} of {total} verified artisanal products
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={handleResetFilters}
                className="px-3 py-1.5 rounded-lg border border-stone-300 text-stone-600 hover:bg-stone-50 text-xs font-medium"
              >
                Reset
              </button>
              <button
                type="submit"
                className="px-4 py-1.5 bg-amber-800 text-white rounded-lg hover:bg-amber-900 text-xs font-semibold transition-colors flex items-center gap-1.5"
              >
                <Filter className="w-3.5 h-3.5" /> Apply Filters
              </button>
            </div>
          </div>
        </form>

        {/* Product Grid */}
        {loading ? (
          <div className="bg-white rounded-xl p-16 text-center text-stone-500 shadow-sm border border-stone-200">
            Filtering verified catalogue...
          </div>
        ) : products.length === 0 ? (
          <div className="bg-white rounded-xl p-16 text-center shadow-sm border border-stone-200 space-y-3">
            <p className="text-stone-700 font-semibold">No published craft products found matching criteria.</p>
            <p className="text-stone-500 text-xs">Try relaxing price, region, or MOQ filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((p) => (
              <div
                key={p.id}
                className="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden flex flex-col hover:shadow-md transition-shadow group"
              >
                <div className="p-5 flex-1 flex flex-col justify-between space-y-4">
                  <div>
                    {/* GI & Provenance Badges */}
                    <div className="flex items-center justify-between gap-2 mb-2">
                      <span className="text-xs font-semibold text-amber-800 uppercase tracking-wider">
                        {p.craft_name || "Handcrafted Tradition"}
                      </span>
                      {p.has_gi_tag && (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold bg-amber-50 text-amber-900 border border-amber-200 px-2 py-0.5 rounded-full">
                          <ShieldCheck className="w-3 h-3 text-amber-700" /> GI {p.gi_tag_number || "Protected"}
                        </span>
                      )}
                    </div>

                    <h2 className="text-base font-bold text-stone-900 group-hover:text-amber-900 transition-colors line-clamp-2">
                      {p.title}
                    </h2>

                    <p className="text-xs text-stone-600 line-clamp-2 mt-1.5">
                      {p.storytelling_description}
                    </p>
                  </div>

                  {/* Artisan & Region Info (No Private PII) */}
                  <div className="pt-3 border-t border-stone-100 text-xs text-stone-500 space-y-1">
                    <div className="flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-stone-400" />
                      <span>{p.artisan_district ? `${p.artisan_district}, ` : ""}{p.artisan_state || p.region || "India"}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-stone-400" />
                      <span>Artisan: <strong className="text-stone-700 font-medium">{p.artisan_public_name}</strong></span>
                    </div>
                  </div>

                  {/* Production & Pricing Matrix */}
                  <div className="pt-3 border-t border-stone-100 flex items-end justify-between">
                    <div>
                      <div className="text-xs text-stone-400 uppercase tracking-wider font-semibold">Fair Price</div>
                      <div className="text-lg font-extrabold text-stone-900">
                        ₹{p.price_inr.toLocaleString("en-IN")}
                      </div>
                      <div className="text-[11px] text-emerald-700 font-medium">
                        {p.stock_quantity > 0 ? `${p.stock_quantity} ready to ship` : "Made to order"}
                      </div>
                    </div>

                    <div className="text-right">
                      <div className="text-[11px] text-stone-500">Cap: {p.monthly_production_capacity}/mo</div>
                      <div className="text-[11px] text-stone-500">MOQ: {p.min_order_quantity} pcs</div>
                      <Link
                        href={`/catalogue/${p.id}`}
                        className="mt-2 inline-flex items-center gap-1 px-3 py-1.5 bg-amber-800 text-white rounded-lg hover:bg-amber-900 text-xs font-semibold transition-colors"
                      >
                        View Craft Details <ArrowRight className="w-3 h-3" />
                      </Link>
                    </div>
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
