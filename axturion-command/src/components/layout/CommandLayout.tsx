"use client";

import { useEffect } from "react";
import { useUXConfig } from "@/hooks/useUXConfig";

export default function CommandLayout({
    module,
    children,
}: {
    module: string;
    children: React.ReactNode;
}) {
    const { config, loading } = useUXConfig(module);

    const layout = config?.config?.layout ?? "default";
    const theme = config?.config?.theme ?? "dark";

    // 🔥 Runtime theme switch
    useEffect(() => {
        if (typeof window === "undefined") return;

        document.documentElement.setAttribute("data-theme", theme);
    }, [theme]);

    if (loading && !config) {
        return <div className="p-10">Loading configuration...</div>;
    }

    return (
        <div className={`layout-${layout}`}>
            {children}
        </div>
    );
}