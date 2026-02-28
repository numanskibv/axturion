import type { StageDurationSummaryItem } from "@/lib/lifecycleApi";

function formatNumber(value: number): string {
    if (!Number.isFinite(value)) return "-";
    return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

export default function StageDurationTable({
    items,
}: {
    items: StageDurationSummaryItem[];
}) {
    return (
        <div className="rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold">Stage Duration Summary</h2>
                <div className="text-xs text-[var(--ax-muted)]">{items.length} stages</div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="text-xs text-[var(--ax-muted)]">
                        <tr className="border-b border-[var(--ax-border)]">
                            <th className="py-2 pr-3 font-medium">stage</th>
                            <th className="py-2 pr-3 font-medium">avg_duration_seconds</th>
                            <th className="py-2 pr-3 font-medium">median_duration_seconds</th>
                            <th className="py-2 pr-3 font-medium">p90_duration_seconds</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr>
                                <td className="py-4 text-[var(--ax-muted)]" colSpan={4}>
                                    No data
                                </td>
                            </tr>
                        ) : (
                            items.map((row) => (
                                <tr key={row.stage} className="border-b border-[var(--ax-border)]">
                                    <td className="py-2 pr-3">{row.stage}</td>
                                    <td className="py-2 pr-3 tabular-nums">
                                        {formatNumber(row.avg_duration_seconds)}
                                    </td>
                                    <td className="py-2 pr-3 tabular-nums">
                                        {formatNumber(row.median_duration_seconds)}
                                    </td>
                                    <td className="py-2 pr-3 tabular-nums">
                                        {formatNumber(row.p90_duration_seconds)}
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
