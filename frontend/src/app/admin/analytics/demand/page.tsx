'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { BarChart3, Database, Layers, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';

interface DemandObservation {
  id: string;
  craft_id: string;
  geography_state: string;
  observation_period_start: string;
  observation_period_end: string;
  total_enquiries: number;
  fulfilled_orders: number;
  unit_volume: number;
  monetary_volume_inr?: string;
  signal_tier: string;
  observation_type: string;
  data_quality_status: string;
  is_sample_or_demo: boolean;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AdminDemandAnalyticsPage() {
  const [observations, setObservations] = useState<DemandObservation[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchObservations() {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setError('Admin authentication required.');
          setLoading(false);
          return;
        }

        const res = await fetch(`${API_BASE}/api/v1/demand/observations?limit=50`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
          throw new Error(`Failed to load observations (HTTP ${res.status})`);
        }

        const data = await res.json();
        setObservations(data);
      } catch (err: any) {
        setError(err.message || 'Error fetching demand records.');
      } finally {
        setLoading(false);
      }
    }
    fetchObservations();
  }, []);

  return (
    <div className="min-h-screen bg-stone-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <BarChart3 className="h-6 w-6 text-indigo-600" />
                <h1 className="text-2xl font-bold text-stone-900">Admin Demand Analytics & Governance</h1>
              </div>
              <p className="mt-1 text-sm text-stone-600">
                Audited real-data observations, forecast validation logs, and data quality metrics.
              </p>
            </div>
            <Link
              href="/admin/products"
              className="px-4 py-2 text-sm font-medium text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-lg transition"
            >
              Catalogue Moderation
            </Link>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-center gap-3">
            <AlertCircle className="h-5 w-5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* 3-Tier Metric Classification Banner */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl">
            <div className="flex items-center gap-2 text-blue-900 font-bold text-sm uppercase">
              <Database className="h-4 w-4 text-blue-700" />
              1. OBSERVED METRICS
            </div>
            <p className="text-xs text-blue-800 mt-1 leading-relaxed">
              Empirical historical records from verified buyer RFQs, executed orders, and authorized government cooperative registries.
            </p>
          </div>

          <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl">
            <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm uppercase">
              <RefreshCw className="h-4 w-4 text-emerald-700" />
              2. CALCULATED METRICS
            </div>
            <p className="text-xs text-emerald-800 mt-1 leading-relaxed">
              Deterministic monthly/quarterly aggregations, rolling moving averages, and period-over-period percentage changes.
            </p>
          </div>

          <div className="bg-purple-50 border border-purple-200 p-4 rounded-xl">
            <div className="flex items-center gap-2 text-purple-900 font-bold text-sm uppercase">
              <Layers className="h-4 w-4 text-purple-700" />
              3. FORECAST PROJECTIONS
            </div>
            <p className="text-xs text-purple-800 mt-1 leading-relaxed">
              Statistical projections (Holt-Winters / WMA) gated by N &ge; 12 threshold with walk-forward validation error reporting.
            </p>
          </div>
        </div>

        {/* Real Observations Table */}
        <div className="bg-white rounded-xl shadow-sm border border-stone-200 overflow-hidden">
          <div className="p-6 border-b border-stone-200 flex justify-between items-center">
            <div>
              <h2 className="text-base font-bold text-stone-900">Historical Demand Observations Registry</h2>
              <p className="text-xs text-stone-500 mt-0.5">Showing latest {observations.length} source-backed demand points.</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-stone-100 text-stone-700 rounded-full">
              {observations.length} Total Records
            </span>
          </div>

          {loading ? (
            <div className="p-8 text-center text-sm text-stone-500">Loading observations...</div>
          ) : observations.length === 0 ? (
            <div className="p-8 text-center text-sm text-stone-500">No demand observations recorded yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-stone-200 text-left text-xs">
                <thead className="bg-stone-50 text-stone-600 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Period</th>
                    <th className="py-3 px-4">State</th>
                    <th className="py-3 px-4">Enquiries / RFQs</th>
                    <th className="py-3 px-4">Orders</th>
                    <th className="py-3 px-4">Unit Volume</th>
                    <th className="py-3 px-4">Signal Tier</th>
                    <th className="py-3 px-4">Quality / Demo</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-200 text-stone-700">
                  {observations.map((obs) => (
                    <tr key={obs.id} className="hover:bg-stone-50 transition">
                      <td className="py-3 px-4 whitespace-nowrap font-medium text-stone-900">
                        {obs.observation_period_start.substring(0, 7)}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">{obs.geography_state}</td>
                      <td className="py-3 px-4 whitespace-nowrap">{obs.total_enquiries}</td>
                      <td className="py-3 px-4 whitespace-nowrap">{obs.fulfilled_orders}</td>
                      <td className="py-3 px-4 whitespace-nowrap font-semibold">{obs.unit_volume.toLocaleString()}</td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 bg-blue-100 text-blue-800 rounded font-mono text-[10px]">
                          {obs.signal_tier}
                        </span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {obs.is_sample_or_demo ? (
                          <span className="px-2 py-0.5 bg-amber-100 text-amber-800 rounded text-[10px] font-semibold">
                            DEMO / SAMPLE
                          </span>
                        ) : (
                          <span className="inline-flex items-center text-emerald-700 text-[11px] font-medium">
                            <CheckCircle2 className="h-3 w-3 mr-1" /> Verified
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
