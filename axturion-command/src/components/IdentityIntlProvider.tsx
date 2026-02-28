"use client";

import type { ReactNode } from "react";
import { NextIntlClientProvider, type AbstractIntlMessages } from "next-intl";

import { useIdentity } from "@/hooks/useIdentity";

type Props = {
    children: ReactNode;
    messagesEn: AbstractIntlMessages;
    messagesNl: AbstractIntlMessages;
};

export function IdentityIntlProvider({ children, messagesEn, messagesNl }: Props) {
    const { identity, loading } = useIdentity();

    const locale = identity?.effective_language ?? "en";
    const messages = locale === "nl" ? messagesNl : messagesEn;

    // Minimal shell while loading, but keep provider so translations don't crash.
    if (loading && !identity) {
        return (
            <NextIntlClientProvider locale="en" messages={messagesEn} timeZone="UTC">
                {children}
            </NextIntlClientProvider>
        );
    }

    return (
        <NextIntlClientProvider locale={locale} messages={messages} timeZone="UTC">
            {children}
        </NextIntlClientProvider>
    );
}
