"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchWorkflows, type WorkflowListItem } from "@/lib/workflowApi";

type UseWorkflowsResult = {
    workflows: WorkflowListItem[];
    loading: boolean;
    error: Error | null;
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

export function useWorkflows(): UseWorkflowsResult {
    const [workflows, setWorkflows] = useState<WorkflowListItem[]>([]);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<Error | null>(null);

    const runFetch = useCallback(async (signal?: AbortSignal) => {
        setLoading(true);
        setError(null);

        try {
            const { orgId, userId } = getIdentityFromLocalStorage();
            const apiUrl = getApiUrl();
            const result = await fetchWorkflows({ apiUrl, orgId, userId, signal });
            setWorkflows(result);
            setLoading(false);
        } catch (err) {
            setWorkflows([]);
            setLoading(false);
            setError(err instanceof Error ? err : new Error("Unknown error"));
        }
    }, []);

    useEffect(() => {
        const controller = new AbortController();
        void Promise.resolve().then(() => runFetch(controller.signal));
        return () => controller.abort();
    }, [runFetch]);

    return { workflows, loading, error };
}
