"use client";

import { useCallback, useMemo, useState } from "react";

import type { UXConfigResponse } from "@/lib/api";

type UXRollbackErrorKind = "forbidden" | "missing-identity" | "network" | "not-found";

export type UXRollbackError = {
    kind: UXRollbackErrorKind;
    message: string;
};

function requireApiUrl(): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) throw new Error("NEXT_PUBLIC_API_URL is not set");
    return apiUrl;
}

function readIdentity(): { orgId: string; userId: string } {
    if (typeof window === "undefined") {
        throw new Error("Client identity requires the browser");
    }

    const orgId = window.localStorage.getItem("org_id")?.trim();
    const userId = window.localStorage.getItem("user_id")?.trim();

    if (!orgId || !userId) {
        throw new Error('Missing "org_id"/"user_id" in localStorage');
    }

    return { orgId, userId };
}

async function postRollback(module: string, version: number): Promise<UXConfigResponse> {
    const trimmed = (module ?? "").trim();
    if (!trimmed) throw new Error("module is required");
    if (!Number.isInteger(version) || version < 1) throw new Error("version must be >= 1");

    const apiUrl = requireApiUrl();
    const { orgId, userId } = readIdentity();
    const url = new URL(`/ux/${encodeURIComponent(trimmed)}/rollback`, apiUrl);

    const res = await fetch(url.toString(), {
        method: "POST",
        headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-Org-Id": orgId,
            "X-User-Id": userId,
        },
        body: JSON.stringify({ version }),
        cache: "no-store",
    });

    if (res.status === 403) {
        const err: UXRollbackError = { kind: "forbidden", message: "Insufficient permissions" };
        throw err;
    }

    if (res.status === 404) {
        const err: UXRollbackError = { kind: "not-found", message: "Version not found" };
        throw err;
    }

    if (!res.ok) {
        const bodyText = await res.text().catch(() => "");
        const err: UXRollbackError = {
            kind: "network",
            message: `Failed to rollback (${res.status} ${res.statusText})${bodyText ? `: ${bodyText}` : ""}`,
        };
        throw err;
    }

    const data: unknown = await res.json();
    return data as UXConfigResponse;
}

export type UseUXRollbackResult = {
    rollback: (version: number) => Promise<UXConfigResponse>;
    loading: boolean;
    error: UXRollbackError | null;
};

export function useUXRollback(module: string): UseUXRollbackResult {
    const normalizedModule = useMemo(() => (module ?? "").trim(), [module]);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<UXRollbackError | null>(null);

    const rollback = useCallback(
        async (version: number) => {
            if (!normalizedModule) {
                const err: UXRollbackError = { kind: "network", message: "Missing module" };
                setError(err);
                throw err;
            }

            // Surface identity issues as a clear UI state.
            try {
                if (typeof window !== "undefined") readIdentity();
            } catch {
                const err: UXRollbackError = {
                    kind: "missing-identity",
                    message: "Missing org/user identity",
                };
                setError(err);
                throw err;
            }

            setLoading(true);
            setError(null);

            try {
                return await postRollback(normalizedModule, version);
            } catch (e) {
                if (e && typeof e === "object" && "kind" in e && "message" in e) {
                    const err = e as UXRollbackError;
                    setError(err);
                    throw err;
                }

                const err: UXRollbackError = {
                    kind: "network",
                    message: e instanceof Error ? e.message : "Unknown error",
                };
                setError(err);
                throw err;
            } finally {
                setLoading(false);
            }
        },
        [normalizedModule],
    );

    return { rollback, loading, error };
}
