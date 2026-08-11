"use client";

import { useAuthStore } from "@/stores/authStore";
import { useSchoolStore } from "@/stores/schoolStore";
import { LogOut, School as SchoolIcon, User as UserIcon, ChevronDown } from "lucide-react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function Navbar() {
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const { selectedSchoolId, setSchoolId } = useSchoolStore();

  const { data: schools = [] } = useQuery({
    queryKey: ["schools"],
    queryFn: async () => (await api.get("/schools")).data,
  });

  const activeSchool = schools.find((s: any) => s.id === selectedSchoolId) || schools[0];

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="flex h-16 w-full items-center justify-between border-b bg-white px-6 shadow-xs">
      <div className="flex items-center gap-3 text-slate-700">
        <SchoolIcon className="h-5 w-5 text-blue-600 shrink-0" />
        {schools.length > 1 ? (
          <div className="relative flex items-center gap-2">
            <span className="text-xs font-medium text-slate-500">Aktif Okul:</span>
            <select
              value={selectedSchoolId}
              onChange={(e) => setSchoolId(Number(e.target.value))}
              className="rounded-lg border border-slate-300 bg-slate-50 px-2.5 py-1 text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {schools.map((s: any) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.short_name || s.city})
                </option>
              ))}
            </select>
          </div>
        ) : (
          <span className="font-semibold text-sm text-slate-800">
            {activeSchool ? activeSchool.name : `Aktif Okul (ID: ${selectedSchoolId})`}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        {user && (
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <UserIcon className="h-4 w-4" />
            <span className="font-medium">{user.full_name}</span>
            <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-800 font-semibold">
              {user.global_role}
            </span>
          </div>
        )}

        <button
          onClick={handleLogout}
          className="flex items-center gap-1.5 rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50 transition"
        >
          <LogOut className="h-3.5 w-3.5" />
          Çıkış Yap
        </button>
      </div>
    </header>
  );
}
