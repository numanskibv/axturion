import { fetchMe, type IdentityResponse } from "@/lib/identityApi";

type IdentityCacheState = {
    identity: IdentityResponse | null;
    inFlight: Promise<IdentityResponse> | null;
};

const state: IdentityCacheState = {
    identity: null,
    inFlight: null,
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

export async function getIdentity(): Promise<IdentityResponse> {
    if (state.identity) return state.identity;
    if (state.inFlight) return state.inFlight;

    const { orgId, userId } = getIdentityFromLocalStorage();
    const apiUrl = getApiUrl();

    state.inFlight = (async () => {
        try {
            const identity = await fetchMe({ apiUrl, orgId, userId });
            state.identity = identity;
            return identity;
        } finally {
            state.inFlight = null;
        }
    })();

    return state.inFlight;
}

export function clearIdentity(): void {
    state.identity = null;
    state.inFlight = null;
}
