export type WorkflowListItem = {
    id: string;
    name: string;
    active: boolean;
};

type BaseFetchParams = {
    apiUrl?: string;
    orgId?: string;
    userId?: string;
    signal?: AbortSignal;
};

function isRecord(value: unknown): value is Record<string, unknown> {
    return value !== null && typeof value === "object";
}

function validateWorkflowListItem(value: unknown): WorkflowListItem {
    if (!isRecord(value)) throw new Error("Invalid workflow list item");

    const id = value.id;
    const name = value.name;
    const active = value.active;

    if (typeof id !== "string" || !id.trim()) throw new Error("Invalid workflow id");
    if (typeof name !== "string") throw new Error("Invalid workflow name");
    if (typeof active !== "boolean") throw new Error("Invalid workflow active");

    return { id, name, active };
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

export async function fetchWorkflows(params?: BaseFetchParams): Promise<WorkflowListItem[]> {
    const { apiUrl, orgId, userId } = requireBaseParams(params);

    const url = new URL("/workflows", apiUrl);
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
            `Failed to fetch workflows (${res.status} ${res.statusText})${body ? `: ${body}` : ""}`,
        );
    }

    const data: unknown = await res.json();
    if (!Array.isArray(data)) throw new Error("Invalid workflows response");
    return data.map(validateWorkflowListItem);
}
