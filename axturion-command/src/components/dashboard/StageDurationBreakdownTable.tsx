"use client";

import type { StageDurationBreakdownItem } from "@/lib/lifecycleApi";
import { formatDuration } from "@/lib/timeFormat";

export type ComparedStageItem = StageDurationBreakdownItem & {
    previousMedian: number | null;
    delta: number | null;
    trend: "faster" | "slower" | "stable" | "new";
};

export default function StageDurationBreakdownTable({
    items,
    bottleneckStage,
}: {
    items: ComparedStageItem[];
    bottleneckStage?: string | null;
}) {
    const formatMaybeDuration = (seconds: number | null): string => {
        if (seconds == null) return "—";
        return formatDuration(seconds);
    };

    const formatSignedDelta = (seconds: number | null): string => {
        if (seconds == null) return "—";
        if (seconds === 0) return formatDuration(0);
        const sign = seconds < 0 ? "-" : "+";
        return sign + formatDuration(Math.abs(seconds));
    };

    return (
        <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="text-xs text-[color:var(--ax-muted)]">
                        <tr className="border-b border-[color:var(--ax-border)]">
                            <th className="py-2 pr-3 font-medium">Stage</th>
                            <th className="py-2 pr-3 font-medium">Median</th>
                            <th className="py-2 pr-3 font-medium">Previous</th>
                            <th className="py-2 pr-3 font-medium">Δ</th>
                            <th className="py-2 pr-3 font-medium">Trend</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr>
                                <td className="py-4 text-[color:var(--ax-muted)]" colSpan={5}>
                                    No data
                                </td>
                            </tr>
                        ) : (
                            items.map((row) => {
                                const isBottleneck =
                                    bottleneckStage != null && row.stage === bottleneckStage;

                                const trendLabel =
                                    row.trend === "faster"
                                        ? "↑ Faster"
                                        : row.trend === "slower"
                                            ? "↓ Slower"
                                            : row.trend === "stable"
                                                ? "→ Stable"
                                                : "• New";

                                const trendClass =
                                    row.trend === "faster"
                                        ? "text-green-400"
                                        : row.trend === "slower"
                                            ? "text-red-400"
                                            : row.trend === "stable"
                                                ? "text-[color:var(--ax-muted)]"
                                                : "text-[color:var(--ax-muted)] opacity-70";

                                return (
                                    <tr
                                        key={row.stage}
                                        className={
                                            "border-b border-[color:var(--ax-border)]" +
                                            (isBottleneck
                                                ? " border-l-2 border-l-[color:var(--ax-muted)]"
                                                : "")
                                        }
                                    >
                                        <td className="py-2 pr-3">{row.stage}</td>
                                        <td className="py-2 pr-3 tabular-nums">
                                            {formatDuration(row.median_seconds)}
                                        </td>
                                        <td className="py-2 pr-3 tabular-nums">
                                            {formatMaybeDuration(row.previousMedian)}
                                        </td>
                                        <td className="py-2 pr-3 tabular-nums">
                                            {formatSignedDelta(row.delta)}
                                        </td>
                                        <td className={"py-2 pr-3 font-medium " + trendClass}>
                                            {trendLabel}
                                        </td>
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
