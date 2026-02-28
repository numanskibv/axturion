"use client";

import type { TimeToCloseStatsResponse } from "@/lib/lifecycleApi";
import { formatDuration } from "@/lib/timeFormat";
import { useTranslations } from "next-intl";

export default function TimeToCloseCard({
    stats,
}: {
    stats: TimeToCloseStatsResponse;
}) {
    const t = useTranslations("dashboard");

    return (
        <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
            <div className="mb-3">
                <h2 className="text-sm font-semibold">{t("timeToClose.title")}</h2>
                <div className="text-xs text-[color:var(--ax-muted)]">{t("timeToClose.subtitle")}</div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                    <div className="text-xs text-[color:var(--ax-muted)]">{t("timeToClose.fields.count")}</div>
                    <div className="tabular-nums">{stats.count}</div>
                </div>
                <div>
                    <div className="text-xs text-[color:var(--ax-muted)]">{t("timeToClose.fields.avg")}</div>
                    <div className="tabular-nums">{formatDuration(stats.avg_seconds)}</div>
                </div>
                <div>
                    <div className="text-xs text-[color:var(--ax-muted)]">{t("timeToClose.fields.median")}</div>
                    <div className="tabular-nums">{formatDuration(stats.median_seconds)}</div>
                </div>
                <div>
                    <div className="text-xs text-[color:var(--ax-muted)]">{t("timeToClose.fields.p90")}</div>
                    <div className="tabular-nums">{formatDuration(stats.p90_seconds)}</div>
                </div>
            </div>
        </div>
    );
}
