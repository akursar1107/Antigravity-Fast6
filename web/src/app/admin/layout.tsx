import { redirect } from "next/navigation";
import { getTokenFromSession } from "@/lib/auth";
import AdminLayoutClient from "@/components/admin/AdminLayoutClient";

export default async function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const token = await getTokenFromSession();
  if (!token) {
    redirect("/login?redirect=/admin");
  }
  return <AdminLayoutClient>{children}</AdminLayoutClient>;
}
