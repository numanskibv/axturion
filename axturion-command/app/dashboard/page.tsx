"use client";

import { Suspense, useEffect, useMemo, useState } from "react";

import CommandLayout from "@/components/layout/CommandLayout";
import DashboardError from "@/components/dashboard/DashboardError";
import StageAgingTable from "@/components/dashboard/StageAgingTable";
import StageDurationTable from "@/components/dashboard/StageDurationTable";
import TimeToCloseCard from "@/components/dashboard/TimeToCloseCard";
import SLABreachCard from "@/components/dashboard/SLABreachCard";
import WorkflowSelector from "@/components/dashboard/WorkflowSelector";

import { useStageAging, useStageDurationSummary, useTimeToClose } from "@/hooks/useLifecycle";
import { usePolicyConfig } from "@/hooks/usePolicyConfig";
import { useWorkflows } from "@/hooks/useWorkflows";

import { useTranslations } from "next-intl";

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

function DashboardInner() {
    const t = useTranslations("dashboard");

    const { workflows, loading: workflowsLoading, error: workflowsError } = useWorkflows();
    const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
    const [selectedPeriod] = useState<string>("all");

    useEffect(() => {
        if (selectedWorkflowId !== null) return;
        if (workflows.length === 0) return;

        const timer = window.setTimeout(() => {
            setSelectedWorkflowId(workflows[0].id);
        }, 0);

        return () => window.clearTimeout(timer);
    }, [selectedWorkflowId, workflows]);

    return (
        <CommandLayout module="dashboard">
            <div className="mx-auto max-w-6xl space-y-6 p-6">
                <div>
                    <h1 className="text-lg font-semibold">{t("title")}</h1>
                    <div className="text-sm text-[color:var(--ax-muted)]">
                        {t("subtitle")}
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <WorkflowSelector
                        workflows={workflows}
                        value={selectedWorkflowId}
                        onChange={(id) => setSelectedWorkflowId(id)}
                        placeholder={t("workflowSelector.placeholder")}
                    />

                    {workflowsLoading ? (
                        <div className="text-sm text-[color:var(--ax-muted)]">{t("workflowSelector.loading")}</div>
                    ) : workflowsError ? (
                        <div className="text-sm text-red-400">{workflowsError.message}</div>
                    ) : null}

                    <div className="sr-only">{selectedPeriod}</div>
                </div>

                {!selectedWorkflowId ? (
                    <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
                        <div className="text-sm text-[color:var(--ax-muted)]">{t("emptyState.selectWorkflow")}</div>
                    </div>
                ) : (
                    <DashboardMetrics workflowId={selectedWorkflowId} />
                )}
            </div>
        </CommandLayout>
    );
}

function DashboardMetrics({ workflowId }: { workflowId: string }) {
    const t = useTranslations("dashboard");

    const stageAging = useStageAging({ workflowId });
    const timeToClose = useTimeToClose({ workflowId });
    const policy = usePolicyConfig();

    const slaDays = policy.policy?.stage_aging_sla_days ?? 7;
    const slaSeconds = Math.max(1, Math.floor(slaDays)) * 24 * 60 * 60;

    const breachMetrics = useMemo(() => {
        const items = stageAging.data ?? [];
        const total = items.length;
        const breachCount = items.reduce((acc, row) => (row.age_seconds > slaSeconds ? acc + 1 : acc), 0);
        const breachPercent = total === 0 ? 0 : (breachCount / total) * 100;
        return { total, breachCount, breachPercent };
    }, [stageAging.data, slaSeconds]);

    const stageDuration = useStageDurationSummary(workflowId);

    return (
        <>
            <div>
                {timeToClose.loading && !timeToClose.data ? (
                    <SkeletonBlock heightClass="h-28" />
                ) : timeToClose.error ? (
                    <DashboardError title={t("timeToClose.title")} message={timeToClose.error.message} />
                ) : timeToClose.data ? (
                    <TimeToCloseCard stats={timeToClose.data} />
                ) : null}
            </div>

            <div>
                {stageAging.loading && !stageAging.data ? (
                    <SkeletonBlock heightClass="h-28" />
                ) : stageAging.error ? (
                    <DashboardError title={t("slaBreaches.title")} message={stageAging.error.message} />
                ) : (
                    <SLABreachCard
                        total={breachMetrics.total}
                        breachCount={breachMetrics.breachCount}
                        breachPercent={breachMetrics.breachPercent}
                        slaDays={slaDays}
                    />
                )}
            </div>

            <div>
                {stageAging.loading && !stageAging.data ? (
                    <SkeletonBlock heightClass="h-64" />
                ) : stageAging.error ? (
                    <DashboardError title={t("stageAging.title")} message={stageAging.error.message} />
                ) : stageAging.data ? (
                    <StageAgingTable items={stageAging.data} slaDays={policy.policy?.stage_aging_sla_days ?? 7} />
                ) : null}
            </div>

            <div>
                {stageDuration.loading && !stageDuration.data ? (
                    <SkeletonBlock heightClass="h-64" />
                ) : stageDuration.error ? (
                    <DashboardError title={t("stageDuration.title")} message={stageDuration.error.message} />
                ) : stageDuration.data ? (
                    <StageDurationTable items={stageDuration.data} />
                ) : null}
            </div>
        </>
    );
}

export default function DashboardPage() {
    return (
        <Suspense
            fallback={
                <div className="mx-auto max-w-6xl space-y-6 p-6">
                    <div className="animate-pulse rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
                        <div className="h-4 w-48 rounded bg-[color:var(--ax-border)]" />
                        <div className="mt-2 h-3 w-80 rounded bg-[color:var(--ax-border)]" />
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
