"use client";

import React, { useState } from "react";
import Link from "next/link";

export default function RegisterPage() {
  const [role, setRole] = useState<"artisan" | "buyer">("artisan");
  const [phone, setPhone] = useState("+91");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [language, setLanguage] = useState("en");
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMessage(null);

    try {
      const payload: any = {
        phone_number: phone,
        password,
        role,
        preferred_language: language
      };
      if (email.trim()) {
        payload.email = email.trim();
      }

      const res = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Registration failed");
      }

      setStatusMessage({
        type: "success",
        text: `Account created successfully for ${data.phone_number}! Redirecting to login...`
      });

      setTimeout(() => {
        window.location.href = "/login";
      }, 1500);
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "20px" }}>
      <div style={{ maxWidth: "480px", width: "100%", background: "#fff", border: "1px solid #e7e5e4", borderRadius: "12px", padding: "32px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <h1 style={{ fontSize: "24px", color: "#78350f", margin: "0 0 8px 0" }}>Create New Account</h1>
          <p style={{ color: "#78716c", fontSize: "14px", margin: 0 }}>Join India&apos;s Artisan Market Linkage Platform</p>
        </div>

        {/* Role Toggle */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "20px" }}>
          <button
            type="button"
            onClick={() => setRole("artisan")}
            style={{
              padding: "12px",
              borderRadius: "8px",
              border: role === "artisan" ? "2px solid #b45309" : "1px solid #d6d3d1",
              background: role === "artisan" ? "#fef3c7" : "#fff",
              color: role === "artisan" ? "#78350f" : "#44403c",
              fontWeight: 600,
              cursor: "pointer",
              textAlign: "center"
            }}
          >
            I am an Artisan
          </button>
          <button
            type="button"
            onClick={() => setRole("buyer")}
            style={{
              padding: "12px",
              borderRadius: "8px",
              border: role === "buyer" ? "2px solid #b45309" : "1px solid #d6d3d1",
              background: role === "buyer" ? "#fef3c7" : "#fff",
              color: role === "buyer" ? "#78350f" : "#44403c",
              fontWeight: 600,
              cursor: "pointer",
              textAlign: "center"
            }}
          >
            I am a Buyer
          </button>
        </div>

        {statusMessage && (
          <div style={{
            padding: "12px",
            borderRadius: "6px",
            marginBottom: "16px",
            fontSize: "14px",
            background: statusMessage.type === "success" ? "#ecfdf5" : "#fef2f2",
            color: statusMessage.type === "success" ? "#065f46" : "#991b1b",
            border: `1px solid ${statusMessage.type === "success" ? "#a7f3d0" : "#fecaca"}`
          }}>
            {statusMessage.text}
          </div>
        )}

        <form onSubmit={handleRegister}>
          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
              Mobile Phone Number (E.164 format) *
            </label>
            <input
              type="text"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+919876543210"
              required
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
            />
            <small style={{ color: "#78716c", fontSize: "12px" }}>Include country code prefix (e.g., +91)</small>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
              Email Address {role === "buyer" ? "*" : "(Optional for artisans)"}
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="artisan@example.in"
              required={role === "buyer"}
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
            />
          </div>

          <div style={{ marginBottom: "16px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
              Password (min. 8 characters) *
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              minLength={8}
              required
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
            />
          </div>

          <div style={{ marginBottom: "20px" }}>
            <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
              Preferred Interaction Language
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box", background: "#fff" }}
            >
              <option value="en">English</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="mr">मराठी (Marathi)</option>
              <option value="ta">தமிழ் (Tamil)</option>
              <option value="bn">বাংলা (Bengali)</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px",
              backgroundColor: "#b45309",
              color: "#fff",
              fontWeight: 600,
              border: "none",
              borderRadius: "6px",
              cursor: loading ? "not-allowed" : "pointer"
            }}
          >
            {loading ? "Registering..." : `Register as ${role === "artisan" ? "Artisan" : "Buyer"}`}
          </button>
        </form>

        <div style={{ marginTop: "24px", textAlign: "center", fontSize: "14px", color: "#78716c" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "#b45309", fontWeight: 600, textDecoration: "none" }}>
            Sign In here
          </Link>
        </div>
      </div>
    </div>
  );
}
