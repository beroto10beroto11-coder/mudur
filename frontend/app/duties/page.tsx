"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import DashboardLayout from "../dashboard/layout";
import { ShieldCheck, Play, Edit, Trash2, Plus, Printer, MapPin, Save, X, Check } from "lucide-react";

export default function DutiesPage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId, selectedAcademicYearId } = useSchoolStore();

  // Modals state
  const [isLocationsModalOpen, setIsLocationsModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingDuty, setEditingDuty] = useState<any>(null);
  const [newLocationInput, setNewLocationInput] = useState("");

  // Queries
  const { data: duties = [], isLoading } = useQuery({
    queryKey: ["duties", selectedSchoolId, selectedAcademicYearId],
    queryFn: async () => {
      const res = await api.get(
        `/duties?school_id=${selectedSchoolId}&academic_year_id=${selectedAcademicYearId}`
      );
      return res.data;
    },
  });

  const { data: teachers = [] } = useQuery({
    queryKey: ["teachers", selectedSchoolId],
    queryFn: async () => (await api.get(`/teachers?school_id=${selectedSchoolId}`)).data,
  });

  const { data: dutyLocations = ["1. Kat Koridor", "2. Kat Koridor", "Bahçe", "Kantin Katı", "Spor Salonu"] } = useQuery({
    queryKey: ["duty-locations", selectedSchoolId],
    queryFn: async () => (await api.get(`/duties/locations?school_id=${selectedSchoolId}`)).data,
  });

  // Mutations
  const saveLocationsMutation = useMutation({
    mutationFn: async (locations: string[]) => {
      return api.post(`/duties/locations?school_id=${selectedSchoolId}`, { locations });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["duty-locations"] });
    },
  });

  const autoAssignMutation = useMutation({
    mutationFn: async () => {
      return api.post(`/duties/auto-assign?school_id=${selectedSchoolId}`, {
        academic_year_id: selectedAcademicYearId,
        days: [0, 1, 2, 3, 4],
        locations: dutyLocations,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["duties"] });
    },
  });

  const updateDutyMutation = useMutation({
    mutationFn: async (updatedData: { id: number; teacher_id: number; day: number; location: string }) => {
      return api.put(`/duties/${updatedData.id}`, {
        teacher_id: updatedData.teacher_id,
        day: updatedData.day,
        location: updatedData.location,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["duties"] });
      setIsEditModalOpen(false);
      setEditingDuty(null);
    },
  });

  const deleteDutyMutation = useMutation({
    mutationFn: async (dutyId: number) => {
      return api.delete(`/duties/${dutyId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["duties"] });
    },
  });

  const days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"];

  const handleAddLocation = () => {
    if (!newLocationInput.trim()) return;
    const updated = [...dutyLocations, newLocationInput.trim()];
    saveLocationsMutation.mutate(updated);
    setNewLocationInput("");
  };

  const handleRemoveLocation = (locToRemove: string) => {
    const updated = dutyLocations.filter((l: string) => l !== locToRemove);
    saveLocationsMutation.mutate(updated);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 print:p-0 print:space-y-4">
        {/* Header Actions */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 print:hidden">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Nöbet Sistemi</h1>
            <p className="text-sm text-slate-500">Öğretmenlerin nöbet yerleri ve dengeli otomatik dağıtımı</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => setIsLocationsModalOpen(true)}
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-xs"
            >
              <MapPin className="h-3.5 w-3.5 text-blue-600" />
              Nöbet Yerlerini Yönet
            </button>

            <button
              onClick={handlePrint}
              className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-xs"
            >
              <Printer className="h-3.5 w-3.5 text-slate-600" />
              Yazdır / PDF
            </button>

            <button
              onClick={() => autoAssignMutation.mutate()}
              disabled={autoAssignMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-700 transition disabled:opacity-50 shadow-xs"
            >
              <Play className="h-3.5 w-3.5" />
              {autoAssignMutation.isPending ? "Dağıtılıyor..." : "Otomatik Nöbet Dağıt"}
            </button>
          </div>
        </div>

        {/* Print Header */}
        <div className="hidden print:block text-center border-b pb-4 mb-4">
          <h1 className="text-xl font-bold uppercase text-slate-900">Atatürk Anadolu Lisesi</h1>
          <h2 className="text-sm font-semibold text-slate-700">Haftalık Öğretmen Nöbet Çizelgesi</h2>
        </div>

        {/* Duty Table */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden print:border-none print:shadow-none">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-3">Öğretmen</th>
                <th className="px-6 py-3">Gün</th>
                <th className="px-6 py-3">Nöbet Yeri</th>
                <th className="px-6 py-3">Tür</th>
                <th className="px-6 py-3 text-right print:hidden">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Yükleniyor...</td>
                </tr>
              ) : duties.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                    Henüz nöbet ataması yapılmamış. "Otomatik Nöbet Dağıt" butonuna basın veya nöbet yerlerini düzenleyin.
                  </td>
                </tr>
              ) : (
                duties.map((d: any) => (
                  <tr key={d.id} className="hover:bg-slate-50">
                    <td className="px-6 py-3.5 font-bold text-slate-800 flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0 print:hidden" />
                      {d.teacher_name}
                    </td>
                    <td className="px-6 py-3.5">{days[d.day] || d.day}</td>
                    <td className="px-6 py-3.5 font-semibold text-blue-900">{d.location}</td>
                    <td className="px-6 py-3.5">
                      <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
                        d.automatic
                          ? "bg-blue-50 text-blue-700 border border-blue-100"
                          : "bg-amber-50 text-amber-700 border border-amber-100"
                      }`}>
                        {d.automatic ? "Otomatik" : "Manuel"}
                      </span>
                    </td>
                    <td className="px-6 py-3.5 text-right space-x-1 print:hidden">
                      <button
                        onClick={() => {
                          setEditingDuty(d);
                          setIsEditModalOpen(true);
                        }}
                        className="p-1 text-slate-400 hover:text-blue-600 transition rounded"
                        title="Düzenle"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => deleteDutyMutation.mutate(d.id)}
                        className="p-1 text-slate-400 hover:text-red-600 transition rounded"
                        title="Sil"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Modal 1: Manage Duty Locations */}
        {isLocationsModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h3 className="font-bold text-slate-800 text-lg">Nöbet Yerlerini Yönet</h3>
                <button onClick={() => setIsLocationsModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-600">Yeni Nöbet Yeri Ekle</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="örn. Spor Salonu"
                    value={newLocationInput}
                    onChange={(e) => setNewLocationInput(e.target.value)}
                    className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    onClick={handleAddLocation}
                    className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-700"
                  >
                    <Plus className="h-4 w-4" /> Ekle
                  </button>
                </div>
              </div>

              <div className="space-y-2 pt-2">
                <label className="block text-xs font-semibold text-slate-600">Tanımlı Nöbet Yerleri</label>
                <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-1">
                  {dutyLocations.map((loc: string) => (
                    <span
                      key={loc}
                      className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700 border"
                    >
                      {loc}
                      <button
                        onClick={() => handleRemoveLocation(loc)}
                        className="text-slate-400 hover:text-red-600 transition"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t">
                <button
                  onClick={() => setIsLocationsModalOpen(false)}
                  className="rounded-lg bg-slate-100 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200"
                >
                  Kapat
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal 2: Edit Single Duty Row */}
        {isEditModalOpen && editingDuty && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h3 className="font-bold text-slate-800 text-lg">Nöbet Kaydını Düzenle</h3>
                <button onClick={() => setIsEditModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="h-5 w-5" />
                </button>
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  updateDutyMutation.mutate(editingDuty);
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Öğretmen</label>
                  <select
                    value={editingDuty.teacher_id}
                    onChange={(e) => setEditingDuty({ ...editingDuty, teacher_id: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-sm"
                  >
                    {teachers.map((t: any) => (
                      <option key={t.id} value={t.id}>{t.full_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Gün</label>
                  <select
                    value={editingDuty.day}
                    onChange={(e) => setEditingDuty({ ...editingDuty, day: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-sm"
                  >
                    {days.map((dName, idx) => (
                      <option key={dName} value={idx}>{dName}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Nöbet Yeri</label>
                  <input
                    type="text"
                    value={editingDuty.location}
                    onChange={(e) => setEditingDuty({ ...editingDuty, location: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-sm"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setIsEditModalOpen(false)}
                    className="rounded-lg border px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700"
                  >
                    Güncelle & Kaydet
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
