"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import DashboardLayout from "../dashboard/layout";
import { Clock, RefreshCw } from "lucide-react";

export default function TimeSlotsPage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId, selectedAcademicYearId } = useSchoolStore();

  const { data: slots = [], isLoading } = useQuery({
    queryKey: ["timeslots", selectedAcademicYearId],
    queryFn: async () => {
      const res = await api.get(`/timeslots?academic_year_id=${selectedAcademicYearId}`);
      return res.data;
    },
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      return api.post(`/timeslots/generate?school_id=${selectedSchoolId}`, {
        academic_year_id: selectedAcademicYearId,
        days: 5,
        periods_per_day: 8,
        start_time_str: "08:30",
        lesson_duration_minutes: 40,
        break_duration_minutes: 10,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["timeslots"] });
    },
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Zaman Slotları (Ders Saatleri)</h1>
            <p className="text-sm text-slate-500">Günlük 8 ders saati ve teneffüs zaman tanımlamaları</p>
          </div>
          <button
            onClick={() => generateMutation.mutate()}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
          >
            <RefreshCw className="h-4 w-4" />
            Varsayılan Saatleri Oluştur
          </button>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-3">Gün</th>
                <th className="px-6 py-3">Ders Saati</th>
                <th className="px-6 py-3">Başlangıç</th>
                <th className="px-6 py-3">Bitiş</th>
                <th className="px-6 py-3">Durum</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Yükleniyor...</td>
                </tr>
              ) : slots.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Henüz zaman slotu oluşturulmamış. "Varsayılan Saatleri Oluştur" butonuna basın.</td>
                </tr>
              ) : (
                slots.map((s: any) => (
                  <tr key={s.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-bold text-slate-800">{s.day_name}</td>
                    <td className="px-6 py-4">{s.period}. Ders</td>
                    <td className="px-6 py-4 font-mono">{s.start_time}</td>
                    <td className="px-6 py-4 font-mono">{s.end_time}</td>
                    <td className="px-6 py-4">
                      <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700">Aktif</span>
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
