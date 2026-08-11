"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import DashboardLayout from "../dashboard/layout";
import { Settings as SettingsIcon, Save } from "lucide-react";

export default function SettingsPage() {
  const { selectedSchoolId } = useSchoolStore();

  const { data: settings = [], isLoading } = useQuery({
    queryKey: ["settings", selectedSchoolId],
    queryFn: async () => (await api.get(`/settings?school_id=${selectedSchoolId}`)).data,
  });

  return (
    <DashboardLayout>
      <div className="max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Sistem Ayarları</h1>
          <p className="text-sm text-slate-500">Okul genel parametreleri ve solver yapılandırma ayarları</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-6">
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Okul Adı</label>
              <input
                type="text"
                defaultValue="Atatürk Anadolu Lisesi"
                className="w-full rounded-lg border border-slate-300 p-2.5 text-sm font-medium"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Solver Maksimum Süre (Saniye)</label>
                <input
                  type="number"
                  defaultValue={300}
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-sm font-medium"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Zaman Slotu Sayısı (Günlük)</label>
                <input
                  type="number"
                  defaultValue={8}
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-sm font-medium"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t">
            <button
              onClick={() => alert("Ayarlar güncellendi.")}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition"
            >
              <Save className="h-4 w-4" />
              Ayarları Kaydet
            </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
