'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { TrendingUp, AlertTriangle, Calendar, Layers, ArrowUpRight, ArrowDownRight, Minus, ShieldCheck, Info } from 'lucide-react';

interface DemandSummary {
  craft_id?: string;
  craft_name?: string;
  total_observations: number;
  total_unit_volume: number;
  total_monetary_volume_inr: string;
  total_enquiries: number;
  total_fulfilled_orders: number;
  period_start?: string;
  period_end?: string;
  data_sufficiency_state: string;
}

interface DemandTrend {
  craft_name?: string;
  trend_status: string;
  current_period_volume?: number;
  previous_period_volume?: number;
  absolute_change?: number;
  percentage_change?: number;
  rolling_average_3m?: number;
  explanation: string;
}

interface ForecastPoint {
  forecast_month: number;
  forecast_year: number;
  projected_demand_index: number;
  projected_unit_volume?: number;
  uncertainty_lower?: number;
  uncertainty_upper?: number;
  data_sufficiency_status: string;
  explanation_note: string;
}

interface DemandForecast {
  status: string;
  model_name: string;
  model_version: string;
  observation_count: number;
  validation_mape?: number;
  points: ForecastPoint[];
  limitations_notes: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ArtisanDemandPage() {
  const [summary, setSummary] = useState<DemandSummary | null>(null);
  const [trend, setTrend] = useState<DemandTrend | null>(null);
  const [forecast, setForecast] = useState<DemandForecast | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDemandInsights() {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          setError('Please log in to view demand insights.');
          setLoading(false);
          return;
        }

        const headers = { 'Authorization': `Bearer ${token}` };

        // 1. Summary
        const sRes = await fetch(`${API_BASE}/api/v1/demand/summary`, { headers });
        if (sRes.ok) setSummary(await sRes.json());

        // 2. Trends
        const tRes = await fetch(`${API_BASE}/api/v1/demand/trends`, { headers });
        if (tRes.ok) setTrend(await tRes.json());

        // 3. Forecast
        const fRes = await fetch(`${API_BASE}/api/v1/demand/forecasts`, { headers });
        if (fRes.ok) setForecast(await fRes.json());
      } catch (err: any) {
        setError(err.message || 'Failed to load demand intelligence.');
      } finally {
        setLoading(false);
      }
    }
    loadDemandInsights();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-stone-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-amber-600 mx-auto"></div>
          <p className="mt-3 text-stone-600 font-medium">Aggregating authentic demand signals...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-stone-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm border border-stone-200 p-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-6 w-6 text-amber-600" />
                <h1 className="text-2xl font-bold text-stone-900">Craft Demand Intelligence</h1>
              </div>
              <p className="mt-1 text-sm text-stone-600">
                Transparent market signals grounded in real buyer requirements, RFQs, and confirmed procurement orders.
              </p>
            </div>
            <Link
              href="/artisan/products"
              className="px-4 py-2 text-sm font-medium text-stone-700 bg-stone-100 hover:bg-stone-200 rounded-lg transition"
            >
              Back to Catalogue
            </Link>
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 flex-shrink-0" />
            <p className="text-sm">{error}</p>
          </div>
        )}

        {/* AI Honesty & Provenance Notice */}
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-start gap-3">
          <ShieldCheck className="h-5 w-5 text-amber-700 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 leading-relaxed">
            <span className="font-bold">Zero-Fabrication Guarantee:</span> Demand figures represent authentic commercial interactions recorded in verified registries and institutional buyer RFQs. The system refuses to manufacture synthetic trends or conversion forecasts when observations are sparse.
          </div>
        </div>

        {/* Summary Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-5 rounded-xl border border-stone-200 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-wider text-stone-500">Recorded RFQ Demand</div>
            <div className="mt-2 text-2xl font-bold text-stone-900">
              {summary ? summary.total_unit_volume.toLocaleString() : '0'} <span className="text-sm font-normal text-stone-500">units</span>
            </div>
            <div className="mt-1 text-xs text-stone-500">From {summary?.total_enquiries || 0} active institutional enquiries</div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-stone-200 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-wider text-stone-500">Fulfilled Batch Orders</div>
            <div className="mt-2 text-2xl font-bold text-stone-900">
              {summary?.total_fulfilled_orders || 0} <span className="text-sm font-normal text-stone-500">orders</span>
            </div>
            <div className="mt-1 text-xs text-stone-500">Commercial milestone completions</div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-stone-200 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-wider text-stone-500">Empirical Trend</div>
            <div className="mt-2 flex items-center gap-2">
              {trend?.trend_status === 'INCREASING' && (
                <span className="inline-flex items-center text-emerald-700 font-bold text-lg">
                  <ArrowUpRight className="h-5 w-5 mr-1" /> Increasing
                </span>
              )}
              {trend?.trend_status === 'DECREASING' && (
                <span className="inline-flex items-center text-rose-700 font-bold text-lg">
                  <ArrowDownRight className="h-5 w-5 mr-1" /> Decreasing
                </span>
              )}
              {trend?.trend_status === 'STABLE' && (
                <span className="inline-flex items-center text-stone-700 font-bold text-lg">
                  <Minus className="h-5 w-5 mr-1" /> Stable
                </span>
              )}
              {trend?.trend_status === 'INSUFFICIENT_DATA' && (
                <span className="inline-flex items-center text-amber-700 font-semibold text-sm">
                  <AlertTriangle className="h-4 w-4 mr-1" /> Insufficient Data
                </span>
              )}
            </div>
            <div className="mt-1 text-xs text-stone-500">
              {trend?.percentage_change !== null && trend?.percentage_change !== undefined
                ? `${trend.percentage_change > 0 ? '+' : ''}${trend.percentage_change}% vs previous period`
                : 'Requires >= 3 periods'}
            </div>
          </div>

          <div className="bg-white p-5 rounded-xl border border-stone-200 shadow-sm">
            <div className="text-xs font-semibold uppercase tracking-wider text-stone-500">Data Coverage</div>
            <div className="mt-2 text-lg font-bold text-stone-900">
              {summary?.data_sufficiency_state || 'UNKNOWN'}
            </div>
            <div className="mt-1 text-xs text-stone-500">
              {summary?.total_observations || 0} monthly observations recorded
            </div>
          </div>
        </div>

        {/* Directional Trend Explanation Card */}
        {trend && (
          <div className="bg-white p-6 rounded-xl border border-stone-200 shadow-sm space-y-2">
            <h2 className="text-sm font-bold uppercase tracking-wider text-stone-700 flex items-center gap-2">
              <Info className="h-4 w-4 text-stone-500" />
              Trend Analysis Rationale
            </h2>
            <p className="text-sm text-stone-600 leading-relaxed">
              {trend.explanation}
            </p>
          </div>
        )}

        {/* Seasonal Festival & Cultural Calendar Indicators */}
        <div className="bg-white p-6 rounded-xl border border-stone-200 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Calendar className="h-5 w-5 text-amber-600" />
            <h2 className="text-base font-bold text-stone-900">Cultural & Seasonal Demand Cycles</h2>
          </div>
          <p className="text-xs text-stone-600">
            Artisanal procurement historically surges around traditional festival windows and the national wedding season.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
              <div className="text-xs font-bold text-amber-900 uppercase">Diwali & Festive Gifting</div>
              <div className="text-xs text-amber-700 mt-1">Months: October – November</div>
              <p className="text-xs text-stone-600 mt-2">Peak corporate gifting, brass handicrafts, and traditional handloom silk stoles.</p>
            </div>

            <div className="bg-rose-50 border border-rose-200 p-4 rounded-lg">
              <div className="text-xs font-bold text-rose-900 uppercase">Winter Wedding Season</div>
              <div className="text-xs text-rose-700 mt-1">Months: November – February</div>
              <p className="text-xs text-stone-600 mt-2">Intense institutional demand for heirloom Zari brocades, bridal wear, and silver filigree.</p>
            </div>

            <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
              <div className="text-xs font-bold text-blue-900 uppercase">Spring & Harvest Festivals</div>
              <div className="text-xs text-blue-700 mt-1">Months: March – April</div>
              <p className="text-xs text-stone-600 mt-2">Elevated regional interest for cotton handlooms, terracotta, and natural vegetable dyes.</p>
            </div>
          </div>
        </div>

        {/* Classical Forecast Projections */}
        <div className="bg-white p-6 rounded-xl border border-stone-200 shadow-sm space-y-4">
          <div className="flex justify-between items-start">
            <div>
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-indigo-600" />
                <h2 className="text-base font-bold text-stone-900">Quarterly Demand Projections</h2>
              </div>
              <p className="text-xs text-stone-600 mt-1">
                Projected using classical statistical models (Holt-Winters / Weighted Moving Average) with walk-forward validation.
              </p>
            </div>
            {forecast && (
              <span className="text-xs font-mono bg-stone-100 text-stone-700 px-2 py-1 rounded">
                Model: {forecast.model_name} ({forecast.model_version})
              </span>
            )}
          </div>

          {forecast?.status === 'INSUFFICIENT_HISTORY' || forecast?.status === 'INSUFFICIENT_DATA_QUALITY' ? (
            <div className="bg-stone-50 border border-stone-200 rounded-lg p-6 text-center">
              <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-2" />
              <div className="text-sm font-bold text-stone-800">Projections Currently Unavailable</div>
              <p className="text-xs text-stone-600 mt-1 max-w-md mx-auto">
                {forecast.limitations_notes}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
              {forecast?.points.map((pt, idx) => (
                <div key={idx} className="bg-stone-50 border border-stone-200 p-4 rounded-lg">
                  <div className="text-xs font-semibold text-stone-500">Period: {pt.forecast_year} - Month {pt.forecast_month}</div>
                  <div className="text-xl font-bold text-indigo-900 mt-2">
                    Index: {pt.projected_demand_index}
                  </div>
                  {pt.projected_unit_volume !== null && pt.projected_unit_volume !== undefined && (
                    <div className="text-xs text-stone-700 mt-1">
                      Est. Volume: <span className="font-semibold">{pt.projected_unit_volume}</span> units
                    </div>
                  )}
                  {pt.uncertainty_lower !== null && pt.uncertainty_upper !== null && (
                    <div className="text-[11px] text-stone-500 mt-1">
                      Confidence Band: [{pt.uncertainty_lower} – {pt.uncertainty_upper}]
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {forecast?.limitations_notes && forecast.status !== 'INSUFFICIENT_HISTORY' && (
            <div className="text-xs text-stone-500 border-t border-stone-100 pt-3">
              <span className="font-semibold">Methodology Note:</span> {forecast.limitations_notes}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
