"use client";

import type { WorkflowListItem } from "@/lib/workflowApi";

export default function WorkflowSelector({
    workflows,
    value,
    onChange,
    placeholder,
}: {
    workflows: WorkflowListItem[];
    value: string | null;
    onChange: (id: string) => void;
    placeholder: string;
}) {
    const normalizedValue = (value ?? "").trim();

    return (
        <select
            value={normalizedValue}
            onChange={(e) => {
                const next = e.target.value.trim();
                if (!next) return;
                onChange(next);
            }}
            className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] px-3 py-2 text-sm"
        >
            <option value="" disabled>
                {placeholder}
            </option>

            {workflows.map((wf) => (
                <option key={wf.id} value={wf.id}>
                    {wf.name}
                </option>
            ))}
        </select>
    );
}
