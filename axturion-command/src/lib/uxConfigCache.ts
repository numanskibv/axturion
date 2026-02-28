import { fetchUXConfig } from "@/lib/api";

export type UXLayout = "default" | "compact" | "dense";
export type UXTheme = "dark" | "light" | "defense";

export type UXModuleConfig = {
    layout?: UXLayout;
    theme?: UXTheme;
    flags?: Record<string, boolean>;
};

export type UXConfigResponse = {
    module: string;
    config: UXModuleConfig;
};

const DEFAULT_TTL_MS = 300_000;

type CacheKey = string;

type CacheEntry = {
    value: UXConfigResponse | null;
    expiresAt: number;
    inFlight: Promise<UXConfigResponse> | null;
};

const cache = new Map<CacheKey, CacheEntry>();

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}

function isUXLayout(value: unknown): value is UXLayout {
    return value === "default" || value === "compact" || value === "dense";
}

function isUXTheme(value: unknown): value is UXTheme {
    return value === "dark" || value === "light" || value === "defense";
}

function normalizeFlags(value: unknown): Record<string, boolean> | undefined {
    if (!isRecord(value)) return undefined;

    const result: Record<string, boolean> = {};
    for (const [key, flagValue] of Object.entries(value)) {
        if (typeof flagValue === "boolean") {
            result[key] = flagValue;
        }
    }

    return Object.keys(result).length > 0 ? result : undefined;
}

function nowMs(): number {
    return Date.now();
}

function requireApiUrl(): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;
    if (!apiUrl) throw new Error("NEXT_PUBLIC_API_URL is not set");
    return apiUrl;
}

function requireClientIdentity(): { orgId: string; userId: string } {
    if (typeof window === "undefined") {
        throw new Error("Client identity requires the browser");
    }

    const orgId = window.localStorage.getItem("org_id")?.trim();
    const userId = window.localStorage.getItem("user_id")?.trim();

    if (!orgId) throw new Error('Missing "org_id" in localStorage');
    if (!userId) throw new Error('Missing "user_id" in localStorage');

    return { orgId, userId };
}

function normalizeModule(module: string): string {
    const trimmed = (module ?? "").trim();
    if (!trimmed) throw new Error("module is required");
    return trimmed;
}

function makeKey(orgId: string, userId: string, module: string): CacheKey {
    return `${orgId}::${userId}::${module}`;
}

export type CachedUXConfigResult = {
    data: UXConfigResponse | null;
    fresh: boolean;
    expiresAt: number | null;
};

export function getCachedUXConfig(
    orgId: string,
    userId: string,
    module: string,
): CachedUXConfigResult {
    const normalized = normalizeModule(module);
    const key = makeKey(orgId, userId, normalized);
    const entry = cache.get(key);
    if (!entry || !entry.value) {
        return { data: null, fresh: false, expiresAt: null };
    }

    const fresh = nowMs() < entry.expiresAt;
    return { data: entry.value, fresh, expiresAt: entry.expiresAt };
}

export function invalidateUXConfig(orgId: string, userId: string, module: string): void {
    const normalized = normalizeModule(module);
    const key = makeKey(orgId, userId, normalized);
    cache.delete(key);
}

export function clearUXConfigCache(): void {
    cache.clear();
}

export async function getUXConfigWithCache(
    module: string,
    options?: { forceRefresh?: boolean; ttlMs?: number },
): Promise<UXConfigResponse> {
    const normalized = normalizeModule(module);
    const { orgId, userId } = requireClientIdentity();
    const apiUrl = requireApiUrl();

    const ttlMs = options?.ttlMs ?? DEFAULT_TTL_MS;
    const key = makeKey(orgId, userId, normalized);
    const entry: CacheEntry = cache.get(key) ?? {
        value: null,
        expiresAt: 0,
        inFlight: null,
    };

    const isFresh = entry.value !== null && nowMs() < entry.expiresAt;

    if (!options?.forceRefresh) {
        if (isFresh) {
            return entry.value as UXConfigResponse;
        }
        if (entry.inFlight) {
            return entry.inFlight;
        }
    }

    const promise = fetchUXConfig(normalized, {
        apiUrl,
        orgId,
        userId,
    })
        .then((result) => {
            const raw: unknown = result;
            const rawModule = isRecord(raw) ? raw["module"] : undefined;
            const rawConfig = isRecord(raw) ? raw["config"] : undefined;

            const normalizedConfig: UXModuleConfig = {};
            if (isRecord(rawConfig)) {
                const layout = rawConfig["layout"];
                const theme = rawConfig["theme"];
                const flags = rawConfig["flags"];

                if (isUXLayout(layout)) normalizedConfig.layout = layout;
                if (isUXTheme(theme)) normalizedConfig.theme = theme;

                const normalizedFlags = normalizeFlags(flags);
                if (normalizedFlags) normalizedConfig.flags = normalizedFlags;
            }

            const normalizedResponse: UXConfigResponse = {
                module: typeof rawModule === "string" ? rawModule : normalized,
                config: normalizedConfig,
            };

            const next: CacheEntry = {
                value: normalizedResponse,
                expiresAt: nowMs() + ttlMs,
                inFlight: null,
            };
            cache.set(key, next);
            return normalizedResponse;
        })
        .catch((err) => {
            // Keep last known good value (if any); only clear inFlight.
            const existing = cache.get(key) ?? entry;
            cache.set(key, { ...existing, inFlight: null });
            throw err;
        });

    cache.set(key, { ...entry, inFlight: promise });
    return promise;
}

/**
 * Manual verification (no test framework configured):
 * - Set `localStorage.org_id` + `localStorage.user_id` to valid UUIDs.
 * - Open DevTools Network tab.
 * - Render two components that call `useUXConfig("applications")` concurrently.
 *   You should see only one `GET /ux/applications` request (dedup).
 * - Reload within 5 minutes: hook should render immediately from cache.
 */
