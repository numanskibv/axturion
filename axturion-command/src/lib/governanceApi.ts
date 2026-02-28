export type PolicyConfigResponse = {
    organization_id: string;
    require_4eyes_on_hire: boolean;
    require_4eyes_on_ux_rollback: boolean;
    stage_aging_sla_days: number;
    candidate_retention_days?: number | null;
    audit_retention_days?: number | null;
    created_at: string;
    updated_at: string;
};

export type FetchPolicyConfigParams = {
    apiUrl: string;
    orgId: string;
    userId: string;
    signal?: AbortSignal;
};

function isRecord(value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === "object";
}

function isFiniteNumber(value: unknown): value is number {
    return typeof value === "number" && Number.isFinite(value);
}

function validatePolicyConfigResponse(value: unknown): PolicyConfigResponse {
    if (!isRecord(value)) throw new Error("Invalid policy response");

    if (typeof value.organization_id !== "string") throw new Error("Invalid organization_id");
    if (typeof value.require_4eyes_on_hire !== "boolean") throw new Error("Invalid require_4eyes_on_hire");
    if (typeof value.require_4eyes_on_ux_rollback !== "boolean") {
        throw new Error("Invalid require_4eyes_on_ux_rollback");
    }
    if (!isFiniteNumber(value.stage_aging_sla_days)) throw new Error("Invalid stage_aging_sla_days");
    if (typeof value.created_at !== "string") throw new Error("Invalid created_at");
    if (typeof value.updated_at !== "string") throw new Error("Invalid updated_at");

    return {
        organization_id: value.organization_id,
        require_4eyes_on_hire: value.require_4eyes_on_hire,
        require_4eyes_on_ux_rollback: value.require_4eyes_on_ux_rollback,
        stage_aging_sla_days: value.stage_aging_sla_days,
        candidate_retention_days: (value.candidate_retention_days ?? null) as number | null,
        audit_retention_days: (value.audit_retention_days ?? null) as number | null,
        created_at: value.created_at,
        updated_at: value.updated_at,
    };
}

export async function fetchPolicyConfig(params: FetchPolicyConfigParams): Promise<PolicyConfigResponse> {
    const apiUrl = params.apiUrl?.trim();
    const orgId = params.orgId?.trim();
    const userId = params.userId?.trim();
    if (!apiUrl) throw new Error("apiUrl is required");
    if (!orgId) throw new Error("orgId is required");
    if (!userId) throw new Error("userId is required");

    const url = new URL("/governance/policy", apiUrl);
    const res = await fetch(url.toString(), {
        method: "GET",
        headers: {
            Accept: "application/json",
            "X-Org-Id": orgId,
            "X-User-Id": userId,
        },
        cache: "no-store",
        signal: params.signal,
    });

    if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(
            `Failed to fetch policy (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`,
        );
    }

    const data: unknown = await res.json();
    return validatePolicyConfigResponse(data);
}
