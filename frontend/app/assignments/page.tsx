"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import { Plus, Trash2, Calendar } from "lucide-react";
import DashboardLayout from "../dashboard/layout";

export default function AssignmentsPage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId, selectedAcademicYearId } = useSchoolStore();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    course_id: 0,
    teacher_id: 0,
    class_id: 0,
    classroom_id: undefined as number | undefined,
    weekly_hours: 2,
  });

  const { data: assignments = [], isLoading } = useQuery({
    queryKey: ["assignments", selectedSchoolId, selectedAcademicYearId],
    queryFn: async () => {
      const res = await api.get(
        `/assignments?school_id=${selectedSchoolId}&academic_year_id=${selectedAcademicYearId}`
      );
      return res.data;
    },
  });

  const { data: teachers = [] } = useQuery({
    queryKey: ["teachers", selectedSchoolId],
    queryFn: async () => (await api.get(`/teachers?school_id=${selectedSchoolId}`)).data,
  });

  const { data: courses = [] } = useQuery({
    queryKey: ["courses", selectedSchoolId],
    queryFn: async () => (await api.get(`/courses?school_id=${selectedSchoolId}`)).data,
  });

  const { data: classes = [] } = useQuery({
    queryKey: ["classes", selectedSchoolId],
    queryFn: async () => (await api.get(`/classes?school_id=${selectedSchoolId}`)).data,
  });

  const { data: classrooms = [] } = useQuery({
    queryKey: ["classrooms", selectedSchoolId],
    queryFn: async () => (await api.get(`/classrooms?school_id=${selectedSchoolId}`)).data,
  });

  const createMutation = useMutation({
    mutationFn: async (newAsgn: typeof formData) => {
      return api.post(`/assignments?school_id=${selectedSchoolId}`, {
        ...newAsgn,
        academic_year_id: selectedAcademicYearId,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      setIsModalOpen(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return api.delete(`/assignments/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Ders Atamaları</h1>
            <p className="text-sm text-slate-500">Hangi öğretmenin hangi sınıfa kaç saat hangi dersi vereceğini eşleştirin</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
          >
            <Plus className="h-4 w-4" />
            Yeni Atama Yap
          </button>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-3">Sınıf</th>
                <th className="px-6 py-3">Ders</th>
                <th className="px-6 py-3">Öğretmen</th>
                <th className="px-6 py-3">Özel Derslik</th>
                <th className="px-6 py-3">Haftalık Saat</th>
                <th className="px-6 py-3 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-400">Yükleniyor...</td>
                </tr>
              ) : assignments.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-400">Henüz atama yapılmamış.</td>
                </tr>
              ) : (
                assignments.map((a: any) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4 font-bold text-slate-800">{a.class_group?.name}</td>
                    <td className="px-6 py-4 font-semibold text-blue-900">{a.course?.name}</td>
                    <td className="px-6 py-4">{a.teacher?.full_name}</td>
                    <td className="px-6 py-4">{a.classroom?.name || "Varsayılan Sınıf"}</td>
                    <td className="px-6 py-4">{a.weekly_hours} saat</td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => deleteMutation.mutate(a.id)}
                        className="text-red-500 hover:text-red-700 p-1 transition"
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

        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
            <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
              <h2 className="text-lg font-bold text-slate-800 mb-4">Yeni Ders Ataması</h2>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  createMutation.mutate(formData);
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Sınıf</label>
                  <select
                    required
                    onChange={(e) => setFormData({ ...formData, class_id: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                  >
                    <option value="">Sınıf Seçin</option>
                    {classes.map((c: any) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Ders</label>
                  <select
                    required
                    onChange={(e) => setFormData({ ...formData, course_id: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                  >
                    <option value="">Ders Seçin</option>
                    {courses.map((c: any) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Öğretmen</label>
                  <select
                    required
                    onChange={(e) => setFormData({ ...formData, teacher_id: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                  >
                    <option value="">Öğretmen Seçin</option>
                    {teachers.map((t: any) => (
                      <option key={t.id} value={t.id}>{t.full_name} ({t.branch})</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Özel Derslik (İsteğe Bağlı)</label>
                  <select
                    onChange={(e) => setFormData({ ...formData, classroom_id: e.target.value ? Number(e.target.value) : undefined })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                  >
                    <option value="">Varsayılan Sınıf</option>
                    {classrooms.map((r: any) => (
                      <option key={r.id} value={r.id}>{r.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Haftalık Ders Saati</label>
                  <input
                    type="number"
                    min={1}
                    value={formData.weekly_hours}
                    onChange={(e) => setFormData({ ...formData, weekly_hours: Number(e.target.value) })}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm"
                  />
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
