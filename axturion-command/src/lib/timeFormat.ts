export function formatDuration(seconds: number): string {
    const safeSeconds = Number.isFinite(seconds) ? Math.max(0, Math.floor(seconds)) : 0;

    if (safeSeconds < 60) return `${safeSeconds}s`;
    if (safeSeconds < 60 * 60) return `${Math.floor(safeSeconds / 60)}m`;
    if (safeSeconds < 24 * 60 * 60) return `${Math.floor(safeSeconds / (60 * 60))}h`;
    return `${Math.floor(safeSeconds / (24 * 60 * 60))}d`;
}