"use client";

import { useMemo } from "react";
import { useParams } from "next/navigation";

import CommandLayout from "@/components/layout/CommandLayout";
import DashboardError from "@/components/dashboard/DashboardError";
import StageDurationBreakdownTable from "@/components/dashboard/StageDurationBreakdownTable";

import { useStageDurationBreakdown } from "@/hooks/useStageDurationBreakdown";

function SkeletonBlock({ heightClass }: { heightClass: string }) {
    return (
        <div
            className={
                "animate-pulse rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] " +
                heightClass
            }
        />
    );
}

function normalizeParam(value: string | string[] | undefined): string | null {
    if (typeof value === "string") return value.trim() || null;
    if (Array.isArray(value)) return value[0]?.trim() || null;
    return null;
}

export default function WorkflowDeepDivePage() {
    const params = useParams();
    const workflowId = normalizeParam(params?.workflowId as string | string[] | undefined);

    const windows = useMemo(() => {
        const now = new Date();
        const currentTo = now;
        const currentFrom = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

        const previousTo = currentFrom;
        const previousFrom = new Date(previousTo.getTime() - 30 * 24 * 60 * 60 * 1000);

        return {
            current: {
                from: currentFrom.toISOString(),
                to: currentTo.toISOString(),
            },
            previous: {
                from: previousFrom.toISOString(),
                to: previousTo.toISOString(),
            },
        };
    }, []);

    const current = useStageDurationBreakdown(workflowId, windows.current);
    const previous = useStageDurationBreakdown(workflowId, windows.previous);

    const comparison = useMemo(() => {
        if (!current.data) return null;

        const previousMap = new Map(
            previous.data?.map((item) => [item.stage, item]) ?? [],
        );

        return current.data.map((stage) => {
            const prev = previousMap.get(stage.stage);

            const previousMedian = prev?.median_seconds ?? null;

            let delta: number | null = null;
            let trend: "faster" | "slower" | "stable" | "new" = "stable";

            if (previousMedian === null) {
                trend = "new";
            } else {
                delta = stage.median_seconds - previousMedian;

                if (Math.abs(delta) < 60) {
                    trend = "stable";
                } else if (delta < 0) {
                    trend = "faster";
                } else {
                    trend = "slower";
                }
            }

            return {
                ...stage,
                previousMedian,
                delta,
                trend,
            };
        });
    }, [current.data, previous.data]);

    const bottleneckStage = useMemo(() => {
        const data = current.data;
        if (!data?.length) return null;
        return [...data].sort((a, b) => b.median_seconds - a.median_seconds)[0]?.stage ?? null;
    }, [current.data]);

    return (
        <CommandLayout module="dashboard">
            <div className="mx-auto max-w-6xl space-y-6 p-6">
                <div>
                    <h1 className="text-lg font-semibold">Workflow Deep Dive</h1>
                    <div className="text-sm text-[color:var(--ax-muted)]">
                        Stage duration breakdown (audit-driven, window-aware)
                    </div>
                </div>

                {!workflowId ? (
                    <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
                        <div className="text-sm text-[color:var(--ax-muted)]">No workflow selected.</div>
                    </div>
                ) : current.error || previous.error ? (
                    <DashboardError
                        title="Workflow Deep Dive"
                        message={(current.error ?? previous.error)?.message ?? "Unknown error"}
                    />
                ) : current.loading || previous.loading || !current.data || !previous.data ? (
                    <SkeletonBlock heightClass="h-64" />
                ) : current.data.length === 0 ? (
                    <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
                        <div className="text-sm text-[color:var(--ax-muted)]">No data</div>
                    </div>
                ) : comparison ? (
                    <StageDurationBreakdownTable
                        items={comparison}
                        bottleneckStage={bottleneckStage}
                    />
                ) : null}
            </div>
        </CommandLayout>
    );
}
