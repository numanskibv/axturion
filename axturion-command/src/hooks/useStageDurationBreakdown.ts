"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type { StageDurationBreakdownItem } from "@/lib/lifecycleApi";
import { fetchStageDurationBreakdown } from "@/lib/lifecycleApi";

type UseStageDurationBreakdownResult = {
    data: StageDurationBreakdownItem[] | null;
    loading: boolean;
    error: Error | null;
    refetch: () => Promise<void>;
};

export type StageDurationBreakdownWindowParams = {
    from?: string;
    to?: string;
};

function getIdentityFromLocalStorage(): { orgId: string; userId: string } {
    if (typeof window === "undefined") {
        throw new Error("localStorage is not available");
    }

    const orgId = window.localStorage.getItem("org_id")?.trim() ?? "";
    const userId = window.localStorage.getItem("user_id")?.trim() ?? "";
    if (!orgId || !userId) {
        throw new Error('Missing "org_id"/"user_id" in localStorage');
    }

    return { orgId, userId };
}

function getApiUrl(): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim() ?? "";
    if (!apiUrl) throw new Error("NEXT_PUBLIC_API_URL is not set");
    return apiUrl;
}

export function useStageDurationBreakdown(
    workflowId: string | null,
    window?: StageDurationBreakdownWindowParams,
): UseStageDurationBreakdownResult {
    const normalizedWorkflowId = useMemo(() => (workflowId ?? "").trim(), [workflowId]);

    const normalizedWindow = useMemo(() => {
        const from = window?.from?.trim() || undefined;
        const to = window?.to?.trim() || undefined;
        return { from, to };
    }, [window?.from, window?.to]);

    const [data, setData] = useState<StageDurationBreakdownItem[] | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);

    const runFetch = useCallback(async () => {
        if (!normalizedWorkflowId) {
            setLoading(false);
            setError(null);
            setData(null);
            return;
        }

        setLoading(true);
        setError(null);
        try {
            const { orgId, userId } = getIdentityFromLocalStorage();
            const apiUrl = getApiUrl();
            const result = await fetchStageDurationBreakdown(normalizedWorkflowId, {
                apiUrl,
                orgId,
                userId,
                from: normalizedWindow.from,
                to: normalizedWindow.to,
            });
            setData(result);
            setLoading(false);
        } catch (err) {
            setLoading(false);
            setError(err instanceof Error ? err : new Error("Unknown error"));
        }
    }, [normalizedWorkflowId, normalizedWindow.from, normalizedWindow.to]);

    useEffect(() => {
        void Promise.resolve().then(() => runFetch());
    }, [runFetch]);

    const refetch = useCallback(async () => {
        await runFetch();
    }, [runFetch]);

    return { data, loading, error, refetch };
}
