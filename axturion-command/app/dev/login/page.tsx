"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function DevLoginPage() {
  const router = useRouter();
  const [orgId, setOrgId] = useState("");
  const [userId, setUserId] = useState("");
  const [error, setError] = useState("");

  if (process.env.NEXT_PUBLIC_DEV_MODE !== "true") {
    return <div className="p-10 text-center">Not available.</div>;
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!orgId || !userId) {
      setError("Both org_id and user_id are required.");
      return;
    }

    localStorage.setItem("org_id", orgId.trim());
    localStorage.setItem("user_id", userId.trim());
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-8">
        <h1 className="text-2xl font-semibold text-slate-100 mb-6 tracking-wide">
          AXTURION DEV ACCESS
        </h1>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm text-slate-400 mb-1">
              Organization ID
            </label>
            <input
              type="text"
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition"
              placeholder="UUID"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1">
              User ID
            </label>
            <input
              type="text"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition"
              placeholder="UUID"
            />
          </div>

          {error && (
            <div className="text-sm text-red-400">{error}</div>
          )}

          <button
            type="submit"
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 rounded-md transition"
          >
            Set Identity
          </button>
        </form>
      </div>
    </div>
  );
}