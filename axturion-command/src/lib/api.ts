import type { UXConfigResponse } from "@/lib/uxConfigCache";

export type { UXModuleConfig, UXConfigResponse } from "@/lib/uxConfigCache";

export type FetchUXConfigParams = {
    apiUrl: string;
    orgId: string;
    userId: string;
    signal?: AbortSignal;
};

export async function fetchUXConfig(
    module: string,
    params: FetchUXConfigParams,
): Promise<UXConfigResponse> {
    const trimmed = (module ?? "").trim();
    if (!trimmed) {
        throw new Error("module is required");
    }

    if (!params.apiUrl) throw new Error("apiUrl is required");
    if (!params.orgId) throw new Error("orgId is required");
    if (!params.userId) throw new Error("userId is required");

    const url = new URL(`/ux/${encodeURIComponent(trimmed)}`, params.apiUrl);

    const res = await fetch(url.toString(), {
        method: "GET",
        headers: {
            Accept: "application/json",
            "X-Org-Id": params.orgId,
            "X-User-Id": params.userId,
        },
        cache: "no-store",
        signal: params.signal,
    });

    if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(
            `Failed to fetch UX config (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`,
        );
    }

    const data: unknown = await res.json();

    // Minimal runtime validation to keep this production-safe.
    if (!data || typeof data !== "object" || !("module" in data) || !("config" in data)) {
        throw new Error("Invalid UX config response shape");
    }

    return data as UXConfigResponse;
}
