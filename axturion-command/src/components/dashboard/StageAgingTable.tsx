import type { StageAgingItem } from "@/lib/lifecycleApi";
import { formatDuration } from "@/lib/timeFormat";

const SEVEN_DAYS_SECONDS = 7 * 24 * 60 * 60;

export default function StageAgingTable({
    items,
}: {
    items: StageAgingItem[];
}) {
    return (
        <div className="rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold">Stage Aging</h2>
                <div className="text-xs text-[var(--ax-muted)]">{items.length} open</div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead className="text-xs text-[var(--ax-muted)]">
                        <tr className="border-b border-[var(--ax-border)]">
                            <th className="py-2 pr-3 font-medium">application_id</th>
                            <th className="py-2 pr-3 font-medium">current_stage</th>
                            <th className="py-2 pr-3 font-medium">age_seconds</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items.length === 0 ? (
                            <tr>
                                <td className="py-4 text-[var(--ax-muted)]" colSpan={3}>
                                    No data
                                </td>
                            </tr>
                        ) : (
                            items.map((row) => {
                                const isStale = row.age_seconds > SEVEN_DAYS_SECONDS;
                                return (
                                    <tr
                                        key={row.application_id}
                                        className={
                                            "border-b border-[var(--ax-border)] " +
                                            (isStale ? "bg-red-900/40" : "")
                                        }
                                    >
                                        <td className="py-2 pr-3 font-mono text-xs text-[var(--ax-text)]">
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
