"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import DashboardLayout from "../dashboard/layout";
import { FileText, ShieldAlert } from "lucide-react";

export default function AuditPage() {
  const { selectedSchoolId } = useSchoolStore();

  const { data: logs = [], isLoading } = useQuery({
    queryKey: ["audit", selectedSchoolId],
    queryFn: async () => (await api.get(`/audit?school_id=${selectedSchoolId}`)).data,
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Audit Log (İşlem Geçmişi)</h1>
          <p className="text-sm text-slate-500">Sistem üzerinde gerçekleştirilen tüm kritik değişikliklerin tarihçesi</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-3">Tarih</th>
                <th className="px-6 py-3">Kullanıcı</th>
                <th className="px-6 py-3">İşlem</th>
                <th className="px-6 py-3">Varlık</th>
                <th className="px-6 py-3">Açıklama</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Yükleniyor...</td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Henüz kayıtlı audit log yok.</td>
                </tr>
              ) : (
                logs.map((l: any) => (
                  <tr key={l.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 text-xs font-mono">{new Date(l.created_at).toLocaleString("tr-TR")}</td>
                    <td className="px-6 py-4 font-semibold text-slate-800">{l.user_email || "Sistem"}</td>
                    <td className="px-6 py-4">
                      <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-bold text-slate-700">
                        {l.action}
                      </span>
                    </td>
                    <td className="px-6 py-4">{l.entity_type} #{l.entity_id}</td>
                    <td className="px-6 py-4 text-xs text-slate-500">{l.description || "-"}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </DashboardLayout>
  );
}
