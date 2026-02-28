"use client";

import { useCallback, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { useUXRollback } from "@/hooks/useUXRollback";
import { useUXVersions } from "@/hooks/useUXVersions";
import { invalidateUXConfig } from "@/lib/uxConfigCache";

type Props = {
    module: string;
};

function formatDateTime(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

function flagsPreview(flags: Record<string, boolean> | undefined): string {
    if (!flags || Object.keys(flags).length === 0) return "";
    const json = JSON.stringify(flags);
    return json.length > 80 ? `${json.slice(0, 77)}...` : json;
}

export function UXVersionHistory({ module }: Props) {
    const normalizedModule = useMemo(() => (module ?? "").trim(), [module]);
    const { versions, loading, error, refetch } = useUXVersions(normalizedModule);
    const { rollback, loading: rollbackLoading, error: rollbackError } = useUXRollback(
        normalizedModule,
    );

    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [expandedById, setExpandedById] = useState<Record<string, boolean>>({});

    const doRollback = useCallback(
        async (version: number) => {
            const ok = window.confirm(
                `Rollback UX config for "${normalizedModule}" to version ${version}?`,
            );
            if (!ok) return;

            await rollback(version);

            // Hard refresh any cached UXConfig for this module so higher-level
            // consumers (e.g. layouts using `useUXConfig`) will re-fetch.
            const orgId = window.localStorage.getItem("org_id")?.trim();
            const userId = window.localStorage.getItem("user_id")?.trim();
            if (orgId && userId) {
                invalidateUXConfig(orgId, userId, normalizedModule);
            }
            window.dispatchEvent(
                new CustomEvent("uxconfig:invalidate", {
                    detail: { module: normalizedModule },
                }),
            );

            await refetch();
            setSuccessMessage(`Rolled back to version ${version}.`);
            window.setTimeout(() => setSuccessMessage(null), 2500);
        },
        [normalizedModule, rollback, refetch],
    );

    const showForbidden = error?.kind === "forbidden" || rollbackError?.kind === "forbidden";

    const toggleExpanded = useCallback((id: string) => {
        setExpandedById((prev) => ({ ...prev, [id]: !prev[id] }));
    }, []);

    const renderDiffSummary = useCallback(
        (diff: unknown) => {
            if (!diff || typeof diff !== "object") return "—";

            const d = diff as {
                layout?: { from: string | null; to: string | null };
                theme?: { from: string | null; to: string | null };
                flags_added?: string[];
                flags_removed?: string[];
                flags_changed?: Array<{ key: string; from: boolean; to: boolean }>;
            };

            const lines: ReactNode[] = [];
            if (d.layout) {
                lines.push(
                    <div key="layout" className="text-xs text-slate-700 dark:text-slate-300">
                        <span className="font-mono">layout</span>: {d.layout.from ?? "—"} → {d.layout.to ?? "—"}
                    </div>,
                );
            }
            if (d.theme) {
                lines.push(
                    <div key="theme" className="text-xs text-slate-700 dark:text-slate-300">
                        <span className="font-mono">theme</span>: {d.theme.from ?? "—"} → {d.theme.to ?? "—"}
                    </div>,
                );
            }

            const addedCount = Array.isArray(d.flags_added) ? d.flags_added.length : 0;
            const removedCount = Array.isArray(d.flags_removed) ? d.flags_removed.length : 0;
            const changedCount = Array.isArray(d.flags_changed) ? d.flags_changed.length : 0;
            const hasFlagsDelta = addedCount + removedCount + changedCount > 0;
            if (hasFlagsDelta) {
                lines.push(
                    <div key="flags" className="text-xs text-slate-700 dark:text-slate-300">
                        <span className="font-mono">flags</span>: +{addedCount}, -{removedCount}, ~{changedCount}
                    </div>,
                );
            }

            return lines.length > 0 ? (
                <div className="flex flex-col gap-1">{lines}</div>
            ) : (
                "—"
            );
        },
        [],
    );

    const renderDiffDetails = useCallback((diff: unknown) => {
        if (!diff || typeof diff !== "object") return null;

        const d = diff as {
            flags_added?: string[];
            flags_removed?: string[];
            flags_changed?: Array<{ key: string; from: boolean; to: boolean }>;
        };

        const added = Array.isArray(d.flags_added) ? d.flags_added : [];
        const removed = Array.isArray(d.flags_removed) ? d.flags_removed : [];
        const changed = Array.isArray(d.flags_changed) ? d.flags_changed : [];

        if (added.length === 0 && removed.length === 0 && changed.length === 0) return null;

        return (
            <div className="mt-2 rounded border border-slate-200 bg-slate-50 px-2 py-2 text-xs text-slate-700 dark:border-slate-800 dark:bg-slate-900/40 dark:text-slate-200">
                {added.length > 0 ? (
                    <div>
                        <span className="font-medium">Added:</span>{" "}
                        <span className="font-mono">{added.join(", ")}</span>
                    </div>
                ) : null}
                {removed.length > 0 ? (
                    <div className={added.length > 0 ? "mt-1" : ""}>
                        <span className="font-medium">Removed:</span>{" "}
                        <span className="font-mono">{removed.join(", ")}</span>
                    </div>
                ) : null}
                {changed.length > 0 ? (
                    <div className={added.length > 0 || removed.length > 0 ? "mt-1" : ""}>
                        <span className="font-medium">Changed:</span>
                        <div className="mt-1 space-y-0.5 font-mono">
                            {changed.map((c) => (
                                <div key={c.key}>
                                    {c.key}: {String(c.from)} → {String(c.to)}
                                </div>
                            ))}
                        </div>
                    </div>
                ) : null}
            </div>
        );
    }, []);

    return (
        <div className="p-6">
            <div className="mb-4">
                <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                    UX Version History
                </h1>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
                    Module: <span className="font-mono">{normalizedModule || "(missing)"}</span>
                </p>
            </div>

            {successMessage ? (
                <div className="mb-4 rounded border border-emerald-300 bg-emerald-50 px-3 py-2 text-sm text-emerald-900 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-100">
                    {successMessage}
                </div>
            ) : null}

            {showForbidden ? (
                <div className="mb-4 rounded border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100">
                    Insufficient permissions
                </div>
            ) : null}

            {error && error.kind !== "forbidden" ? (
                <div className="mb-4 rounded border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-900 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-100">
                    {error.message}
                </div>
            ) : null}

            {rollbackError && rollbackError.kind !== "forbidden" ? (
                <div className="mb-4 rounded border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-900 dark:border-rose-700 dark:bg-rose-950/40 dark:text-rose-100">
                    {rollbackError.message}
                </div>
            ) : null}

            <div className="mb-3 flex items-center justify-between">
                <div className="text-sm text-slate-600 dark:text-slate-300">
                    {loading ? "Loading versions…" : `${versions.length} version(s)`}
                </div>
                <button
                    type="button"
                    onClick={() => void refetch()}
                    className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
                    disabled={loading}
                >
                    Refresh
                </button>
            </div>

            <div className="overflow-x-auto rounded border border-slate-200 dark:border-slate-800">
                <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-800">
                    <thead className="bg-slate-50 dark:bg-slate-900">
                        <tr className="text-left text-slate-700 dark:text-slate-200">
                            <th className="px-3 py-2 font-medium">Version</th>
                            <th className="px-3 py-2 font-medium">Updated At</th>
                            <th className="px-3 py-2 font-medium">Actor ID</th>
                            <th className="px-3 py-2 font-medium">Layout</th>
                            <th className="px-3 py-2 font-medium">Theme</th>
                            <th className="px-3 py-2 font-medium">Flags</th>
                            <th className="px-3 py-2 font-medium">Diff</th>
                            <th className="px-3 py-2 font-medium">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white dark:divide-slate-800 dark:bg-slate-950">
                        {versions.map((v) => {
                            const layout = v.config.layout ?? "";
                            const theme = v.config.theme ?? "";
                            const flags = flagsPreview(v.config.flags);
                            const expanded = expandedById[v.audit_log_id] === true;
                            const hasDiff = v.diff !== null && v.diff !== undefined;

                            return (
                                <tr key={v.audit_log_id} className="text-slate-900 dark:text-slate-100">
                                    <td className="px-3 py-2 font-mono">{v.version}</td>
                                    <td className="px-3 py-2 whitespace-nowrap text-slate-700 dark:text-slate-300">
                                        {formatDateTime(v.created_at)}
                                    </td>
                                    <td className="px-3 py-2 font-mono text-slate-700 dark:text-slate-300">
                                        {v.actor_id || "—"}
                                    </td>
                                    <td className="px-3 py-2">{layout || "—"}</td>
                                    <td className="px-3 py-2">{theme || "—"}</td>
                                    <td className="px-3 py-2 font-mono text-slate-700 dark:text-slate-300">
                                        {flags || "—"}
                                    </td>
                                    <td className="px-3 py-2 text-slate-700 dark:text-slate-300">
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="min-w-0 flex-1">{renderDiffSummary(v.diff)}</div>
                                            {hasDiff ? (
                                                <button
                                                    type="button"
                                                    onClick={() => toggleExpanded(v.audit_log_id)}
                                                    className="shrink-0 rounded border border-slate-300 bg-white px-2 py-1 text-xs text-slate-900 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
                                                >
                                                    {expanded ? "Hide" : "Show"}
                                                </button>
                                            ) : null}
                                        </div>
                                        {expanded ? renderDiffDetails(v.diff) : null}
                                    </td>
                                    <td className="px-3 py-2">
                                        <button
                                            type="button"
                                            onClick={() => void doRollback(v.version)}
                                            disabled={rollbackLoading}
                                            className="rounded bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-white"
                                        >
                                            Rollback
                                        </button>
                                    </td>
                                </tr>
                            );
                        })}
                        {!loading && versions.length === 0 ? (
                            <tr>
                                <td
                                    colSpan={8}
                                    className="px-3 py-6 text-center text-slate-600 dark:text-slate-300"
                                >
                                    No versions found.
                                </td>
                            </tr>
                        ) : null}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
