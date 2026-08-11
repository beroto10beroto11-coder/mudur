"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import { Plus, Trash2, Building2 } from "lucide-react";
import DashboardLayout from "../dashboard/layout";

export default function ClassroomsPage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId } = useSchoolStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    capacity: 30,
    room_type: "normal",
  });

  const { data: classrooms = [], isLoading } = useQuery({
    queryKey: ["classrooms", selectedSchoolId],
    queryFn: async () => {
      const res = await api.get(`/classrooms?school_id=${selectedSchoolId}`);
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (newRoom: typeof formData) => {
      return api.post(`/classrooms?school_id=${selectedSchoolId}`, newRoom);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classrooms", selectedSchoolId] });
      setIsModalOpen(false);
      setFormData({ name: "", capacity: 30, room_type: "normal" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return api.delete(`/classrooms/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classrooms", selectedSchoolId] });
    },
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Derslik Yönetimi</h1>
            <p className="text-sm text-slate-500">Derslik, laboratuvar ve spor alanlarının kapasite ve tür tanımları</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
          >
            <Plus className="h-4 w-4" />
            Yeni Derslik Ekle
          </button>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {isLoading ? (
            <p className="text-slate-400 col-span-full">Yükleniyor...</p>
          ) : classrooms.length === 0 ? (
            <p className="text-slate-400 col-span-full">Henüz derslik eklenmemiş.</p>
          ) : (
            classrooms.map((r: any) => (
              <div key={r.id} className="flex items-center justify-between rounded-xl bg-white p-5 border border-slate-200 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-indigo-50 p-3 text-indigo-600">
                    <Building2 className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-lg">{r.name}</h3>
                    <p className="text-xs text-slate-500">Kapasite: {r.capacity} • {r.room_type}</p>
                  </div>
                </div>
                <button
                  onClick={() => deleteMutation.mutate(r.id)}
                  className="text-slate-400 hover:text-red-600 transition"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))
          )}
        </div>

        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
              <h2 className="text-lg font-bold text-slate-800 mb-4">Yeni Derslik Ekle</h2>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  createMutation.mutate(formData);
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Derslik Adı</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Kapasite</label>
                    <input
                      type="number"
                      required
                      value={formData.capacity}
                      onChange={(e) => setFormData({ ...formData, capacity: Number(e.target.value) })}
                      className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Derslik Türü</label>
                    <select
                      value={formData.room_type}
                      onChange={(e) => setFormData({ ...formData, room_type: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                    >
                      <option value="normal">Normal Derslik</option>
                      <option value="lab_computer">Bilişim Laboratuvarı</option>
                      <option value="lab_science">Fen Laboratuvarı</option>
                      <option value="gym">Spor Salonu</option>
                      <option value="music">Müzik Odası</option>
                    </select>
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="rounded-lg border px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                  >
                    Kaydet
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
