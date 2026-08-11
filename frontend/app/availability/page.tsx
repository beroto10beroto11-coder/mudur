"use client";

import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import DashboardLayout from "../dashboard/layout";
import { Check, X, Save, Loader2 } from "lucide-react";

export default function AvailabilityPage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId, selectedAcademicYearId } = useSchoolStore();
  const [selectedTeacherId, setSelectedTeacherId] = useState<number | null>(null);
  const [gridState, setGridState] = useState<Record<string, boolean>>({});
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  const { data: teachers = [] } = useQuery({
    queryKey: ["teachers", selectedSchoolId],
    queryFn: async () => (await api.get(`/teachers?school_id=${selectedSchoolId}`)).data,
  });

  const { data: availability = [] } = useQuery({
    queryKey: ["availability", selectedTeacherId, selectedAcademicYearId],
    queryFn: async () => {
      if (!selectedTeacherId) return [];
      const res = await api.get(
        `/availability/teacher/${selectedTeacherId}?academic_year_id=${selectedAcademicYearId}`
      );
      return res.data;
    },
    enabled: !!selectedTeacherId,
  });

  // Warn user before leaving page/switching tab if unsaved changes exist
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = "Müsaitlik matrisinde kaydedilmemiş değişiklikler var. Ayrılmak istediğinize emin misiniz?";
        return e.returnValue;
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasUnsavedChanges]);

  // Sync gridState when availability data is loaded or teacher changes (when no unsaved changes)
  useEffect(() => {
    if (!selectedTeacherId) {
      setGridState({});
      setHasUnsavedChanges(false);
      return;
    }
    if (!hasUnsavedChanges) {
      const initialGridState: Record<string, boolean> = {};
      for (let d = 0; d < 5; d++) {
        for (let p = 1; p <= 8; p++) {
          const key = `${d}-${p}`;
          const record = availability.find((a: any) => a.day === d && a.period === p);
          initialGridState[key] = record ? record.available : true;
        }
      }
      setGridState(initialGridState);
    }
  }, [selectedTeacherId, availability]);

  const isSlotAvailable = (d: number, p: number) => {
    const key = `${d}-${p}`;
    if (gridState[key] !== undefined) return gridState[key];
    const record = availability.find((a: any) => a.day === d && a.period === p);
    return record ? record.available : true;
  };

  const toggleSlot = (d: number, p: number) => {
    const key = `${d}-${p}`;
    const currentAvail = isSlotAvailable(d, p);
    setGridState((prev) => ({
      ...prev,
      [key]: !currentAvail,
    }));
    setHasUnsavedChanges(true);
  };

  const saveMutation = useMutation({
    mutationFn: async () => {
      const unavailabilities: any[] = [];
      for (let d = 0; d < 5; d++) {
        for (let p = 1; p <= 8; p++) {
          const isAvail = isSlotAvailable(d, p);
          if (!isAvail) {
            unavailabilities.push({ day: d, period: p, available: false });
          }
        }
      }

      return api.post("/availability/batch", {
        teacher_id: selectedTeacherId,
        academic_year_id: selectedAcademicYearId,
        unavailabilities,
      });
    },
    onSuccess: () => {
      setHasUnsavedChanges(false);
      queryClient.invalidateQueries({ queryKey: ["availability"] });
    },
  });

  const days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"];
  const periods = [1, 2, 3, 4, 5, 6, 7, 8];

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Öğretmen Müsaitlik Matrisi</h1>
            <p className="text-sm text-slate-500">Öğretmenlerin izinli/kapalı olduğu saatleri kırmızı işaretleyin</p>
          </div>

          <div className="flex items-center gap-2">
            {hasUnsavedChanges && (
              <span className="flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-800">
                <span className="h-2 w-2 rounded-full bg-amber-500 animate-ping"></span>
                Değişiklik Var
              </span>
            )}

            <button
              onClick={() => saveMutation.mutate()}
              disabled={!selectedTeacherId || !hasUnsavedChanges || saveMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition disabled:opacity-40 shadow-xs"
            >
              {saveMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Save className="h-3.5 w-3.5" />
              )}
              {saveMutation.isPending ? "Kaydediliyor..." : "Müsaitlikleri Kaydet"}
            </button>
          </div>
        </div>

        <div className="w-full max-w-xs">
          <label className="block text-xs font-semibold text-slate-600 mb-1">Öğretmen Seçin</label>
          <select
            value={selectedTeacherId || ""}
            onChange={(e) => {
              if (hasUnsavedChanges && !confirm("Kaydedilmemiş değişiklikler kaybolacak. Devam etmek istiyor musunuz?")) {
                return;
              }
              setSelectedTeacherId(Number(e.target.value));
              setGridState({});
              setHasUnsavedChanges(false);
            }}
            className="w-full rounded-lg border border-slate-300 p-2.5 text-sm font-medium bg-white"
          >
            <option value="">-- Öğretmen Seçin --</option>
            {teachers.map((t: any) => (
              <option key={t.id} value={t.id}>{t.full_name} ({t.branch})</option>
            ))}
          </select>
        </div>

        {selectedTeacherId ? (
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm overflow-x-auto">
            <table className="w-full border-collapse text-center text-sm">
              <thead>
                <tr className="bg-slate-100 text-slate-700 font-bold uppercase text-xs">
                  <th className="border p-3">Ders Saati</th>
                  {days.map((d) => (
                    <th key={d} className="border p-3">{d}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {periods.map((p) => (
                  <tr key={p}>
                    <td className="border font-bold bg-slate-50 text-slate-600 w-24 p-3">{p}. Ders</td>
                    {days.map((_, dIdx) => {
                      const avail = isSlotAvailable(dIdx, p);
                      return (
                        <td
                          key={dIdx}
                          onClick={() => toggleSlot(dIdx, p)}
                          className={`border p-4 cursor-pointer transition font-bold select-none ${
                            avail
                              ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                              : "bg-red-100 text-red-700 hover:bg-red-200"
                          }`}
                        >
                          <div className="flex items-center justify-center gap-1">
                            {avail ? <Check className="h-4 w-4" /> : <X className="h-4 w-4" />}
                            <span>{avail ? "Uygun" : "Kapalı"}</span>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-slate-300 p-12 text-center text-slate-400">
            Müsaitlik matrisini görüntülemek için lütfen bir öğretmen seçin.
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
