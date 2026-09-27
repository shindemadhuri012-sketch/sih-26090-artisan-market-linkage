"use client";

import React, { useState } from "react";
import Link from "next/link";

export default function LoginPage() {
  const [authMode, setAuthMode] = useState<"password" | "otp">("password");
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [phone, setPhone] = useState("+91");
  const [otpCode, setOtpCode] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [devOtpHint, setDevOtpHint] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMessage(null);
    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ login_identifier: identifier, password })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Authentication failed");
      }
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("user_role", data.role);
      setStatusMessage({ type: "success", text: `Authenticated successfully as ${data.role}. Redirecting...` });
      setTimeout(() => {
        window.location.href = data.role === "artisan" ? "/artisan/profile" : "/buyer/profile";
      }, 1000);
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleRequestOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMessage(null);
    try {
      const res = await fetch("/api/v1/auth/otp/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phone })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to send OTP");
      }
      setOtpSent(true);
      if (data.dev_otp_code) {
        setDevOtpHint(data.dev_otp_code);
      }
      setStatusMessage({ type: "success", text: "OTP sent to your mobile phone. Valid for 5 minutes." });
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatusMessage(null);
    try {
      const res = await fetch("/api/v1/auth/otp/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phone, otp_code: otpCode })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "OTP verification failed");
      }
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("refresh_token", data.refresh_token);
      localStorage.setItem("user_role", data.role);
      setStatusMessage({ type: "success", text: "Phone verified! Entering platform..." });
      setTimeout(() => {
        window.location.href = "/artisan/profile";
      }, 1000);
    } catch (err: any) {
      setStatusMessage({ type: "error", text: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "20px" }}>
      <div style={{ maxWidth: "440px", width: "100%", background: "#fff", border: "1px solid #e7e5e4", borderRadius: "12px", padding: "32px", boxShadow: "0 4px 12px rgba(0,0,0,0.05)" }}>
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <h1 style={{ fontSize: "24px", color: "#78350f", margin: "0 0 8px 0" }}>Sign In to Artisan Linkage</h1>
          <p style={{ color: "#78716c", fontSize: "14px", margin: 0 }}>Smart India Hackathon 2026 | Verified Identity</p>
        </div>

        {/* Tab Selector */}
        <div style={{ display: "flex", borderBottom: "1px solid #e7e5e4", marginBottom: "24px" }}>
          <button
            type="button"
            onClick={() => { setAuthMode("password"); setStatusMessage(null); }}
            style={{
              flex: 1,
              padding: "10px",
              background: "none",
              border: "none",
              borderBottom: authMode === "password" ? "2px solid #b45309" : "none",
              color: authMode === "password" ? "#b45309" : "#78716c",
              fontWeight: authMode === "password" ? 600 : 400,
              cursor: "pointer"
            }}
          >
            Password Login
          </button>
          <button
            type="button"
            onClick={() => { setAuthMode("otp"); setStatusMessage(null); }}
            style={{
              flex: 1,
              padding: "10px",
              background: "none",
              border: "none",
              borderBottom: authMode === "otp" ? "2px solid #b45309" : "none",
              color: authMode === "otp" ? "#b45309" : "#78716c",
              fontWeight: authMode === "otp" ? 600 : 400,
              cursor: "pointer"
            }}
          >
            OTP / Passwordless
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

        {authMode === "password" ? (
          <form onSubmit={handlePasswordLogin}>
            <div style={{ marginBottom: "16px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
                Phone Number or Email
              </label>
              <input
                type="text"
                placeholder="+919876543210 or buyer@example.in"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                required
                style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
              />
            </div>

            <div style={{ marginBottom: "20px" }}>
              <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
                Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
              />
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
              {loading ? "Authenticating..." : "Sign In with Password"}
            </button>
          </form>
        ) : (
          <div>
            {!otpSent ? (
              <form onSubmit={handleRequestOtp}>
                <div style={{ marginBottom: "20px" }}>
                  <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
                    Artisan Mobile Number (E.164)
                  </label>
                  <input
                    type="text"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+919876543210"
                    required
                    style={{ width: "100%", padding: "10px", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
                  />
                  <small style={{ color: "#78716c", fontSize: "12px" }}>Low-bandwidth SMS OTP supported across India</small>
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
                  {loading ? "Sending OTP..." : "Send Verification Code"}
                </button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOtp}>
                {devOtpHint && (
                  <div style={{ padding: "8px", background: "#fef3c7", borderRadius: "4px", marginBottom: "12px", fontSize: "12px", color: "#92400e" }}>
                    Development Hint: Enter OTP <strong>{devOtpHint}</strong>
                  </div>
                )}
                <div style={{ marginBottom: "20px" }}>
                  <label style={{ display: "block", fontSize: "14px", fontWeight: 500, color: "#44403c", marginBottom: "6px" }}>
                    Enter 6-Digit OTP
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    required
                    style={{ width: "100%", padding: "10px", fontSize: "18px", letterSpacing: "4px", textAlign: "center", borderRadius: "6px", border: "1px solid #d6d3d1", boxSizing: "border-box" }}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    width: "100%",
                    padding: "12px",
                    backgroundColor: "#059669",
                    color: "#fff",
                    fontWeight: 600,
                    border: "none",
                    borderRadius: "6px",
                    cursor: loading ? "not-allowed" : "pointer",
                    marginBottom: "10px"
                  }}
                >
                  {loading ? "Verifying..." : "Verify & Sign In"}
                </button>

                <button
                  type="button"
                  onClick={() => setOtpSent(false)}
                  style={{ width: "100%", background: "none", border: "none", color: "#78716c", fontSize: "13px", cursor: "pointer" }}
                >
                  Change phone number
                </button>
              </form>
            )}
          </div>
        )}

        <div style={{ marginTop: "24px", textAlign: "center", fontSize: "14px", color: "#78716c" }}>
          Don&apos;t have an account?{" "}
          <Link href="/register" style={{ color: "#b45309", fontWeight: 600, textDecoration: "none" }}>
            Register here
          </Link>
        </div>
      </div>
    </div>
  );
}
