"use client";

import { useTranslations } from "next-intl";

function getIndicatorClasses(args: {
    breachCount: number;
    breachPercent: number;
}): {
    badgeBg: string;
    badgeText: string;
} {
    if (args.breachCount === 0) {
        return { badgeBg: "bg-green-500/15", badgeText: "text-green-400" };
    }

    if (args.breachPercent <= 20) {
        return { badgeBg: "bg-amber-500/15", badgeText: "text-amber-400" };
    }

    return { badgeBg: "bg-red-500/15", badgeText: "text-red-400" };
}

export default function SLABreachCard({
    total,
    breachCount,
    breachPercent,
    slaDays,
}: {
    total: number;
    breachCount: number;
    breachPercent: number;
    slaDays: number;
}) {
    const t = useTranslations("dashboard");

    const safeTotal = Number.isFinite(total) ? Math.max(0, Math.floor(total)) : 0;
    const safeBreachCount = Number.isFinite(breachCount)
        ? Math.max(0, Math.floor(breachCount))
        : 0;
    const safeBreachPercent = Number.isFinite(breachPercent) ? Math.max(0, breachPercent) : 0;
    const safeSlaDays = Number.isFinite(slaDays) ? Math.max(1, Math.floor(slaDays)) : 7;

    const indicator = getIndicatorClasses({
        breachCount: safeBreachCount,
        breachPercent: safeBreachPercent,
    });

    return (
        <div className="rounded-[length:var(--ax-radius)] border border-[color:var(--ax-border)] bg-[color:var(--ax-surface)] p-4">
            <div className="mb-3 flex items-start justify-between gap-3">
                <div>
                    <h2 className="text-sm font-semibold">{t("slaBreaches.title")}</h2>
                    <div className="text-xs text-[color:var(--ax-muted)]">
                        {t("slaBreaches.subtitle", { days: safeSlaDays })}
                    </div>
                </div>

                <div
                    className={
                        "shrink-0 rounded-full px-2 py-1 text-xs font-medium " +
                        indicator.badgeBg +
                        " " +
                        indicator.badgeText
                    }
                >
                    {safeBreachCount === 0
                        ? t("slaBreaches.badge.ok")
                        : t("slaBreaches.badge.attention")}
                </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                    <div className="text-xs text-[color:var(--ax-muted)]">{t("slaBreaches.fields.breachCount")}</div>
                    <div className="tabular-nums text-[color:var(--ax-text)]">{safeBreachCount}</div>
                </div>
                <div>
                    <div className="text-xs text-[color:var(--ax-muted)]">{t("slaBreaches.fields.total")}</div>
                    <div className="tabular-nums text-[color:var(--ax-text)]">{safeTotal}</div>
                </div>
                <div>
                    <div className="text-xs text-[color:var(--ax-muted)]">{t("slaBreaches.fields.breachPercent")}</div>
                    <div className="tabular-nums text-[color:var(--ax-text)]">
                        {safeTotal === 0 ? "0%" : `${safeBreachPercent.toFixed(1)}%`}
                    </div>
                </div>
                <div>
                    <div className="text-xs text-[color:var(--ax-muted)]">{t("slaBreaches.fields.slaDays")}</div>
                    <div className="tabular-nums text-[color:var(--ax-text)]">{safeSlaDays}d</div>
                </div>
            </div>
        </div>
    );
}
