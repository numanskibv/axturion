import type { TimeToCloseStatsResponse } from "@/lib/lifecycleApi";

function formatNumber(value: number): string {
    if (!Number.isFinite(value)) return "-";
    // Keep UI stable: show integers as-is, floats to 1 decimal.
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export default function TimeToCloseCard({
    stats,
}: {
    stats: TimeToCloseStatsResponse;
}) {
    return (
        <div className="rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
            <div className="mb-3">
                <h2 className="text-sm font-semibold">Time to Close</h2>
                <div className="text-xs text-[var(--ax-muted)]">Closed applications (org-scoped)</div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                    <div className="text-xs text-[var(--ax-muted)]">count</div>
                    <div className="tabular-nums">{formatNumber(stats.count)}</div>
                </div>
                <div>
                    <div className="text-xs text-[var(--ax-muted)]">avg_seconds</div>
                    <div className="tabular-nums">{formatNumber(stats.avg_seconds)}</div>
                </div>
                <div>
                    <div className="text-xs text-[var(--ax-muted)]">median_seconds</div>
                    <div className="tabular-nums">{formatNumber(stats.median_seconds)}</div>
                </div>
                <div>
                    <div className="text-xs text-[var(--ax-muted)]">p90_seconds</div>
                    <div className="tabular-nums">{formatNumber(stats.p90_seconds)}</div>
                </div>
            </div>
        </div>
    );
}
