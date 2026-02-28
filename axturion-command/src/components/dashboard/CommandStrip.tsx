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

    return (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiTile label={t("commandStrip.openCount")} value={String(openCount)} />
            <KpiTile label={t("commandStrip.breachCount")} value={String(breachCount)} />
            <KpiTile
                label={t("commandStrip.breachPercent")}
                value={`${breachPercent}%`}
            />
            <KpiTile
                label={t("commandStrip.avgTimeToClose")}
                value={avgTimeToClose === undefined ? "—" : formatDuration(avgTimeToClose)}
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
