"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";

interface ArtisanProfile {
  id: string;
  full_name: string;
  cooperative_name?: string;
  state: string;
  district: string;
  pincode: string;
  address_line?: string;
  primary_craft_id: string;
  years_of_experience?: number;
  monthly_production_capacity?: number;
  pehchan_id?: string;
  verification_status: string;
  created_at: string;
}

interface CraftPassport {
  id: string;
  craft_id: string;
  craft_name?: string;
  passport_uuid: string;
  qr_code_url: string;
  authorized_user_gi_certificate?: string;
  verification_level: string;
  status: string;
  issued_at: string;
  provenance_hash: string;
}

export default function ArtisanProfilePage() {
  const [profile, setProfile] = useState<ArtisanProfile | null>(null);
  const [passports, setPassports] = useState<CraftPassport[]>([]);
  const [loading, setLoading] = useState(true);
  const [docType, setDocType] = useState("GI_AUTHORIZED_USER_CERT");
  const [docUrl, setDocUrl] = useState("");
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const fetchProfileData = async () => {
    setLoading(true);
    const token = localStorage.getItem("access_token");
    if (!token) {
      window.location.href = "/login";
      return;
    }

    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      // Fetch Profile
      const profRes = await fetch("/api/v1/artisans/me", { headers });
      if (profRes.ok) {
        const data = await profRes.json();
        setProfile(data);
      }

      // Fetch Passports
      const passRes = await fetch("/api/v1/passports/my", { headers });
      if (passRes.ok) {
        const pList = await passRes.json();
        setPassports(pList);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileData();
  }, []);

  const handleDocumentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("access_token");
    if (!token) return;

    try {
      const res = await fetch("/api/v1/verifications/submit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          document_type: docType,
          document_url: docUrl
        })
      });
      if (res.ok) {
        setStatusMsg("Document submitted successfully! Under administrator review.");
        setDocUrl("");
        fetchProfileData();
      } else {
        const err = await res.json();
        setStatusMsg(`Submission failed: ${err.detail || "Error"}`);
      }
    } catch (err: any) {
      setStatusMsg(`Submission error: ${err.message}`);
    }
  };

  if (loading) {
    return <div style={{ padding: "40px", textAlign: "center" }}>Loading artisan workspace...</div>;
  }

  return (
    <div style={{ maxWidth: "1000px", margin: "0 auto", padding: "30px 20px" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #e7e5e4", paddingBottom: "20px", marginBottom: "30px" }}>
        <div>
          <h1 style={{ fontSize: "28px", color: "#78350f", margin: "0 0 6px 0" }}>Artisan Dashboard & Digital Passports</h1>
          <p style={{ color: "#78716c", margin: 0 }}>SIH 26090 — Artisan Market Linkage & Provenance Registry</p>
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

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "40px" }}>
        {/* Profile Card */}
        <div style={{ background: "#fff", border: "1px solid #e7e5e4", borderRadius: "12px", padding: "24px" }}>
          <h2 style={{ fontSize: "18px", color: "#44403c", marginTop: 0, marginBottom: "16px", borderBottom: "1px solid #f5f5f4", paddingBottom: "8px" }}>
            Artisan Identity Profile
          </h2>
          {profile ? (
            <div>
              <div style={{ marginBottom: "12px" }}>
                <span style={{ fontSize: "13px", color: "#78716c" }}>Full Name:</span>
                <div style={{ fontSize: "16px", fontWeight: 600, color: "#1c1917" }}>{profile.full_name}</div>
              </div>
              <div style={{ marginBottom: "12px" }}>
                <span style={{ fontSize: "13px", color: "#78716c" }}>Location:</span>
                <div style={{ fontSize: "15px", color: "#1c1917" }}>{profile.district}, {profile.state} (PIN: {profile.pincode})</div>
              </div>
              <div style={{ marginBottom: "12px" }}>
                <span style={{ fontSize: "13px", color: "#78716c" }}>Cooperative / Society:</span>
                <div style={{ fontSize: "15px", color: "#1c1917" }}>{profile.cooperative_name || "Independent Artisan"}</div>
              </div>
              <div style={{ marginBottom: "12px" }}>
                <span style={{ fontSize: "13px", color: "#78716c" }}>Monthly Production Capacity:</span>
                <div style={{ fontSize: "15px", color: "#1c1917" }}>{profile.monthly_production_capacity || "Not specified"} units/month</div>
              </div>
              <div style={{ marginBottom: "12px" }}>
                <span style={{ fontSize: "13px", color: "#78716c" }}>Verification Status:</span>
                <div style={{ marginTop: "4px" }}>
                  <span style={{
                    display: "inline-block",
                    padding: "4px 10px",
                    borderRadius: "12px",
                    fontSize: "12px",
                    fontWeight: 600,
                    background: profile.verification_status.includes("VERIFIED") ? "#dcfce7" : "#fef3c7",
                    color: profile.verification_status.includes("VERIFIED") ? "#15803d" : "#b45309"
                  }}>
                    {profile.verification_status}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <p style={{ color: "#78716c", fontSize: "14px" }}>Profile not initialized yet.</p>
            </div>
          )}
        </div>

        {/* KYC Verification Upload */}
        <div style={{ background: "#fff", border: "1px solid #e7e5e4", borderRadius: "12px", padding: "24px" }}>
          <h2 style={{ fontSize: "18px", color: "#44403c", marginTop: 0, marginBottom: "16px", borderBottom: "1px solid #f5f5f4", paddingBottom: "8px" }}>
            Submit Craft Credentials (KYC)
          </h2>
          <form onSubmit={handleDocumentSubmit}>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
                Document Type
              </label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", background: "#fff" }}
              >
                <option value="GI_AUTHORIZED_USER_CERT">GI Authorized User Certificate</option>
                <option value="PEHCHAN_CARD">Ministry of Textiles Pehchan Card</option>
                <option value="COOPERATIVE_MEMBERSHIP">Handloom Weaver Cooperative Card</option>
                <option value="STATE_CRAFT_AWARD">State / National Merit Certificate</option>
              </select>
            </div>

            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
                Document URL / Digital Certificate Link
              </label>
              <input
                type="url"
                value={docUrl}
                onChange={(e) => setDocUrl(e.target.value)}
                placeholder="https://storage.artisanlinkage.in/docs/cert.pdf"
                required
                style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
              />
            </div>

            <button
              type="submit"
              style={{
                width: "100%",
                padding: "10px",
                background: "#b45309",
                color: "#fff",
                border: "none",
                borderRadius: "6px",
                fontWeight: 600,
                cursor: "pointer"
              }}
            >
              Submit for Admin Verification
            </button>
          </form>
        </div>
      </div>

      {/* Craft Passports Section */}
      <div style={{ background: "#fff", border: "1px solid #e7e5e4", borderRadius: "12px", padding: "24px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div>
            <h2 style={{ fontSize: "20px", color: "#78350f", margin: 0 }}>Issued Digital Craft Passports</h2>
            <p style={{ color: "#78716c", fontSize: "14px", margin: "4px 0 0 0" }}>Tamper-evident provenance credentials with cryptographic QR codes</p>
          </div>
        </div>

        {passports.length === 0 ? (
          <div style={{ textAlign: "center", padding: "40px 20px", color: "#78716c" }}>
            No Craft Passports generated yet.
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "20px" }}>
            {passports.map((p) => (
              <div key={p.id} style={{ border: "1px solid #e7e5e4", borderRadius: "8px", padding: "16px", background: "#fdfbf7" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                  <span style={{ fontWeight: 700, color: "#78350f", fontSize: "15px" }}>{p.passport_uuid}</span>
                  <span style={{
                    fontSize: "11px",
                    fontWeight: 600,
                    padding: "2px 8px",
                    borderRadius: "10px",
                    background: p.status === "VERIFIED" ? "#dcfce7" : "#fef3c7",
                    color: p.status === "VERIFIED" ? "#15803d" : "#b45309"
                  }}>
                    {p.status}
                  </span>
                </div>

                <div style={{ textAlign: "center", margin: "16px 0" }}>
                  {p.qr_code_url && (
                    <img
                      src={p.qr_code_url}
                      alt={`QR Code for ${p.passport_uuid}`}
                      style={{ width: "160px", height: "160px", borderRadius: "8px", border: "1px solid #e7e5e4" }}
                    />
                  )}
                </div>

                <div style={{ fontSize: "13px", color: "#44403c", marginBottom: "6px" }}>
                  <strong>Craft:</strong> {p.craft_name || "Traditional Handloom"}
                </div>
                <div style={{ fontSize: "13px", color: "#44403c", marginBottom: "12px" }}>
                  <strong>Provenance Hash:</strong>
                  <div style={{ fontSize: "11px", fontFamily: "monospace", color: "#78716c", wordBreak: "break-all" }}>
                    {p.provenance_hash.substring(0, 24)}...
                  </div>
                </div>

                <div style={{ marginTop: "12px", borderTop: "1px solid #e7e5e4", paddingTop: "12px", textAlign: "center" }}>
                  <Link
                    href={`/passport/${p.passport_uuid}`}
                    target="_blank"
                    style={{ color: "#b45309", fontSize: "13px", fontWeight: 600, textDecoration: "none" }}
                  >
                    View Public Verification Page &rarr;
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
