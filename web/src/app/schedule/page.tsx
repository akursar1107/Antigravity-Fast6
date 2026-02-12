import { redirect } from "next/navigation";

const CURRENT_WEEK = process.env.NEXT_PUBLIC_CURRENT_WEEK ?? "1";

export default function SchedulePage() {
  redirect(`/schedule/${CURRENT_WEEK}`);
}
