"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { UXModuleConfig } from "@/lib/api";

export type UXVersionDiffField = {
    from: string | null;
    to: string | null;
};

export type UXVersionDiffFlagChanged = {
    key: string;
    from: boolean;
    to: boolean;
};

export type UXVersionDiff = {
    layout?: UXVersionDiffField;
    theme?: UXVersionDiffField;
    flags_added?: string[];
    flags_removed?: string[];
    flags_changed?: UXVersionDiffFlagChanged[];
};

export type UXConfigVersionItem = {
    version: number;
    audit_log_id: string;
    created_at: string;
    actor_id: string;
    config: UXModuleConfig;
    diff?: UXVersionDiff | null;
};

type UXVersionsErrorKind = "forbidden" | "missing-identity" | "network";

export type UXVersionsError = {
    kind: UXVersionsErrorKind;
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

async function fetchUXVersions(module: string): Promise<UXConfigVersionItem[]> {
    const trimmed = (module ?? "").trim();
    if (!trimmed) throw new Error("module is required");

    const apiUrl = requireApiUrl();
    const { orgId, userId } = readIdentity();
    const url = new URL(`/ux/${encodeURIComponent(trimmed)}/versions`, apiUrl);

    const res = await fetch(url.toString(), {
        method: "GET",
        headers: {
            Accept: "application/json",
            "X-Org-Id": orgId,
            "X-User-Id": userId,
        },
        cache: "no-store",
    });

    if (res.status === 403) {
        const err: UXVersionsError = {
            kind: "forbidden",
            message: "Insufficient permissions",
        };
        throw err;
    }

    if (!res.ok) {
        const body = await res.text().catch(() => "");
        const err: UXVersionsError = {
            kind: "network",
            message: `Failed to fetch versions (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`,
        };
        throw err;
    }

    const data: unknown = await res.json();
    if (!Array.isArray(data)) {
        const err: UXVersionsError = {
            kind: "network",
            message: "Invalid versions response shape",
        };
        throw err;
    }

    return data as UXConfigVersionItem[];
}

export type UseUXVersionsResult = {
    versions: UXConfigVersionItem[];
    loading: boolean;
    error: UXVersionsError | null;
    refetch: () => Promise<void>;
};

export function useUXVersions(module: string): UseUXVersionsResult {
    const normalizedModule = useMemo(() => (module ?? "").trim(), [module]);

    const [versions, setVersions] = useState<UXConfigVersionItem[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<UXVersionsError | null>(null);

    const runFetch = useCallback(async () => {
        if (!normalizedModule) {
            setVersions([]);
            setLoading(false);
            setError({ kind: "network", message: "Missing module" });
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const result = await fetchUXVersions(normalizedModule);
            setVersions(result);
        } catch (e) {
            if (e && typeof e === "object" && "kind" in e && "message" in e) {
                const err = e as UXVersionsError;
                setError(err);
            } else if (e instanceof Error) {
                setError({ kind: "network", message: e.message });
            } else {
                setError({ kind: "network", message: "Unknown error" });
            }
            setVersions([]);
        } finally {
            setLoading(false);
        }
    }, [normalizedModule]);

    useEffect(() => {
        // If identity is missing, show a deterministic error rather than a silent empty state.
        try {
            if (typeof window !== "undefined") {
                readIdentity();
            }
        } catch {
            setVersions([]);
            setLoading(false);
            setError({ kind: "missing-identity", message: "Missing org/user identity" });
            return;
        }

        void runFetch();
    }, [runFetch]);

    const refetch = useCallback(async () => {
        await runFetch();
    }, [runFetch]);

    return { versions, loading, error, refetch };
}
