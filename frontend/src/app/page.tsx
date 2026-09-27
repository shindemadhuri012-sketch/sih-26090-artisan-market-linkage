import React from "react";
import Link from "next/link";
import { ShieldCheck, Package, ShoppingBag, UserCheck, Layers, Sparkles } from "lucide-react";

export default function HomePage() {
  return (
    <main className="max-w-5xl mx-auto py-12 px-4 sm:px-6 lg:px-8 space-y-10">
      <header className="border-b border-stone-200 pb-8 text-center space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-200">
          <ShieldCheck className="w-4 h-4 text-amber-800" />
          Smart India Hackathon 2026 • SIH 26090
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold text-stone-900 tracking-tight">
          Artisan Market Linkage & Smart Seller Matching
        </h1>
        <p className="text-stone-600 text-base sm:text-lg max-w-2xl mx-auto">
          Production-Grade AI Market Linkage Platform for Indian Artisans, GI Crafts & Institutional Buyers.
        </p>
      </header>

      {/* Phase Completion Status Banner */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-5 text-emerald-900 space-y-1">
        <div className="flex items-center gap-2 font-bold text-sm">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 animate-pulse"></span>
          Phase 4 Complete: AI Product Studio (Image Understanding, Attribute Suggestions & Human Confirmation)
        </div>
        <p className="text-xs text-emerald-800">
          Multimodal vision understanding, versioned prompts, strict AI honesty with uncalibrated confidence transparency, server-side IDOR defense, and field-level human confirmation workflows are live.
        </p>
      </div>

      {/* Navigation Modules Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Module 1: Public Catalogue */}
        <Link
          href="/catalogue"
          className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 hover:shadow-md hover:border-amber-300 transition-all flex flex-col justify-between group"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-800 flex items-center justify-center font-bold">
              <ShoppingBag className="w-5 h-5" />
            </div>
            <h2 className="text-lg font-bold text-stone-900 group-hover:text-amber-900 transition-colors">
              Public Craft Catalogue
            </h2>
            <p className="text-xs text-stone-600">
              Browse authentic Indian crafts with GI verification, transparent fair pricing, and deterministic filtering by MOQ and capacity.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-stone-100 text-xs font-semibold text-amber-800 flex items-center gap-1">
            Explore Catalogue &rarr;
          </div>
        </Link>

        {/* Module 2: Artisan Products */}
        <Link
          href="/artisan/products"
          className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 hover:shadow-md hover:border-amber-300 transition-all flex flex-col justify-between group"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-800 flex items-center justify-center font-bold">
              <Package className="w-5 h-5" />
            </div>
            <h2 className="text-lg font-bold text-stone-900 group-hover:text-emerald-900 transition-colors">
              Artisan Product Workspace
            </h2>
            <p className="text-xs text-stone-600">
              Manage product listings, track DRAFT/PUBLISHED lifecycle status, and separate ready stock from monthly production capacity.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-stone-100 text-xs font-semibold text-emerald-800 flex items-center gap-1">
            Manage Products &rarr;
          </div>
        </Link>

        {/* Module 3: Admin Moderation */}
        <Link
          href="/admin/products"
          className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 hover:shadow-md hover:border-amber-300 transition-all flex flex-col justify-between group"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-800 flex items-center justify-center font-bold">
              <UserCheck className="w-5 h-5" />
            </div>
            <h2 className="text-lg font-bold text-stone-900 group-hover:text-blue-900 transition-colors">
              Moderation Dashboard
            </h2>
            <p className="text-xs text-stone-600">
              Administrator workflow to review submitted artisan products, verify GI heritage authenticity, and approve or reject listings.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-stone-100 text-xs font-semibold text-blue-800 flex items-center gap-1">
            Review Queue &rarr;
          </div>
        </Link>

        {/* Module 4: Artisan Profile & Passports */}
        <Link
          href="/artisan/profile"
          className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 hover:shadow-md hover:border-stone-400 transition-all flex flex-col justify-between group"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-stone-100 text-stone-800 flex items-center justify-center font-bold">
              <Layers className="w-5 h-5" />
            </div>
            <h2 className="text-lg font-bold text-stone-900">
              Artisan Profile & Passports
            </h2>
            <p className="text-xs text-stone-600">
              View and update artisan cooperative information, Pehchan ID, and verifiable Craft Passports with QR code verification.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-stone-100 text-xs font-semibold text-stone-700 flex items-center gap-1">
            View Profile &rarr;
          </div>
        </Link>

        {/* Module 5: Buyer Portal */}
        <Link
          href="/buyer/profile"
          className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 hover:shadow-md hover:border-stone-400 transition-all flex flex-col justify-between group"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-stone-100 text-stone-800 flex items-center justify-center font-bold">
              <ShoppingBag className="w-5 h-5" />
            </div>
            <h2 className="text-lg font-bold text-stone-900">
              Buyer Profile & Procurement
            </h2>
            <p className="text-xs text-stone-600">
              Configure buyer organization details, procurement volume targets, export requirements, and matching preferences.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-stone-100 text-xs font-semibold text-stone-700 flex items-center gap-1">
            Buyer Profile &rarr;
          </div>
        </Link>

        {/* Module 6: AI Product Studio */}
        <Link
          href="/artisan/products"
          className="bg-white rounded-xl shadow-sm border border-stone-200 p-6 hover:shadow-md hover:border-amber-300 transition-all flex flex-col justify-between group"
        >
          <div className="space-y-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-900 flex items-center justify-center font-bold">
              <Sparkles className="w-5 h-5" />
            </div>
            <h2 className="text-lg font-bold text-stone-900 group-hover:text-amber-900 transition-colors">
              AI Product Studio
            </h2>
            <p className="text-xs text-stone-600">
              Analyze product photographs to extract craft technique, authentic materials, and cultural storytelling suggestions with field-level human review.
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-stone-100 text-xs font-semibold text-amber-800 flex items-center gap-1">
            Launch AI Studio &rarr;
          </div>
        </Link>
      </div>

      <footer className="text-center text-xs text-stone-500 pt-6 border-t border-stone-200 space-y-1">
        <p>Backend API Endpoints: <code>/api/v1/crafts</code> | <code>/api/v1/products</code> | <code>/api/v1/products/{'{id}'}/ai/analyze</code></p>
        <p>Interactive OpenAPI Documentation: <code>http://localhost:8000/docs</code></p>
      </footer>
    </main>
  );
}
