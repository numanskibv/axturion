export type IdentityResponse = {
    organization_id: string;
    user_id: string;
    role: string;
    scopes: string[];
    language: "en" | "nl" | null;
    default_language: "en" | "nl";
    effective_language: "en" | "nl";
    correlation_id: string;
    ux: Record<string, unknown>;
    features: Record<string, unknown>;
};

type FetchMeParams = {
    apiUrl?: string;
    orgId?: string;
    userId?: string;
    signal?: AbortSignal;
};

function isRecord(value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === "object";
}

function isLocale(value: unknown): value is "en" | "nl" {
    return value === "en" || value === "nl";
}

function validateIdentityResponse(value: unknown): IdentityResponse {
    if (!isRecord(value)) throw new Error("Invalid identity response");

    if (typeof value.organization_id !== "string" || !value.organization_id.trim()) {
        throw new Error("Invalid organization_id");
    }
    if (typeof value.user_id !== "string" || !value.user_id.trim()) {
        throw new Error("Invalid user_id");
    }
    if (!isLocale(value.effective_language)) {
        throw new Error("Invalid effective_language");
    }

    const role = typeof value.role === "string" ? value.role : "";
    const scopes = Array.isArray(value.scopes)
        ? value.scopes.filter((s): s is string => typeof s === "string")
        : [];

    const language = value.language === null ? null : isLocale(value.language) ? value.language : null;
    const defaultLanguage = isLocale(value.default_language) ? value.default_language : "en";

    const correlationId = typeof value.correlation_id === "string" ? value.correlation_id : "";

    const ux = isRecord(value.ux) ? value.ux : {};
    const features = isRecord(value.features) ? value.features : {};

    return {
        organization_id: value.organization_id,
        user_id: value.user_id,
        role,
        scopes,
        language,
        default_language: defaultLanguage,
        effective_language: value.effective_language,
        correlation_id: correlationId,
        ux,
        features,
    };
}

function requireBaseParams(params?: FetchMeParams): { apiUrl: string; orgId: string; userId: string } {
    const apiUrl = params?.apiUrl?.trim() ?? "";
    const orgId = params?.orgId?.trim() ?? "";
    const userId = params?.userId?.trim() ?? "";

    if (!apiUrl) throw new Error("NEXT_PUBLIC_API_URL is required");
    if (!orgId) throw new Error("orgId is required");
    if (!userId) throw new Error("userId is required");

    return { apiUrl, orgId, userId };
}

export async function fetchMe(params?: FetchMeParams): Promise<IdentityResponse> {
    const { apiUrl, orgId, userId } = requireBaseParams(params);

    const url = new URL("/me", apiUrl);
    const res = await fetch(url.toString(), {
        method: "GET",
        headers: {
            Accept: "application/json",
            "X-Org-Id": orgId,
            "X-User-Id": userId,
        },
        cache: "no-store",
        signal: params?.signal,
    });

    if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(
            `Failed to fetch identity (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`,
        );
    }

    const data: unknown = await res.json();
    return validateIdentityResponse(data);
}
