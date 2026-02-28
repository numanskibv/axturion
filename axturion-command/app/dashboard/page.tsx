"use client";

import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";

import CommandLayout from "@/components/layout/CommandLayout";
import DashboardError from "@/components/dashboard/DashboardError";
import StageAgingTable from "@/components/dashboard/StageAgingTable";
import StageDurationTable from "@/components/dashboard/StageDurationTable";
import TimeToCloseCard from "@/components/dashboard/TimeToCloseCard";

import { useStageAging, useStageDurationSummary, useTimeToClose } from "@/hooks/useLifecycle";
import { usePolicyConfig } from "@/hooks/usePolicyConfig";

function SkeletonBlock({ heightClass }: { heightClass: string }) {
    return (
        <div
            className={
                "animate-pulse rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] " +
                heightClass
            }
        />
    );
}

function DashboardInner() {
    const searchParams = useSearchParams();
    const queryWorkflowId = searchParams.get("workflow_id")?.trim() ?? "";

    const stageAging = useStageAging();
    const timeToClose = useTimeToClose();
    const policy = usePolicyConfig();

    const inferredWorkflowId = useMemo(() => {
        const first = stageAging.data?.[0];
        return first?.workflow_id ?? "";
    }, [stageAging.data]);

    const workflowId = queryWorkflowId || inferredWorkflowId;
    const stageDuration = useStageDurationSummary(workflowId);

    return (
        <CommandLayout module="dashboard">
            <div className="mx-auto max-w-6xl space-y-6 p-6">
                <div>
                    <h1 className="text-lg font-semibold">Lifecycle Dashboard</h1>
                    <div className="text-sm text-[var(--ax-muted)]">
                        Uses reporting endpoints (org-scoped) with localStorage identity.
                    </div>
                </div>

                <div>
                    {timeToClose.loading && !timeToClose.data ? (
                        <SkeletonBlock heightClass="h-28" />
                    ) : timeToClose.error ? (
                        <DashboardError title="Time to Close" message={timeToClose.error.message} />
                    ) : timeToClose.data ? (
                        <TimeToCloseCard stats={timeToClose.data} />
                    ) : null}
                </div>

                <div>
                    {stageAging.loading && !stageAging.data ? (
                        <SkeletonBlock heightClass="h-64" />
                    ) : stageAging.error ? (
                        <DashboardError title="Stage Aging" message={stageAging.error.message} />
                    ) : stageAging.data ? (
                        <StageAgingTable
                            items={stageAging.data}
                            slaDays={policy.policy?.stage_aging_sla_days ?? 7}
                        />
                    ) : null}
                </div>

                <div>
                    {!workflowId ? (
                        <DashboardError
                            title="Stage Duration Summary"
                            message="Select a workflow to view stage duration analytics."
                        />
                    ) : stageDuration.loading && !stageDuration.data ? (
                        <SkeletonBlock heightClass="h-64" />
                    ) : stageDuration.error ? (
                        <DashboardError
                            title="Stage Duration Summary"
                            message={stageDuration.error.message}
                        />
                    ) : stageDuration.data ? (
                        <StageDurationTable items={stageDuration.data} />
                    ) : null}
                </div>
            </div>
        </CommandLayout>
    );
}

export default function DashboardPage() {
    return (
        <Suspense
            fallback={
                <div className="mx-auto max-w-6xl space-y-6 p-6">
                    <div className="animate-pulse rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
                        <div className="h-4 w-48 rounded bg-[var(--ax-border)]" />
                        <div className="mt-2 h-3 w-80 rounded bg-[var(--ax-border)]" />
                    </div>
                    <SkeletonBlock heightClass="h-28" />
                    <SkeletonBlock heightClass="h-64" />
                    <SkeletonBlock heightClass="h-64" />
                </div>
            }
        >
            <DashboardInner />
        </Suspense>
    );
}
