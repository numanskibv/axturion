export type StageAgingItem = {
    application_id: string;
    workflow_id: string;
    current_stage: string;
    age_seconds: number;
};

export type StageDurationSummaryItem = {
    stage: string;
    count: number;
    avg_duration_seconds: number;
    median_duration_seconds: number;
    p90_duration_seconds: number;
};

export type TimeToCloseResult = "hired" | "rejected";

export type TimeToCloseStatsResponse = {
    count: number;
    avg_seconds: number;
    median_seconds: number;
    p90_seconds: number;
    min_seconds: number;
    max_seconds: number;
};

type BaseFetchParams = {
    apiUrl?: string;
    orgId?: string;
    userId?: string;
    signal?: AbortSignal;
};

export type FetchStageAgingParams = BaseFetchParams & {
    workflowId?: string;
    limit?: number;
    offset?: number;
};

export type FetchTimeToCloseParams = BaseFetchParams & {
    workflowId?: string;
    result?: TimeToCloseResult;
};

function isRecord(value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === "object";
}

function isFiniteNumber(value: unknown): value is number {
    return typeof value === "number" && Number.isFinite(value);
}

function validateStageAgingItem(value: unknown): StageAgingItem {
    if (!isRecord(value)) throw new Error("Invalid stage aging item");
    if (typeof value.application_id !== "string") throw new Error("Invalid application_id");
    if (typeof value.workflow_id !== "string") throw new Error("Invalid workflow_id");
    if (typeof value.current_stage !== "string") throw new Error("Invalid current_stage");
    if (!isFiniteNumber(value.age_seconds)) throw new Error("Invalid age_seconds");

    return {
        application_id: value.application_id,
        workflow_id: value.workflow_id,
        current_stage: value.current_stage,
        age_seconds: value.age_seconds,
    };
}

function validateStageDurationSummaryItem(value: unknown): StageDurationSummaryItem {
    if (!isRecord(value)) throw new Error("Invalid stage duration summary item");
    if (typeof value.stage !== "string") throw new Error("Invalid stage");
    if (!isFiniteNumber(value.count)) throw new Error("Invalid count");
    if (!isFiniteNumber(value.avg_duration_seconds)) throw new Error("Invalid avg_duration_seconds");
    if (!isFiniteNumber(value.median_duration_seconds)) {
        throw new Error("Invalid median_duration_seconds");
    }
    if (!isFiniteNumber(value.p90_duration_seconds)) throw new Error("Invalid p90_duration_seconds");

    return {
        stage: value.stage,
        count: value.count,
        avg_duration_seconds: value.avg_duration_seconds,
        median_duration_seconds: value.median_duration_seconds,
        p90_duration_seconds: value.p90_duration_seconds,
    };
}

function validateTimeToCloseStatsResponse(value: unknown): TimeToCloseStatsResponse {
    if (!isRecord(value)) throw new Error("Invalid time-to-close response");

    const count = value.count;
    const avg_seconds = value.avg_seconds;
    const median_seconds = value.median_seconds;
    const p90_seconds = value.p90_seconds;
    const min_seconds = value.min_seconds;
    const max_seconds = value.max_seconds;

    if (!isFiniteNumber(count)) throw new Error("Invalid count");
    if (!isFiniteNumber(avg_seconds)) throw new Error("Invalid avg_seconds");
    if (!isFiniteNumber(median_seconds)) throw new Error("Invalid median_seconds");
    if (!isFiniteNumber(p90_seconds)) throw new Error("Invalid p90_seconds");
    if (!isFiniteNumber(min_seconds)) throw new Error("Invalid min_seconds");
    if (!isFiniteNumber(max_seconds)) throw new Error("Invalid max_seconds");

    return {
        count,
        avg_seconds,
        median_seconds,
        p90_seconds,
        min_seconds,
        max_seconds,
    };
}

async function fetchJson(url: string, init: RequestInit): Promise<unknown> {
    const res = await fetch(url, init);
    if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(
            `Request failed (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`,
        );
    }
    return res.json() as Promise<unknown>;
}

function requireBaseParams(params?: BaseFetchParams): { apiUrl: string; orgId: string; userId: string } {
    const apiUrl = params?.apiUrl?.trim() ?? "";
    const orgId = params?.orgId?.trim() ?? "";
    const userId = params?.userId?.trim() ?? "";

    if (!apiUrl) throw new Error("NEXT_PUBLIC_API_URL is required");
    if (!orgId) throw new Error('Missing "org_id" in localStorage');
    if (!userId) throw new Error('Missing "user_id" in localStorage');

    return { apiUrl, orgId, userId };
}

export async function fetchStageAging(params?: FetchStageAgingParams): Promise<StageAgingItem[]> {
    const { apiUrl, orgId, userId } = requireBaseParams(params);

    const url = new URL("/reporting/stage-aging", apiUrl);
    if (params?.workflowId) url.searchParams.set("workflow_id", params.workflowId);
    if (typeof params?.limit === "number") url.searchParams.set("limit", String(params.limit));
    if (typeof params?.offset === "number") url.searchParams.set("offset", String(params.offset));

    const data = await fetchJson(url.toString(), {
        method: "GET",
        headers: {
            Accept: "application/json",
            "X-Org-Id": orgId,
            "X-User-Id": userId,
        },
        cache: "no-store",
        signal: params?.signal,
    });

    if (!Array.isArray(data)) throw new Error("Invalid stage aging response");
    return data.map(validateStageAgingItem);
}

export async function fetchTimeToClose(params?: FetchTimeToCloseParams): Promise<TimeToCloseStatsResponse> {
    const { apiUrl, orgId, userId } = requireBaseParams(params);

    const url = new URL("/reporting/time-to-close", apiUrl);
    if (params?.workflowId) url.searchParams.set("workflow_id", params.workflowId);
    if (params?.result) url.searchParams.set("result", params.result);

    const data = await fetchJson(url.toString(), {
        method: "GET",
        headers: {
            Accept: "application/json",
            "X-Org-Id": orgId,
            "X-User-Id": userId,
        },
        cache: "no-store",
        signal: params?.signal,
    });

    return validateTimeToCloseStatsResponse(data);
}

export async function fetchStageDurationSummary(
    workflowId: string,
    params?: BaseFetchParams,
): Promise<StageDurationSummaryItem[]> {
    const trimmedWorkflowId = (workflowId ?? "").trim();
    if (!trimmedWorkflowId) throw new Error("workflowId is required");

    const { apiUrl, orgId, userId } = requireBaseParams(params);
    const url = new URL("/reporting/stage-duration-summary", apiUrl);
    url.searchParams.set("workflow_id", trimmedWorkflowId);

    const data = await fetchJson(url.toString(), {
        method: "GET",
        headers: {
            Accept: "application/json",
            "X-Org-Id": orgId,
            "X-User-Id": userId,
        },
        cache: "no-store",
        signal: params?.signal,
    });

    if (!Array.isArray(data)) throw new Error("Invalid stage duration summary response");
    return data.map(validateStageDurationSummaryItem);
}
