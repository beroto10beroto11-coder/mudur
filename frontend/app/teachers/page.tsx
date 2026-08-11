"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import { Plus, Trash2, Edit, Search, X, Mail, Phone, Clock, BookOpen, GraduationCap, Check, AlertCircle } from "lucide-react";
import DashboardLayout from "../dashboard/layout";

export default function TeachersPage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId } = useSchoolStore();
  const [search, setSearch] = useState("");

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState("");

  const initialFormState = {
    first_name: "",
    last_name: "",
    branch: "",
    email: "",
    phone: "",
    max_weekly_hours: 30,
    allowed_courses: "ALL",
    allowed_classes: "ALL",
    notes: "",
    is_active: true,
  };

  const [formData, setFormData] = useState(initialFormState);
  const [selectedCoursesAdd, setSelectedCoursesAdd] = useState<string[]>([]);
  const [selectedClassesAdd, setSelectedClassesAdd] = useState<string[]>([]);

  const [selectedCoursesEdit, setSelectedCoursesEdit] = useState<string[]>([]);
  const [selectedClassesEdit, setSelectedClassesEdit] = useState<string[]>([]);

  // Helper to clean payloads and prevent Pydantic 422 EmailStr errors on empty string
  const cleanTeacherPayload = (raw: any) => {
    const emailVal = raw.email && typeof raw.email === "string" && raw.email.trim() !== "" ? raw.email.trim() : null;
    const phoneVal = raw.phone && typeof raw.phone === "string" && raw.phone.trim() !== "" ? raw.phone.trim() : null;
    const branchVal = raw.branch && typeof raw.branch === "string" && raw.branch.trim() !== "" ? raw.branch.trim() : null;
    const notesVal = raw.notes && typeof raw.notes === "string" && raw.notes.trim() !== "" ? raw.notes.trim() : null;

    return {
      first_name: raw.first_name,
      last_name: raw.last_name,
      branch: branchVal,
      email: emailVal,
      phone: phoneVal,
      notes: notesVal,
      max_weekly_hours: Number(raw.max_weekly_hours) || 0,
      allowed_courses: raw.allowed_courses || "ALL",
      allowed_classes: raw.allowed_classes || "ALL",
      is_active: raw.is_active ?? true,
    };
  };

  // Queries
  const { data: teachers = [], isLoading } = useQuery({
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

  // Mutations
  const createMutation = useMutation({
    mutationFn: async (newTeacher: typeof formData) => {
      const payload = cleanTeacherPayload(newTeacher);
      return api.post(`/teachers?school_id=${selectedSchoolId}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers", selectedSchoolId] });
      setIsAddModalOpen(false);
      setFormData(initialFormState);
      setSelectedCoursesAdd([]);
      setSelectedClassesAdd([]);
      setErrorMessage("");
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setErrorMessage(detail.map((e: any) => `${e.loc?.slice(-1)[0]}: ${e.msg}`).join(", "));
      } else {
        setErrorMessage(detail || "Öğretmen eklenemedi. Bilgileri kontrol edin.");
      }
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (updatedTeacher: any) => {
      const payload = cleanTeacherPayload(updatedTeacher);
      return api.put(`/teachers/${updatedTeacher.id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers", selectedSchoolId] });
      setIsEditModalOpen(false);
      setEditingTeacher(null);
      setErrorMessage("");
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setErrorMessage(detail.map((e: any) => `${e.loc?.slice(-1)[0]}: ${e.msg}`).join(", "));
      } else {
        setErrorMessage(detail || "Öğretmen güncellenemedi. Bilgileri kontrol edin.");
      }
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return api.delete(`/teachers/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["teachers", selectedSchoolId] });
    },
  });

  const handleOpenEdit = (t: any) => {
    setErrorMessage("");
    const cStr = t.allowed_courses || "ALL";
    const clStr = t.allowed_classes || "ALL";

    const initialC = cStr === "ALL" ? courses.map((c: any) => c.name) : cStr.split(",").map((s: string) => s.trim());
    const initialCl = clStr === "ALL" ? classes.map((c: any) => c.name) : clStr.split(",").map((s: string) => s.trim());

    setSelectedCoursesEdit(initialC);
    setSelectedClassesEdit(initialCl);

    setEditingTeacher({
      id: t.id,
      first_name: t.first_name || "",
      last_name: t.last_name || "",
      branch: t.branch || "",
      email: t.email || "",
      phone: t.phone || "",
      max_weekly_hours: t.max_weekly_hours ?? 30,
      allowed_courses: initialC.length === courses.length ? "ALL" : initialC.join(","),
      allowed_classes: initialCl.length === classes.length ? "ALL" : initialCl.join(","),
      notes: t.notes || "",
      is_active: t.is_active ?? true,
    });
    setIsEditModalOpen(true);
  };

  const handleOpenAdd = () => {
    setErrorMessage("");
    setFormData(initialFormState);
    const allC = courses.map((c: any) => c.name);
    const allCl = classes.map((c: any) => c.name);
    setSelectedCoursesAdd(allC);
    setSelectedClassesAdd(allCl);
    setFormData({
      ...initialFormState,
      allowed_courses: "ALL",
      allowed_classes: "ALL",
    });
    setIsAddModalOpen(true);
  };

  const toggleCourseAdd = (cName: string) => {
    const updated = selectedCoursesAdd.includes(cName)
      ? selectedCoursesAdd.filter((c) => c !== cName)
      : [...selectedCoursesAdd, cName];
    setSelectedCoursesAdd(updated);
    setFormData({
      ...formData,
      allowed_courses: updated.length === courses.length ? "ALL" : updated.join(","),
    });
  };

  const toggleClassAdd = (clName: string) => {
    const updated = selectedClassesAdd.includes(clName)
      ? selectedClassesAdd.filter((c) => c !== clName)
      : [...selectedClassesAdd, clName];
    setSelectedClassesAdd(updated);
    setFormData({
      ...formData,
      allowed_classes: updated.length === classes.length ? "ALL" : updated.join(","),
    });
  };

  const toggleCourseEdit = (cName: string) => {
    const updated = selectedCoursesEdit.includes(cName)
      ? selectedCoursesEdit.filter((c) => c !== cName)
      : [...selectedCoursesEdit, cName];
    setSelectedCoursesEdit(updated);
    setEditingTeacher({
      ...editingTeacher,
      allowed_courses: updated.length === courses.length ? "ALL" : updated.join(","),
    });
  };

  const toggleClassEdit = (clName: string) => {
    const updated = selectedClassesEdit.includes(clName)
      ? selectedClassesEdit.filter((c) => c !== clName)
      : [...selectedClassesEdit, clName];
    setSelectedClassesEdit(updated);
    setEditingTeacher({
      ...editingTeacher,
      allowed_classes: updated.length === classes.length ? "ALL" : updated.join(","),
    });
  };

  const filteredTeachers = teachers.filter((t: any) =>
    t.full_name.toLowerCase().includes(search.toLowerCase()) ||
    (t.allowed_courses && t.allowed_courses.toLowerCase().includes(search.toLowerCase())) ||
    (t.allowed_classes && t.allowed_classes.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Öğretmen Yönetimi</h1>
            <p className="text-sm text-slate-500">Öğretmenlerin verebileceği dersleri, girebileceği sınıfları ve limitlerini tanımlayın</p>
          </div>
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition shadow-xs"
          >
            <Plus className="h-4 w-4" />
            Yeni Öğretmen Ekle
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Öğretmen adı, verebileceği ders veya sınıfa göre ara..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-300 pl-10 pr-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none bg-white shadow-xs"
          />
        </div>

        {/* Table */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-3.5">Ad Soyad</th>
                <th className="px-6 py-3.5">Verebileceği Dersler</th>
                <th className="px-6 py-3.5">Girebileceği Sınıflar</th>
                <th className="px-6 py-3.5">İletişim & Limitler</th>
                <th className="px-6 py-3.5 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Yükleniyor...</td>
                </tr>
              ) : filteredTeachers.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">Öğretmen bulunamadı.</td>
                </tr>
              ) : (
                filteredTeachers.map((t: any) => {
                  const cStr = t.allowed_courses || "ALL";
                  const clStr = t.allowed_classes || "ALL";

                  return (
                    <tr key={t.id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 font-bold text-slate-800">
                        {t.full_name}
                      </td>

                      {/* Courses */}
                      <td className="px-6 py-4">
                        {cStr === "ALL" ? (
                          <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 border border-blue-100">
                            Tüm Dersler
                          </span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {cStr.split(",").map((cName: string) => (
                              <span key={cName} className="rounded-md bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-800 border border-blue-200 flex items-center gap-1">
                                <BookOpen className="h-3 w-3 text-blue-600" />
                                {cName.trim()}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>

                      {/* Classes */}
                      <td className="px-6 py-4">
                        {clStr === "ALL" ? (
                          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700 border border-emerald-100">
                            Tüm Sınıflar
                          </span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {clStr.split(",").map((clsName: string) => (
                              <span key={clsName} className="rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-800 border border-emerald-200 flex items-center gap-1">
                                <GraduationCap className="h-3 w-3 text-emerald-600" />
                                {clsName.trim()}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>

                      {/* Contact & Limits */}
                      <td className="px-6 py-4 text-xs space-y-1">
                        <div className="flex items-center gap-2 text-slate-700 font-medium">
                          <Clock className="h-3.5 w-3.5 text-amber-500" />
                          <span>Haftalık Max: <strong>{t.max_weekly_hours > 0 ? `${t.max_weekly_hours} Saat` : "Sınırsız"}</strong></span>
                        </div>
                        {(t.email || t.phone) && (
                          <div className="text-slate-400 font-mono text-[11px]">
                            {t.email} {t.phone ? `(${t.phone})` : ""}
                          </div>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right space-x-1">
                        <button
                          onClick={() => handleOpenEdit(t)}
                          className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                          title="Düzenle"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`${t.full_name} isimli öğretmeni silmek istediğinize emin misiniz?`)) {
                              deleteMutation.mutate(t.id);
                            }
                          }}
                          className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                          title="Sil"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Modal 1: Add Teacher */}
        {isAddModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto">
            <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h2 className="text-lg font-bold text-slate-800">Yeni Öğretmen Ekle</h2>
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
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Ad *</label>
                    <input
                      type="text"
                      required
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Soyad *</label>
                    <input
                      type="text"
                      required
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                {/* Courses Selection */}
                <div className="space-y-2 border-t pt-3">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold text-slate-700">Verebileceği Dersler (Branşlar)</label>
                    <div className="space-x-2 text-[11px]">
                      <button
                        type="button"
                        onClick={() => {
                          const allC = courses.map((c: any) => c.name);
                          setSelectedCoursesAdd(allC);
                          setFormData({ ...formData, allowed_courses: "ALL" });
                        }}
                        className="text-blue-600 hover:underline font-semibold"
                      >
                        Tümünü Seç
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCoursesAdd([]);
                          setFormData({ ...formData, allowed_courses: "" });
                        }}
                        className="text-slate-400 hover:underline"
                      >
                        Temizle
                      </button>
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto">
                      {courses.map((c: any) => {
                        const isSel = selectedCoursesAdd.includes(c.name);
                        return (
                          <button
                            key={c.id}
                            type="button"
                            onClick={() => toggleCourseAdd(c.name)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                              isSel
                                ? "bg-blue-600 text-white border-blue-700 shadow-xs"
                                : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
                            }`}
                          >
                            {isSel && <Check className="h-3.5 w-3.5 shrink-0" />}
                            <span>{c.name}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Classes Selection */}
                <div className="space-y-2 border-t pt-3">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold text-slate-700">Girebileceği Sınıflar</label>
                    <div className="space-x-2 text-[11px]">
                      <button
                        type="button"
                        onClick={() => {
                          const allCl = classes.map((c: any) => c.name);
                          setSelectedClassesAdd(allCl);
                          setFormData({ ...formData, allowed_classes: "ALL" });
                        }}
                        className="text-emerald-600 hover:underline font-semibold"
                      >
                        Tümünü Seç
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedClassesAdd([]);
                          setFormData({ ...formData, allowed_classes: "" });
                        }}
                        className="text-slate-400 hover:underline"
                      >
                        Temizle
                      </button>
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto">
                      {classes.map((cls: any) => {
                        const isSel = selectedClassesAdd.includes(cls.name);
                        return (
                          <button
                            key={cls.id}
                            type="button"
                            onClick={() => toggleClassAdd(cls.name)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                              isSel
                                ? "bg-emerald-600 text-white border-emerald-700 shadow-xs"
                                : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
                            }`}
                          >
                            {isSel && <Check className="h-3.5 w-3.5 shrink-0" />}
                            <span>{cls.name}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 border-t pt-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">E-posta</label>
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Telefon</label>
                    <input
                      type="text"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Haftalık Max Ders Saati</label>
                  <input
                    type="number"
                    min={0}
                    max={50}
                    value={formData.max_weekly_hours}
                    onChange={(e) => setFormData({ ...formData, max_weekly_hours: Number(e.target.value) })}
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

        {/* Modal 2: Edit Teacher */}
        {isEditModalOpen && editingTeacher && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto">
            <div className="w-full max-w-xl rounded-2xl bg-white p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h2 className="text-lg font-bold text-slate-800">Öğretmen Parametrelerini Düzenle</h2>
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
                  updateMutation.mutate(editingTeacher);
                }}
                className="space-y-4"
              >
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Ad *</label>
                    <input
                      type="text"
                      required
                      value={editingTeacher.first_name}
                      onChange={(e) => setEditingTeacher({ ...editingTeacher, first_name: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Soyad *</label>
                    <input
                      type="text"
                      required
                      value={editingTeacher.last_name}
                      onChange={(e) => setEditingTeacher({ ...editingTeacher, last_name: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                {/* Courses Selection Edit */}
                <div className="space-y-2 border-t pt-3">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold text-slate-700">Verebileceği Dersler (Branşlar)</label>
                    <div className="space-x-2 text-[11px]">
                      <button
                        type="button"
                        onClick={() => {
                          const allC = courses.map((c: any) => c.name);
                          setSelectedCoursesEdit(allC);
                          setEditingTeacher({ ...editingTeacher, allowed_courses: "ALL" });
                        }}
                        className="text-blue-600 hover:underline font-semibold"
                      >
                        Tümünü Seç
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedCoursesEdit([]);
                          setEditingTeacher({ ...editingTeacher, allowed_courses: "" });
                        }}
                        className="text-slate-400 hover:underline"
                      >
                        Temizle
                      </button>
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto">
                      {courses.map((c: any) => {
                        const isSel = selectedCoursesEdit.includes(c.name);
                        return (
                          <button
                            key={c.id}
                            type="button"
                            onClick={() => toggleCourseEdit(c.name)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                              isSel
                                ? "bg-blue-600 text-white border-blue-700 shadow-xs"
                                : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
                            }`}
                          >
                            {isSel && <Check className="h-3.5 w-3.5 shrink-0" />}
                            <span>{c.name}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                {/* Classes Selection Edit */}
                <div className="space-y-2 border-t pt-3">
                  <div className="flex items-center justify-between">
                    <label className="block text-xs font-semibold text-slate-700">Girebileceği Sınıflar</label>
                    <div className="space-x-2 text-[11px]">
                      <button
                        type="button"
                        onClick={() => {
                          const allCl = classes.map((c: any) => c.name);
                          setSelectedClassesEdit(allCl);
                          setEditingTeacher({ ...editingTeacher, allowed_classes: "ALL" });
                        }}
                        className="text-emerald-600 hover:underline font-semibold"
                      >
                        Tümünü Seç
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedClassesEdit([]);
                          setEditingTeacher({ ...editingTeacher, allowed_classes: "" });
                        }}
                        className="text-slate-400 hover:underline"
                      >
                        Temizle
                      </button>
                    </div>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                    <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto">
                      {classes.map((cls: any) => {
                        const isSel = selectedClassesEdit.includes(cls.name);
                        return (
                          <button
                            key={cls.id}
                            type="button"
                            onClick={() => toggleClassEdit(cls.name)}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                              isSel
                                ? "bg-emerald-600 text-white border-emerald-700 shadow-xs"
                                : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
                            }`}
                          >
                            {isSel && <Check className="h-3.5 w-3.5 shrink-0" />}
                            <span>{cls.name}</span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 border-t pt-3">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">E-posta</label>
                    <input
                      type="email"
                      value={editingTeacher.email}
                      onChange={(e) => setEditingTeacher({ ...editingTeacher, email: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Telefon</label>
                    <input
                      type="text"
                      value={editingTeacher.phone}
                      onChange={(e) => setEditingTeacher({ ...editingTeacher, phone: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Haftalık Max Ders Saati</label>
                  <input
                    type="number"
                    min={0}
                    max={50}
                    value={editingTeacher.max_weekly_hours}
                    onChange={(e) => setEditingTeacher({ ...editingTeacher, max_weekly_hours: Number(e.target.value) })}
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
