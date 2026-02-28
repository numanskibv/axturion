"use client";

import { formatDuration } from "@/lib/timeFormat";
import { useTranslations } from "next-intl";

type RiskLevel = "controlled" | "watch" | "at_risk" | "critical";
type Trend = "improving" | "stable" | "worsening";

export default function CommandStrip({
    openCount,
    breachCount,
    breachPercent,
    avgTimeToClose,
    riskLevel,
    trend,
}: {
    openCount: number;
    breachCount: number;
    breachPercent: number;
    avgTimeToClose?: number;
    riskLevel: RiskLevel;
    trend?: Trend;
}) {
    const t = useTranslations("dashboard");

    const riskLabelByLevel: Record<RiskLevel, string> = {
        controlled: t("commandStrip.risk.controlled"),
        watch: t("commandStrip.risk.watch"),
        at_risk: t("commandStrip.risk.at_risk"),
        critical: t("commandStrip.risk.critical"),
    };

    const riskLabel = riskLabelByLevel[riskLevel];

    const trendLabel =
        trend === "improving"
            ? "↑ Improving"
            : trend === "worsening"
                ? "↓ Worsening"
                : trend === "stable"
                    ? "→ Stable"
                    : undefined;

    return (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <KpiTile label={t("commandStrip.openCount")} value={String(openCount)} />
            <KpiTile label={t("commandStrip.breachCount")} value={String(breachCount)} />
            <KpiTile
                label={t("commandStrip.breachPercent")}
                value={`${breachPercent}%`}
                subLabel={riskLabel}
                subLabel2={trendLabel}
            />
            <KpiTile
                label={t("commandStrip.avgTimeToClose")}
                value={avgTimeToClose === undefined ? "—" : formatDuration(avgTimeToClose)}
            />
        </div>
    );
}

function KpiTile({
    label,
    value,
    subLabel,
    subLabel2,
}: {
    label: string;
    value: string;
    subLabel?: string;
    subLabel2?: string;
}) {
    return (
        <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
            <div className="text-xs text-[color:var(--ax-muted)]">{label}</div>
            <div className="mt-1 tabular-nums text-sm font-semibold">{value}</div>
            {subLabel ? (
                <div className="mt-1 text-xs text-[color:var(--ax-muted)]">{subLabel}</div>
            ) : null}
            {subLabel2 ? (
                <div className="mt-1 text-xs text-[color:var(--ax-muted)]">{subLabel2}</div>
            ) : null}
        </div>
    );
}
