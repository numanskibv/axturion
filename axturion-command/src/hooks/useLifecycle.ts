"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import type {
    StageAgingItem,
    StageDurationSummaryItem,
    TimeToCloseStatsResponse,
} from "@/lib/lifecycleApi";
import {
    fetchStageAging,
    fetchStageDurationSummary,
    fetchTimeToClose,
} from "@/lib/lifecycleApi";

type UseLifecycleResult<T> = {
    data: T | null;
    loading: boolean;
    error: Error | null;
    refetch: () => Promise<void>;
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

export function useStageAging(args: { workflowId: string }): UseLifecycleResult<StageAgingItem[]> {
    const normalizedWorkflowId = useMemo(() => (args.workflowId ?? "").trim(), [args.workflowId]);

    const [data, setData] = useState<StageAgingItem[] | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<Error | null>(null);

    const runFetch = useCallback(async (signal?: AbortSignal) => {
        setLoading(true);
        setError(null);
        try {
            const { orgId, userId } = getIdentityFromLocalStorage();
            const apiUrl = getApiUrl();
            const result = await fetchStageAging({ apiUrl, orgId, userId, workflowId: normalizedWorkflowId, signal });
            setData(result);
            setLoading(false);
        } catch (err) {
            setLoading(false);
            setError(err instanceof Error ? err : new Error("Unknown error"));
        }
    }, [normalizedWorkflowId]);

    useEffect(() => {
        const controller = new AbortController();
        void Promise.resolve().then(() => runFetch(controller.signal));
        return () => controller.abort();
    }, [runFetch]);

    const refetch = useCallback(async () => {
        const controller = new AbortController();
        await runFetch(controller.signal);
    }, [runFetch]);

    return { data, loading, error, refetch };
}

export function useTimeToClose(args: { workflowId: string }): UseLifecycleResult<TimeToCloseStatsResponse> {
    const normalizedWorkflowId = useMemo(() => (args.workflowId ?? "").trim(), [args.workflowId]);

    const [data, setData] = useState<TimeToCloseStatsResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<Error | null>(null);

    const runFetch = useCallback(async (signal?: AbortSignal) => {
        setLoading(true);
        setError(null);
        try {
            const { orgId, userId } = getIdentityFromLocalStorage();
            const apiUrl = getApiUrl();
            const result = await fetchTimeToClose({ apiUrl, orgId, userId, workflowId: normalizedWorkflowId, signal });
            setData(result);
            setLoading(false);
        } catch (err) {
            setLoading(false);
            setError(err instanceof Error ? err : new Error("Unknown error"));
        }
    }, [normalizedWorkflowId]);

    useEffect(() => {
        const controller = new AbortController();
        void Promise.resolve().then(() => runFetch(controller.signal));
        return () => controller.abort();
    }, [runFetch]);

    const refetch = useCallback(async () => {
        const controller = new AbortController();
        await runFetch(controller.signal);
    }, [runFetch]);

    return { data, loading, error, refetch };
}

export function useStageDurationSummary(
    workflowId: string | null,
): UseLifecycleResult<StageDurationSummaryItem[]> {
    const normalizedWorkflowId = useMemo(() => (workflowId ?? "").trim(), [workflowId]);

    const [data, setData] = useState<StageDurationSummaryItem[] | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<Error | null>(null);

    const runFetch = useCallback(
        async (signal?: AbortSignal) => {
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
                const result = await fetchStageDurationSummary(normalizedWorkflowId, {
                    apiUrl,
                    orgId,
                    userId,
                    signal,
                });
                setData(result);
                setLoading(false);
            } catch (err) {
                setLoading(false);
                setError(err instanceof Error ? err : new Error("Unknown error"));
            }
        },
        [normalizedWorkflowId],
    );

    useEffect(() => {
        const controller = new AbortController();
        void Promise.resolve().then(() => runFetch(controller.signal));
        return () => controller.abort();
    }, [runFetch]);

    const refetch = useCallback(async () => {
        const controller = new AbortController();
        await runFetch(controller.signal);
    }, [runFetch]);

    return { data, loading, error, refetch };
}
