"use client";

import { formatDuration } from "@/lib/timeFormat";
import { useTranslations } from "next-intl";

export default function CommandStrip({
    openCount,
    breachCount,
    breachPercent,
    avgTimeToClose,
}: {
    openCount: number;
    breachCount: number;
    breachPercent: number;
    avgTimeToClose?: number;
}) {
    const t = useTranslations("dashboard");

    const safeOpenCount = Number.isFinite(openCount) ? Math.max(0, Math.floor(openCount)) : 0;
    const safeBreachCount = Number.isFinite(breachCount) ? Math.max(0, Math.floor(breachCount)) : 0;
    const safeBreachPercent = Number.isFinite(breachPercent) ? Math.max(0, breachPercent) : 0;
    const safeAvgTimeToClose =
        typeof avgTimeToClose === "number" && Number.isFinite(avgTimeToClose) ? avgTimeToClose : undefined;

    return (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiTile label={t("commandStrip.openCount")} value={String(safeOpenCount)} />
            <KpiTile label={t("commandStrip.breachCount")} value={String(safeBreachCount)} />
            <KpiTile
                label={t("commandStrip.breachPercent")}
                value={`${safeBreachPercent.toFixed(1)}%`}
            />
            <KpiTile
                label={t("commandStrip.avgTimeToClose")}
                value={safeAvgTimeToClose === undefined ? "—" : formatDuration(safeAvgTimeToClose)}
            />
        </div>
    );
}

function KpiTile({ label, value }: { label: string; value: string }) {
    return (
        <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
            <div className="text-xs text-[color:var(--ax-muted)]">{label}</div>
            <div className="mt-1 tabular-nums text-sm font-semibold">{value}</div>
        </div>
    );
}
