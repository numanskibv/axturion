import "./globals.css";

import type { AbstractIntlMessages } from "next-intl";

import en from "@/messages/en.json";
import nl from "@/messages/nl.json";
import { IdentityIntlProvider } from "@/components/IdentityIntlProvider";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <IdentityIntlProvider
          messagesEn={en as AbstractIntlMessages}
          messagesNl={nl as AbstractIntlMessages}
        >
          {children}
        </IdentityIntlProvider>
      </body>
    </html>
  );
}