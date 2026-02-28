export default function DashboardError({
    title,
    message,
}: {
    title: string;
    message: string;
}) {
    return (
        <div className="rounded-[var(--ax-radius)] border border-[var(--ax-border)] bg-[var(--ax-surface)] p-4">
            <div className="text-sm font-semibold">{title}</div>
            <div className="mt-2 text-sm text-red-400">{message}</div>
        </div>
    );
}
