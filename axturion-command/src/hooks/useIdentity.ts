"use client";

import { useCallback, useEffect, useState } from "react";

import type { IdentityResponse } from "@/lib/identityApi";
import { clearIdentity, getIdentity } from "@/lib/identityCache";

type UseIdentityResult = {
    identity: IdentityResponse | null;
    loading: boolean;
    error: Error | null;
    refetch: () => Promise<void>;
};

export function useIdentity(): UseIdentityResult {
    const [identity, setIdentity] = useState<IdentityResponse | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<Error | null>(null);

    const runFetch = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const result = await getIdentity();
            setIdentity(result);
            setLoading(false);
        } catch (err) {
            const resolved = err instanceof Error ? err : new Error("Unknown error");
            setLoading(false);
            setError(resolved);
        }
    }, []);

    useEffect(() => {
        void Promise.resolve().then(() => runFetch());
    }, [runFetch]);

    useEffect(() => {
        if (!error) return;
        if (process.env.NODE_ENV === "development") {
            console.error("Failed to load identity", error);
        }
    }, [error]);

    const refetch = useCallback(async () => {
        clearIdentity();
        await runFetch();
    }, [runFetch]);

    return { identity, loading, error, refetch };
}
