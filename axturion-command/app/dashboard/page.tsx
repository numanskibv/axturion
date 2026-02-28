"use client";

import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";

import CommandLayout from "@/components/layout/CommandLayout";
import StageAgingTable from "@/components/dashboard/StageAgingTable";
import StageDurationTable from "@/components/dashboard/StageDurationTable";
import TimeToCloseCard from "@/components/dashboard/TimeToCloseCard";

import { useStageAging, useStageDurationSummary, useTimeToClose } from "@/hooks/useLifecycle";

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
                        <div className="rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
                            <div className="text-sm font-semibold">Time to Close</div>
                            <div className="mt-2 text-sm text-red-400">{timeToClose.error.message}</div>
                        </div>
                    ) : timeToClose.data ? (
                        <TimeToCloseCard stats={timeToClose.data} />
                    ) : null}
                </div>

                <div>
                    {stageAging.loading && !stageAging.data ? (
                        <SkeletonBlock heightClass="h-64" />
                    ) : stageAging.error ? (
                        <div className="rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
                            <div className="text-sm font-semibold">Stage Aging</div>
                            <div className="mt-2 text-sm text-red-400">{stageAging.error.message}</div>
                        </div>
                    ) : stageAging.data ? (
                        <StageAgingTable items={stageAging.data} />
                    ) : null}
                </div>

                <div>
                    {!workflowId ? (
                        <div className="rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
                            <div className="text-sm font-semibold">Stage Duration Summary</div>
                            <div className="mt-2 text-sm text-red-400">
                                Missing workflow_id (pass ?workflow_id=... or ensure stage aging returns data)
                            </div>
                        </div>
                    ) : stageDuration.loading && !stageDuration.data ? (
                        <SkeletonBlock heightClass="h-64" />
                    ) : stageDuration.error ? (
                        <div className="rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
                            <div className="text-sm font-semibold">Stage Duration Summary</div>
                            <div className="mt-2 text-sm text-red-400">{stageDuration.error.message}</div>
                        </div>
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
