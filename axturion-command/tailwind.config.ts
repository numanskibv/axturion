import type { Config } from "tailwindcss";

const config: Config = {
    content: [
        "./app/**/*.{ts,tsx}",
        "./src/**/*.{ts,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                ax: {
                    bg: "#0B1220",         // main background
                    surface: "#111827",    // cards
                    border: "#1F2937",
                    muted: "#6B7280",
                    text: "#E5E7EB",

                    primary: "#2563EB",
                    primaryHover: "#1D4ED8",

                    danger: "#DC2626",
                    success: "#16A34A",
                },
            },
            borderRadius: {
                ax: "0.75rem",
            },
            boxShadow: {
                ax: "0 10px 40px rgba(0,0,0,0.4)",
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
            },
        },
    },
    plugins: [],
};

export default config;