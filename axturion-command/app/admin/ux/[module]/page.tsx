import { UXVersionHistory } from "@/components/admin/UXVersionHistory";

export default function UXModuleAdminPage({
    params,
}: {
    params: { module: string };
}) {
    return <UXVersionHistory module={params.module} />;
}
