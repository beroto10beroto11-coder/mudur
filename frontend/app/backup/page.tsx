"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import DashboardLayout from "../dashboard/layout";
import { Database, Play, CheckCircle, Clock } from "lucide-react";

export default function BackupPage() {
  const queryClient = useQueryClient();

  const { data: backups = [], isLoading } = useQuery({
    queryKey: ["backups"],
    queryFn: async () => (await api.get("/backups")).data,
  });

  const triggerMutation = useMutation({
    mutationFn: async () => api.post("/backups/trigger"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["backups"] }),
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Veritabanı Yedekleme & Geri Yükleme</h1>
            <p className="text-sm text-slate-500">PostgreSQL pg_dump ile manuel ve otomatik (her gün 03:00) yedekleme</p>
          </div>
          <button
            onClick={() => triggerMutation.mutate()}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
          >
            <Play className="h-4 w-4" />
            Manuel Yedek Al
          </button>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-3">Yedek Adı</th>
                <th className="px-6 py-3">Tür</th>
                <th className="px-6 py-3">Tarih</th>
                <th className="px-6 py-3">Boyut</th>
                <th className="px-6 py-3">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Yükleniyor...</td>
                </tr>
              ) : backups.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Henüz alınmış yedek yok.</td>
                </tr>
              ) : (
                backups.map((b: any) => (
                  <tr key={b.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-bold text-slate-800 flex items-center gap-2">
                      <Database className="h-4 w-4 text-blue-600" />
                      {b.name}
                    </td>
                    <td className="px-6 py-4">{b.backup_type}</td>
                    <td className="px-6 py-4 text-xs font-mono">{new Date(b.created_at).toLocaleString("tr-TR")}</td>
                    <td className="px-6 py-4 text-xs">{b.file_size_bytes ? `${(b.file_size_bytes / 1024 / 1024).toFixed(2)} MB` : "-"}</td>
                    <td className="px-6 py-4">
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                        <CheckCircle className="h-3.5 w-3.5" />
                        {b.status}
                      </span>
                    </td>
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
