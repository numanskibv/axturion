"use client";

import type { StageAgingItem } from "@/lib/lifecycleApi";
import { formatDuration } from "@/lib/timeFormat";
import { useTranslations } from "next-intl";

function toSlaSeconds(slaDays: number): number {
    const days = Number.isFinite(slaDays) ? Math.max(1, Math.floor(slaDays)) : 7;
    return days * 24 * 60 * 60;
}

export default function StageAgingTable({
    items,
    slaDays,
}: {
    items: StageAgingItem[];
    slaDays?: number;
}) {
    const t = useTranslations("dashboard");
    const slaSeconds = toSlaSeconds(slaDays ?? 7);
    return (
        <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold">{t("stageAging.title")}</h2>
                <div className="text-xs text-[color:var(--ax-muted)]">
                    {t("stageAging.openCount", { count: items.length })}
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="text-xs text-[color:var(--ax-muted)]">
                        <tr className="border-b border-[color:var(--ax-border)]">
                            <th className="py-2 pr-3 font-medium">{t("stageAging.columns.applicationId")}</th>
                            <th className="py-2 pr-3 font-medium">{t("stageAging.columns.currentStage")}</th>
                            <th className="py-2 pr-3 font-medium">{t("stageAging.columns.age")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr>
                                <td className="py-4 text-[color:var(--ax-muted)]" colSpan={3}>
                                    {t("common.noData")}
                                </td>
                            </tr>
                        ) : (
                            items.map((row) => {
                                const isStale = row.age_seconds > slaSeconds;
                                return (
                                    <tr
                                        key={row.application_id}
                                        className={
                                            "border-b border-[color:var(--ax-border)] " +
                                            (isStale ? "bg-red-900/40" : "")
                                        }
                                    >
                                        <td className="py-2 pr-3 font-mono text-xs text-[color:var(--ax-text)]">
                                            {row.application_id}
                                        </td>
                                        <td className="py-2 pr-3">{row.current_stage}</td>
                                        <td className="py-2 pr-3 tabular-nums">{formatDuration(row.age_seconds)}</td>
                                    </tr>
                                );
                            })
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
