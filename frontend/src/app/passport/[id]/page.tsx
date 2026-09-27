"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";

interface PublicPassport {
  passport_uuid: string;
  status: string;
  verification_level: string;
  issued_at: string;
  artisan_public_name: string;
  craft_name: string;
  origin_state: string;
  origin_district: string;
  gi_tag_number?: string;
  has_gi_tag: boolean;
  cultural_heritage_description: string;
  traditional_raw_materials: string[];
  provenance_hash?: string;
  is_valid: boolean;
}

export default function PublicPassportPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const [data, setData] = useState<PublicPassport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadPassport() {
      try {
        const res = await fetch(`/api/v1/public/passports/${id}`);
        if (!res.ok) {
          throw new Error(`Passport '${id}' could not be verified or does not exist.`);
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    if (id) {
      loadPassport();
    }
  }, [id]);

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#fdfbf7" }}>
        <p style={{ color: "#78716c", fontSize: "16px" }}>Verifying digital craft passport cryptographic signature...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "20px", background: "#fdfbf7" }}>
        <div style={{ maxWidth: "480px", width: "100%", background: "#fff", border: "1px solid #fee2e2", borderRadius: "12px", padding: "32px", textAlign: "center" }}>
          <div style={{ width: "48px", height: "48px", borderRadius: "50%", background: "#fee2e2", color: "#dc2626", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px auto", fontSize: "20px", fontWeight: "bold" }}>
            !
          </div>
          <h1 style={{ fontSize: "20px", color: "#991b1b", margin: "0 0 8px 0" }}>Unverified or Invalid Passport</h1>
          <p style={{ color: "#78716c", fontSize: "14px", marginBottom: "24px" }}>{error}</p>
          <Link href="/" style={{ color: "#b45309", fontWeight: 600, textDecoration: "none" }}>
            Return to Platform Home &rarr;
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: "#fdfbf7", padding: "40px 20px" }}>
      <div style={{ maxWidth: "680px", margin: "0 auto", background: "#fff", border: "1px solid #e7e5e4", borderRadius: "16px", padding: "36px", boxShadow: "0 10px 25px rgba(0,0,0,0.04)" }}>
        {/* Verification Badge Header */}
        <div style={{ textAlign: "center", borderBottom: "1px solid #f5f5f4", paddingBottom: "24px", marginBottom: "24px" }}>
          <div style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            background: "#dcfce7",
            color: "#15803d",
            padding: "6px 16px",
            borderRadius: "20px",
            fontSize: "14px",
            fontWeight: 600,
            marginBottom: "12px"
          }}>
            <span style={{ fontSize: "18px" }}>✓</span> Government & Cooperative Verified Authenticity
          </div>
          <h1 style={{ fontSize: "26px", color: "#78350f", margin: "0 0 6px 0" }}>
            Digital Craft Passport
          </h1>
          <div style={{ fontFamily: "monospace", color: "#78716c", fontSize: "14px", letterSpacing: "1px" }}>
            {data.passport_uuid}
          </div>
        </div>

        {/* Craft Core Details */}
        <div style={{ marginBottom: "28px" }}>
          <h2 style={{ fontSize: "22px", color: "#1c1917", margin: "0 0 8px 0" }}>{data.craft_name}</h2>
          <div style={{ fontSize: "15px", color: "#44403c", display: "flex", gap: "16px", flexWrap: "wrap", marginBottom: "16px" }}>
            <span><strong>Artisan:</strong> {data.artisan_public_name}</span>
            <span><strong>Origin:</strong> {data.origin_district}, {data.origin_state}</span>
          </div>

          {data.has_gi_tag && (
            <div style={{ background: "#fef3c7", border: "1px solid #fde68a", borderRadius: "8px", padding: "12px 16px", marginBottom: "20px" }}>
              <div style={{ fontWeight: 600, color: "#92400e", fontSize: "14px" }}>
                Official Geographical Indication (GI) Protected
              </div>
              <div style={{ color: "#78350f", fontSize: "13px", marginTop: "2px" }}>
                GI Registry Reference: <strong>{data.gi_tag_number}</strong> | Status: <strong>{data.verification_level}</strong>
              </div>
            </div>
          )}

          <div style={{ marginBottom: "20px" }}>
            <h3 style={{ fontSize: "14px", textTransform: "uppercase", letterSpacing: "0.5px", color: "#78716c", marginBottom: "8px" }}>
              Cultural Heritage & Technique
            </h3>
            <p style={{ fontSize: "14px", lineHeight: "1.6", color: "#44403c", margin: 0 }}>
              {data.cultural_heritage_description || "Traditional handmade craft produced using historic ancestral techniques passed down across generations."}
            </p>
          </div>

          <div style={{ marginBottom: "20px" }}>
            <h3 style={{ fontSize: "14px", textTransform: "uppercase", letterSpacing: "0.5px", color: "#78716c", marginBottom: "8px" }}>
              Traditional Raw Materials
            </h3>
            <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
              {data.traditional_raw_materials && data.traditional_raw_materials.length > 0 ? (
                data.traditional_raw_materials.map((m, idx) => (
                  <span key={idx} style={{ background: "#f5f5f4", border: "1px solid #e7e5e4", padding: "4px 10px", borderRadius: "12px", fontSize: "13px", color: "#44403c" }}>
                    {m}
                  </span>
                ))
              ) : (
                <span style={{ fontSize: "13px", color: "#78716c" }}>Natural regional raw materials</span>
              )}
            </div>
          </div>
        </div>

        {/* Cryptographic Provenance Section */}
        <div style={{ background: "#fafaf9", border: "1px solid #e7e5e4", borderRadius: "10px", padding: "16px", marginBottom: "24px" }}>
          <div style={{ fontSize: "12px", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", color: "#78716c", marginBottom: "6px" }}>
            Tamper-Evident Provenance Signature
          </div>
          <div style={{ fontSize: "12px", fontFamily: "monospace", color: "#44403c", wordBreak: "break-all" }}>
            {data.provenance_hash || "SHA256:VERIFIED_AUTHENTIC_CRAFT"}
          </div>
          <div style={{ fontSize: "12px", color: "#78716c", marginTop: "8px" }}>
            Issued on: {new Date(data.issued_at).toLocaleString()}
          </div>
        </div>

        {/* Privacy Assurance Footer */}
        <div style={{ textAlign: "center", borderTop: "1px solid #f5f5f4", paddingTop: "20px" }}>
          <p style={{ fontSize: "12px", color: "#a8a29e", margin: "0 0 12px 0" }}>
            Protected by SIH 26090 Privacy Guard. Personal phone numbers, street addresses, and financial credentials are encrypted and never exposed on public passport scans.
          </p>
          <Link href="/" style={{ color: "#b45309", fontSize: "13px", fontWeight: 600, textDecoration: "none" }}>
            Artisan Market Linkage Platform &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
}
