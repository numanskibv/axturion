import type { TimeToCloseStatsResponse } from "@/lib/lifecycleApi";
import { formatDuration } from "@/lib/timeFormat";

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
                    <div className="tabular-nums">{stats.count}</div>
                </div>
                <div>
                    <div className="text-xs text-[var(--ax-muted)]">avg_seconds</div>
                    <div className="tabular-nums">{formatDuration(stats.avg_seconds)}</div>
                </div>
                <div>
                    <div className="text-xs text-[var(--ax-muted)]">median_seconds</div>
                    <div className="tabular-nums">{formatDuration(stats.median_seconds)}</div>
                </div>
                <div>
                    <div className="text-xs text-[var(--ax-muted)]">p90_seconds</div>
                    <div className="tabular-nums">{formatDuration(stats.p90_seconds)}</div>
                </div>
            </div>
        </div>
    );
}
