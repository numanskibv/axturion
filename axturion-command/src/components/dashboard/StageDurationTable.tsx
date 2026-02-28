"use client";

import type { StageDurationSummaryItem } from "@/lib/lifecycleApi";
import { formatDuration } from "@/lib/timeFormat";
import { useTranslations } from "next-intl";

export default function StageDurationTable({
    items,
    hideHeader,
}: {
    items: StageDurationSummaryItem[];
    hideHeader?: boolean;
}) {
    const t = useTranslations("dashboard");

    return (
        <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
            {hideHeader ? null : (
                <div className="mb-3 flex items-center justify-between">
                    <h2 className="text-sm font-semibold">{t("stageDuration.title")}</h2>
                    <div className="text-xs text-[color:var(--ax-muted)]">
                        {t("stageDuration.stagesCount", { count: items.length })}
                    </div>
                </div>
            )}

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="text-xs text-[color:var(--ax-muted)]">
                        <tr className="border-b border-[color:var(--ax-border)]">
                            <th className="py-2 pr-3 font-medium">{t("stageDuration.columns.stage")}</th>
                            <th className="py-2 pr-3 font-medium">{t("stageDuration.columns.avg")}</th>
                            <th className="py-2 pr-3 font-medium">{t("stageDuration.columns.median")}</th>
                            <th className="py-2 pr-3 font-medium">{t("stageDuration.columns.p90")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr>
                                <td className="py-4 text-[color:var(--ax-muted)]" colSpan={4}>
                                    {t("common.noData")}
                                </td>
                            </tr>
                        ) : (
                            items.map((row) => (
                                <tr key={row.stage} className="border-b border-[color:var(--ax-border)]">
                                    <td className="py-2 pr-3">{row.stage}</td>
                                    <td className="py-2 pr-3 tabular-nums">
                                        {formatDuration(row.avg_duration_seconds)}
                                    </td>
                                    <td className="py-2 pr-3 tabular-nums">
                                        {formatDuration(row.median_duration_seconds)}
                                    </td>
                                    <td className="py-2 pr-3 tabular-nums">
                                        {formatDuration(row.p90_duration_seconds)}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
