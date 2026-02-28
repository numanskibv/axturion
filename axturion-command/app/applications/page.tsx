import CommandLayout from "@/components/layout/CommandLayout";

export default function ApplicationsPage() {
    return (
        <CommandLayout module="applications">
            <div className="p-6">
                <h1 className="text-xl font-semibold">Applications</h1>
                <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                    Config-driven layout wrapper is active.
                </p>
            </div>
        </CommandLayout>
    );
}
