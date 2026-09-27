"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  Package,
  Inbox,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Eye,
  RefreshCw
} from "lucide-react";

export default function ArtisanIncomingRFQsPage() {
  const [rfqs, setRfqs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadIncomingRFQs();
  }, []);

  const loadIncomingRFQs = async () => {
    setLoading(true);
    const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    try {
      const res = await fetch("/api/v1/rfqs/incoming", {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (res.ok) {
        const data = await res.json();
        setRfqs(data);
      }
    } catch (err) {
      console.error("Error loading incoming RFQs:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 pb-20">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <span>Incoming Buyer RFQs</span>
              <span className="text-xs bg-emerald-50 text-emerald-700 font-semibold px-2 py-0.5 rounded-full border border-emerald-200">
                Direct Market Linkage
              </span>
            </h1>
            <p className="text-xs text-slate-500">Commercial procurement enquiries matched with your craft capacity</p>
          </div>

          <Link
            href="/artisan/products"
            className="px-4 py-2 bg-white border border-slate-200 text-slate-700 text-xs font-semibold rounded-xl hover:bg-slate-50"
          >
            My Catalogue
          </Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        {loading ? (
          <div className="p-12 text-center text-slate-400">Loading incoming RFQs...</div>
        ) : rfqs.length === 0 ? (
          <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3">
            <Inbox className="w-10 h-10 text-slate-300 mx-auto" />
            <h3 className="font-bold text-slate-800 text-base">No Incoming RFQs Right Now</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              Ensure your products are PUBLISHED with accurate production capacity and materials to receive buyer matches.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {rfqs.map((rfq) => {
              const statusColors: Record<string, string> = {
                SENT: "bg-blue-100 text-blue-800 border-blue-200",
                VIEWED: "bg-purple-100 text-purple-800 border-purple-200",
                NEGOTIATION: "bg-amber-100 text-amber-800 border-amber-200",
                ACCEPTED: "bg-emerald-100 text-emerald-800 border-emerald-200",
                DECLINED: "bg-rose-100 text-rose-800 border-rose-200"
              };

              const isNew = rfq.status === "SENT";

              return (
                <div
                  key={rfq.id}
                  className={`bg-white border rounded-xl p-5 shadow-sm space-y-3 transition-all hover:border-slate-300 ${
                    isNew ? "border-blue-200 bg-blue-50/20" : "border-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-700 bg-slate-100 px-2.5 py-1 rounded-md">
                        {rfq.rfq_reference_number || "RFQ-PENDING"}
                      </span>
                      <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${statusColors[rfq.status] || "bg-slate-100 text-slate-700 border-slate-200"}`}>
                        {rfq.status}
                      </span>
                      {isNew && (
                        <span className="text-[10px] bg-blue-600 text-white font-bold px-2 py-0.5 rounded-full">
                          NEW
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-slate-400">
                      Received: {new Date(rfq.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs pt-1">
                    <div>
                      <p className="text-slate-400">Buyer Company</p>
                      <p className="font-bold text-slate-800">{rfq.buyer_company_name || "Institutional Buyer"}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Requested Volume</p>
                      <p className="font-bold text-slate-800">{rfq.proposed_quantity} units</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Offered Unit Price</p>
                      <p className="font-bold text-slate-800">₹{rfq.proposed_unit_price}</p>
                    </div>
                    <div>
                      <p className="text-slate-400">Estimated Total Order</p>
                      <p className="font-bold text-emerald-700 text-sm">
                        ₹{(rfq.proposed_quantity * Number(rfq.proposed_unit_price)).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-lg">
                    "{rfq.message}"
                  </p>

                  <div className="flex justify-end pt-2">
                    <Link
                      href={`/artisan/rfqs/${rfq.id}`}
                      className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 shadow-sm"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Review Terms & Respond</span>
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
