"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { UXConfigResponse } from "@/lib/api";
import {
    getCachedUXConfig,
    getUXConfigWithCache,
} from "@/lib/uxConfigCache";

export type UseUXConfigResult = {
    config: UXConfigResponse | null;
    loading: boolean;
    error: Error | null;
    refetch: () => Promise<void>;
};

export function useUXConfig(module: string): UseUXConfigResult {
    const normalizedModule = useMemo(() => (module ?? "").trim(), [module]);

    const [config, setConfig] = useState<UXConfigResponse | null>(() => {
        if (typeof window === "undefined") return null;
        const orgId = window.localStorage.getItem("org_id")?.trim();
        const userId = window.localStorage.getItem("user_id")?.trim();
        if (!orgId || !userId) return null;
        if (!normalizedModule) return null;

        const cached = getCachedUXConfig(orgId, userId, normalizedModule);
        return cached.data ?? null;
    });

    const [loading, setLoading] = useState<boolean>(() => {
        if (typeof window === "undefined") return true;
        const orgId = window.localStorage.getItem("org_id")?.trim();
        const userId = window.localStorage.getItem("user_id")?.trim();
        if (!orgId || !userId) return false;
        if (!normalizedModule) return false;

        const cached = getCachedUXConfig(orgId, userId, normalizedModule);
        return !cached.fresh;
    });

    const [error, setError] = useState<Error | null>(null);

    const runFetch = useCallback(
        async (opts?: { forceRefresh?: boolean }) => {
            if (!normalizedModule) {
                setLoading(false);
                setError(new Error("module is required"));
                return;
            }

            setLoading(true);
            setError(null);

            try {
                const response = await getUXConfigWithCache(normalizedModule, {
                    forceRefresh: opts?.forceRefresh,
                });
                setConfig(response);
                setLoading(false);
            } catch (err) {
                // Keep last known good config (if any).
                setLoading(false);
                setError(err instanceof Error ? err : new Error("Unknown error"));
            }
        },
        [normalizedModule],
    );

    useEffect(() => {
        let cancelled = false;

        async function sync() {
            if (typeof window === "undefined") return;
            if (!normalizedModule) {
                setLoading(false);
                setError(new Error("module is required"));
                return;
            }

            const orgId = window.localStorage.getItem("org_id")?.trim();
            const userId = window.localStorage.getItem("user_id")?.trim();
            if (!orgId || !userId) {
                setLoading(false);
                setError(new Error('Missing "org_id"/"user_id" in localStorage'));
                return;
            }

            const cached = getCachedUXConfig(orgId, userId, normalizedModule);
            if (cached.data && !cancelled) {
                setConfig(cached.data);
            }

            // If the cache is fresh, avoid re-fetching and avoid flicker.
            if (cached.fresh) {
                if (!cancelled) setLoading(false);
                return;
            }

            // Cache missing/stale: fetch (deduped) but keep any cached config visible.
            if (cancelled) return;

            setLoading(true);
            setError(null);

            try {
                const response = await getUXConfigWithCache(normalizedModule);
                if (cancelled) return;
                setConfig(response);
                setLoading(false);
            } catch (err) {
                if (cancelled) return;
                setLoading(false);
                setError(err instanceof Error ? err : new Error("Unknown error"));
            }
        }

        void sync();

        return () => {
            cancelled = true;
        };
    }, [normalizedModule]);

    const refetch = useCallback(async () => {
        await runFetch({ forceRefresh: true });
    }, [runFetch]);

    return { config, loading, error, refetch };
}
