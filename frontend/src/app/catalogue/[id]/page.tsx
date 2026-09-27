"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, ShieldCheck, MapPin, Calendar, Clock, PackageCheck, Sparkles, Layers } from "lucide-react";

interface MediaAsset {
  id: string;
  url: string;
  original_filename: string;
  mime_type: string;
  is_primary: boolean;
}

interface ProductDetail {
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
  availability_status: string;
  region?: string;
  materials: string[];
  primary_color?: string;
  dimensions?: string;
  weight_grams?: number;
  technique?: string;
  style?: string;
  tags: string[];
  is_customizable: boolean;
  status: string;
  provenance_status: string;
  craft_name?: string;
  category_name?: string;
  artisan_public_name?: string;
  artisan_district?: string;
  artisan_state?: string;
  has_gi_tag: boolean;
  gi_tag_number?: string;
  media: MediaAsset[];
  created_at: string;
}

export default function ProductDetailPage() {
  const params = useParams();
  const productId = params?.id as string;
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeMedia, setActiveMedia] = useState<string | null>(null);

  useEffect(() => {
    if (!productId) return;
    fetch(`/api/v1/products/${productId}`)
      .then((res) => {
        if (res.ok) return res.json();
        throw new Error("Product not found");
      })
      .then((data: ProductDetail) => {
        setProduct(data);
        if (data.media && data.media.length > 0) {
          const primary = data.media.find((m) => m.is_primary) || data.media[0];
          setActiveMedia(primary.url);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [productId]);

  if (loading) {
    return <div className="min-h-screen bg-stone-50 p-16 text-center text-stone-500">Loading craft product...</div>;
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-stone-50 p-16 text-center space-y-4">
        <h2 className="text-xl font-bold text-stone-800">Product Not Found</h2>
        <p className="text-stone-500 text-sm">The listing may have been retired or is pending administrative review.</p>
        <Link href="/catalogue" className="inline-block px-4 py-2 bg-amber-800 text-white rounded-lg text-sm">
          Return to Catalogue
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex items-center gap-3">
          <Link
            href="/catalogue"
            className="p-2 bg-white rounded-lg border border-stone-200 text-stone-600 hover:text-stone-900 shadow-sm"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="text-sm text-stone-500">
            <span>Catalogue</span> / <span className="font-semibold text-stone-900">{product.craft_name}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 bg-white rounded-2xl shadow-sm border border-stone-200 p-6 sm:p-8">
          {/* Media Gallery */}
          <div className="space-y-4">
            <div className="aspect-square bg-stone-100 rounded-xl overflow-hidden border border-stone-200 flex items-center justify-center">
              {activeMedia ? (
                <img src={activeMedia} alt={product.title} className="w-full h-full object-cover" />
              ) : (
                <div className="text-center p-6 text-stone-400">
                  <PackageCheck className="w-16 h-16 mx-auto mb-2 opacity-50" />
                  <p className="text-xs">Authentic Verified Craft Listing</p>
                </div>
              )}
            </div>

            {product.media && product.media.length > 1 && (
              <div className="flex gap-3 overflow-x-auto pb-2">
                {product.media.map((m) => (
                  <button
                    key={m.id}
                    onClick={() => setActiveMedia(m.url)}
                    className={`h-16 w-16 flex-shrink-0 rounded-lg overflow-hidden border-2 transition-all ${
                      activeMedia === m.url ? "border-amber-800 shadow-sm" : "border-stone-200 opacity-70"
                    }`}
                  >
                    <img src={m.url} alt={m.original_filename} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            )}

            {/* Provenance & GI Information Card */}
            <div className="bg-stone-50 rounded-xl p-4 border border-stone-200 space-y-3">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-amber-800" />
                <h4 className="text-xs font-bold uppercase tracking-wider text-stone-900">
                  Authentic Provenance & Registry Verification
                </h4>
              </div>
              <div className="text-xs text-stone-600 space-y-1">
                <div>Provenance Status: <strong className="text-amber-900 font-semibold">{product.provenance_status}</strong></div>
                {product.has_gi_tag && (
                  <div>
                    Geographical Indication (GI): <span className="font-semibold text-stone-900">{product.gi_tag_number || "Certified"}</span>
                  </div>
                )}
                <div>Origin Region: {product.region || `${product.artisan_district}, ${product.artisan_state}`}</div>
              </div>
            </div>
          </div>

          {/* Product Commercials & Storytelling */}
          <div className="space-y-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div>
                <div className="text-xs font-mono text-stone-400">SKU: {product.sku}</div>
                <h1 className="text-2xl sm:text-3xl font-bold text-stone-900 mt-1">{product.title}</h1>
                <div className="flex items-center gap-2 mt-2 text-xs text-stone-500">
                  <MapPin className="w-3.5 h-3.5 text-stone-400" />
                  <span>{product.artisan_district ? `${product.artisan_district}, ` : ""}{product.artisan_state || "India"}</span>
                  <span>•</span>
                  <span>Artisan: <strong className="text-stone-800">{product.artisan_public_name}</strong></span>
                </div>
              </div>

              {/* Price Banner */}
              <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase font-semibold text-amber-800">Fair Direct Artisan Price</div>
                  <div className="text-3xl font-extrabold text-amber-950">
                    ₹{product.price_inr.toLocaleString("en-IN")}
                  </div>
                  <div className="text-xs text-stone-500 mt-0.5">INR (Taxes & Craft Packaging Included)</div>
                </div>
                <div className="text-right">
                  <span className="inline-block px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
                    {product.stock_quantity > 0 ? `${product.stock_quantity} Ready Stock` : "Made to Order"}
                  </span>
                </div>
              </div>

              {/* Storytelling Narrative */}
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-stone-700 mb-2">
                  Craft Storytelling & Cultural Heritage
                </h3>
                <p className="text-sm text-stone-700 leading-relaxed bg-stone-50/50 p-4 rounded-xl border border-stone-100">
                  {product.storytelling_description}
                </p>
              </div>

              {/* Technical Specifications */}
              <div className="grid grid-cols-2 gap-3 text-xs">
                {product.technique && (
                  <div className="bg-stone-50 p-3 rounded-lg border border-stone-100">
                    <span className="text-stone-400 block font-medium">Technique</span>
                    <span className="font-semibold text-stone-800">{product.technique}</span>
                  </div>
                )}
                {product.materials && product.materials.length > 0 && (
                  <div className="bg-stone-50 p-3 rounded-lg border border-stone-100">
                    <span className="text-stone-400 block font-medium">Authentic Materials</span>
                    <span className="font-semibold text-stone-800">{product.materials.join(", ")}</span>
                  </div>
                )}
                {product.dimensions && (
                  <div className="bg-stone-50 p-3 rounded-lg border border-stone-100">
                    <span className="text-stone-400 block font-medium">Dimensions</span>
                    <span className="font-semibold text-stone-800">{product.dimensions}</span>
                  </div>
                )}
                {product.weight_grams && (
                  <div className="bg-stone-50 p-3 rounded-lg border border-stone-100">
                    <span className="text-stone-400 block font-medium">Net Weight</span>
                    <span className="font-semibold text-stone-800">{product.weight_grams} grams</span>
                  </div>
                )}
              </div>

              {/* Procurement & Capacity Parameters */}
              <div className="pt-2 border-t border-stone-100">
                <h4 className="text-xs font-bold uppercase tracking-wider text-stone-700 mb-2">
                  Procurement & Production Parameters
                </h4>
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="p-2.5 bg-stone-50 rounded-lg border border-stone-200">
                    <div className="text-xs text-stone-500">Monthly Capacity</div>
                    <div className="text-sm font-bold text-stone-900">{product.monthly_production_capacity} pcs</div>
                  </div>
                  <div className="p-2.5 bg-stone-50 rounded-lg border border-stone-200">
                    <div className="text-xs text-stone-500">Min Order Qty</div>
                    <div className="text-sm font-bold text-stone-900">{product.min_order_quantity} pcs</div>
                  </div>
                  <div className="p-2.5 bg-stone-50 rounded-lg border border-stone-200">
                    <div className="text-xs text-stone-500">Lead Time</div>
                    <div className="text-sm font-bold text-stone-900">{product.lead_time_days} days</div>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-stone-200">
              <Link
                href="/buyer/profile"
                className="w-full block py-3 bg-amber-800 text-white rounded-xl text-center text-sm font-semibold hover:bg-amber-900 transition-colors shadow-sm"
              >
                Inquire / Place Order as Buyer
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
