import { redirect } from "next/navigation";

export default function RootPage() {
  // 重定向到預設語言
  redirect("/zh-TW");
}
