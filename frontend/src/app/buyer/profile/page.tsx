"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";

interface BuyerProfile {
  id: string;
  company_name: string;
  buyer_type: string;
  gstin?: string;
  country: string;
  state?: string;
  typical_order_volume?: string;
  is_verified_buyer: boolean;
  created_at: string;
}

export default function BuyerProfilePage() {
  const [profile, setProfile] = useState<BuyerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [orderVolume, setOrderVolume] = useState("");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const fetchProfile = async () => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      const res = await fetch("/api/v1/buyers/me", {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        setOrderVolume(data.typical_order_volume || "");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, []);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const res = await fetch("/api/v1/buyers/me", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ typical_order_volume: orderVolume })
      });
      if (res.ok) {
        setStatusMsg("Procurement preferences updated successfully!");
        setEditing(false);
        fetchProfile();
      }
    } catch (err: any) {
      setStatusMsg(`Update error: ${err.message}`);
    }
  };

  if (loading) {
    return <div style={{ padding: "40px", textAlign: "center" }}>Loading procurement workspace...</div>;
  }

  return (
    <div style={{ maxWidth: "800px", margin: "0 auto", padding: "30px 20px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #e7e5e4", paddingBottom: "20px", marginBottom: "30px" }}>
        <div>
          <h1 style={{ fontSize: "28px", color: "#78350f", margin: "0 0 6px 0" }}>Buyer Procurement Profile</h1>
          <p style={{ color: "#78716c", margin: 0 }}>SIH 26090 — Verified B2B & Institutional Sourcing</p>
        </div>
        <button
          onClick={() => {
            localStorage.clear();
            window.location.href = "/login";
          }}
          style={{ padding: "8px 16px", borderRadius: "6px", border: "1px solid #d6d3d1", background: "#fff", cursor: "pointer" }}
        >
          Sign Out
        </button>
      </div>

      {statusMsg && (
        <div style={{ padding: "12px 16px", background: "#ecfdf5", border: "1px solid #a7f3d0", color: "#065f46", borderRadius: "8px", marginBottom: "24px" }}>
          {statusMsg}
        </div>
      )}

      {profile ? (
        <div style={{ background: "#fff", border: "1px solid #e7e5e4", borderRadius: "12px", padding: "32px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "24px" }}>
            <div>
              <h2 style={{ fontSize: "22px", color: "#1c1917", margin: "0 0 6px 0" }}>{profile.company_name}</h2>
              <span style={{
                display: "inline-block",
                padding: "4px 10px",
                borderRadius: "12px",
                fontSize: "12px",
                fontWeight: 600,
                background: "#fef3c7",
                color: "#b45309"
              }}>
                {profile.buyer_type.replace(/_/g, " ")}
              </span>
            </div>
            <div>
              <span style={{
                padding: "6px 12px",
                borderRadius: "20px",
                fontSize: "12px",
                fontWeight: 600,
                background: profile.is_verified_buyer ? "#dcfce7" : "#f3f4f6",
                color: profile.is_verified_buyer ? "#15803d" : "#6b7280"
              }}>
                {profile.is_verified_buyer ? "Verified Buyer" : "Standard Buyer"}
              </span>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginBottom: "24px" }}>
            <div>
              <div style={{ fontSize: "13px", color: "#78716c", marginBottom: "4px" }}>GSTIN:</div>
              <div style={{ fontSize: "15px", fontWeight: 500, color: "#1c1917" }}>{profile.gstin || "Not provided"}</div>
            </div>
            <div>
              <div style={{ fontSize: "13px", color: "#78716c", marginBottom: "4px" }}>Region:</div>
              <div style={{ fontSize: "15px", fontWeight: 500, color: "#1c1917" }}>{profile.state ? `${profile.state}, ` : ""}{profile.country}</div>
            </div>
            <div>
              <div style={{ fontSize: "13px", color: "#78716c", marginBottom: "4px" }}>Typical Order Batch:</div>
              <div style={{ fontSize: "15px", fontWeight: 500, color: "#1c1917" }}>{profile.typical_order_volume || "Not specified"}</div>
            </div>
            <div>
              <div style={{ fontSize: "13px", color: "#78716c", marginBottom: "4px" }}>Member Since:</div>
              <div style={{ fontSize: "15px", fontWeight: 500, color: "#1c1917" }}>{new Date(profile.created_at).toLocaleDateString()}</div>
            </div>
          </div>

          {editing ? (
            <form onSubmit={handleUpdate} style={{ borderTop: "1px solid #f5f5f4", paddingTop: "20px" }}>
              <div style={{ marginBottom: "16px" }}>
                <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
                  Update Typical Order Volume (units)
                </label>
                <input
                  type="text"
                  value={orderVolume}
                  onChange={(e) => setOrderVolume(e.target.value)}
                  placeholder="e.g. 100-500 units"
                  style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
                />
              </div>
              <div style={{ display: "flex", gap: "10px" }}>
                <button
                  type="submit"
                  style={{ padding: "10px 20px", background: "#b45309", color: "#fff", border: "none", borderRadius: "6px", fontWeight: 600, cursor: "pointer" }}
                >
                  Save Changes
                </button>
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  style={{ padding: "10px 20px", background: "#f5f5f4", border: "1px solid #d6d3d1", borderRadius: "6px", cursor: "pointer" }}
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div style={{ borderTop: "1px solid #f5f5f4", paddingTop: "20px" }}>
              <button
                type="button"
                onClick={() => setEditing(true)}
                style={{ padding: "8px 16px", background: "#fff", border: "1px solid #d6d3d1", borderRadius: "6px", fontWeight: 500, cursor: "pointer" }}
              >
                Edit Procurement Preferences
              </button>
            </div>
          )}
        </div>
      ) : (
        <div style={{ background: "#fff", border: "1px solid #e7e5e4", borderRadius: "12px", padding: "32px", textAlign: "center" }}>
          <p style={{ color: "#78716c", marginBottom: "20px" }}>No buyer procurement profile found.</p>
        </div>
      )}
    </div>
  );
}
