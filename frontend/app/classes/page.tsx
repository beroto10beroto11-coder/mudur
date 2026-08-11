"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import { Plus, Trash2, Edit, GraduationCap, Clock, Users, X, AlertCircle } from "lucide-react";
import DashboardLayout from "../dashboard/layout";

export default function ClassesPage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId } = useSchoolStore();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingClass, setEditingClass] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const initialFormState = {
    grade: 9,
    section: "A",
    notes: "",
  };

  const [formData, setFormData] = useState(initialFormState);

  const cleanClassPayload = (raw: any) => {
    return {
      grade: Number(raw.grade) || 9,
      section: String(raw.section).trim().toUpperCase(),
      name: `${raw.grade}/${String(raw.section).trim().toUpperCase()}`,
      notes: raw.notes && raw.notes.trim() !== "" ? raw.notes.trim() : null,
    };
  };

  const { data: classes = [], isLoading } = useQuery({
    queryKey: ["classes", selectedSchoolId],
    queryFn: async () => {
      const res = await api.get(`/classes?school_id=${selectedSchoolId}`);
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (newClass: typeof formData) => {
      const payload = cleanClassPayload(newClass);
      return api.post(`/classes?school_id=${selectedSchoolId}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes", selectedSchoolId] });
      setIsAddModalOpen(false);
      setFormData(initialFormState);
      setErrorMessage("");
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === "string" ? detail : "Sınıf eklenemedi. Bilgileri kontrol edin.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (updatedClass: any) => {
      const payload = cleanClassPayload(updatedClass);
      return api.put(`/classes/${updatedClass.id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes", selectedSchoolId] });
      setIsEditModalOpen(false);
      setEditingClass(null);
      setErrorMessage("");
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === "string" ? detail : "Sınıf güncellenemedi. Bilgileri kontrol edin.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return api.delete(`/classes/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classes", selectedSchoolId] });
    },
  });

  const handleOpenEdit = (c: any) => {
    setErrorMessage("");
    setEditingClass({
      id: c.id,
      grade: c.grade || 9,
      section: c.section || "A",
      notes: c.notes || "",
    });
    setIsEditModalOpen(true);
  };

  const handleOpenAdd = () => {
    setErrorMessage("");
    setFormData(initialFormState);
    setIsAddModalOpen(true);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Sınıf Yönetimi</h1>
            <p className="text-sm text-slate-500">Okuldaki şube ve sınıf parametrelerini yönetin</p>
          </div>
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition shadow-xs"
          >
            <Plus className="h-4 w-4" />
            Yeni Sınıf Ekle
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading ? (
            <p className="text-slate-400 col-span-full">Yükleniyor...</p>
          ) : classes.length === 0 ? (
            <p className="text-slate-400 col-span-full">Henüz sınıf eklenmemiş.</p>
          ) : (
            classes.map((c: any) => (
              <div key={c.id} className="flex items-center justify-between rounded-xl bg-white p-5 border border-slate-200 shadow-sm hover:border-blue-300 transition">
                <div className="flex items-center gap-3.5">
                  <div className="rounded-xl bg-emerald-50 p-3 text-emerald-600 shrink-0">
                    <GraduationCap className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-lg">{c.name}</h3>
                    {c.notes && <p className="text-xs text-slate-400 mt-0.5">{c.notes}</p>}
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleOpenEdit(c)}
                    className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                    title="Düzenle"
                  >
                    <Edit className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`${c.name} sınıfını silmek istediğinize emin misiniz?`)) {
                        deleteMutation.mutate(c.id);
                      }
                    }}
                    className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                    title="Sil"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Modal 1: Add Class */}
        {isAddModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h2 className="text-lg font-bold text-slate-800">Yeni Sınıf Ekle</h2>
                <button onClick={() => setIsAddModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="h-5 w-5" />
                </button>
              </div>

              {errorMessage && (
                <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs font-semibold text-red-700">
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  createMutation.mutate(formData);
                }}
                className="space-y-4"
              >
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Sınıf Seviyesi (9, 10...)</label>
                    <input
                      type="number"
                      required
                      min={1}
                      max={12}
                      value={formData.grade}
                      onChange={(e) => setFormData({ ...formData, grade: Number(e.target.value) })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Şube (A, B, C...)</label>
                    <input
                      type="text"
                      required
                      value={formData.section}
                      onChange={(e) => setFormData({ ...formData, section: e.target.value.toUpperCase() })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Notlar</label>
                  <input
                    type="text"
                    placeholder="örn. Şube notu veya açıklaması..."
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="rounded-lg border px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition disabled:opacity-50"
                  >
                    {createMutation.isPending ? "Kaydediliyor..." : "Kaydet"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal 2: Edit Class */}
        {isEditModalOpen && editingClass && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h2 className="text-lg font-bold text-slate-800">Sınıf Parametrelerini Düzenle</h2>
                <button onClick={() => setIsEditModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X className="h-5 w-5" />
                </button>
              </div>

              {errorMessage && (
                <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-xs font-semibold text-red-700">
                  <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
                  <span>{errorMessage}</span>
                </div>
              )}

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  updateMutation.mutate(editingClass);
                }}
                className="space-y-4"
              >
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Sınıf Seviyesi (9, 10...)</label>
                    <input
                      type="number"
                      required
                      min={1}
                      max={12}
                      value={editingClass.grade}
                      onChange={(e) => setEditingClass({ ...editingClass, grade: Number(e.target.value) })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Şube (A, B, C...)</label>
                    <input
                      type="text"
                      required
                      value={editingClass.section}
                      onChange={(e) => setEditingClass({ ...editingClass, section: e.target.value.toUpperCase() })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Notlar</label>
                  <input
                    type="text"
                    value={editingClass.notes}
                    onChange={(e) => setEditingClass({ ...editingClass, notes: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
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
                    disabled={updateMutation.isPending}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition disabled:opacity-50"
                  >
                    {updateMutation.isPending ? "Güncelleniyor..." : "Güncelle & Kaydet"}
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
