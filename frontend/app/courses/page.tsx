"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import { Plus, Trash2, Edit, BookOpen, Layers, Check, X, AlertCircle, Calendar, Clock } from "lucide-react";
import DashboardLayout from "../dashboard/layout";

// Helpers for Course Distribution
const getDefaultDistribution = (hours: number): string => {
  if (hours <= 0) return "1";
  if (hours === 1) return "1";
  if (hours === 2) return "2";
  if (hours === 3) return "2+1";
  if (hours === 4) return "2+2";
  if (hours === 5) return "2+2+1";
  if (hours === 6) return "2+2+2";
  if (hours === 7) return "2+2+2+1";
  if (hours === 8) return "2+2+2+2";
  const twos = Math.floor(hours / 2);
  const ones = hours % 2;
  const arr = Array(twos).fill(2);
  if (ones > 0) arr.push(1);
  return arr.join("+");
};

const getDistributionSum = (distStr: string): number => {
  if (!distStr) return 0;
  const parts = distStr.split(/[\+\s]+/).map((p) => Number(p.trim())).filter((n) => !isNaN(n));
  return parts.reduce((a, b) => a + b, 0);
};

export default function CoursesPage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId, selectedAcademicYearId } = useSchoolStore();

  const [weeklyStructure, setWeeklyStructure] = useState("6+6+6+6+6");
  const [structureStatus, setStructureStatus] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [isSavingStructure, setIsSavingStructure] = useState(false);

  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState("");

  // Distribution options array for forms
  const [addDistributions, setAddDistributions] = useState<string[]>(["2+2+2"]);
  const [editDistributions, setEditDistributions] = useState<string[]>([]);

  const initialFormState = {
    name: "",
    code: "",
    weekly_hours: 6,
    requires_classroom: false,
    target_classes: "ALL",
  };

  const [formData, setFormData] = useState(initialFormState);
  const [selectedClassesAdd, setSelectedClassesAdd] = useState<string[]>([]);
  const [selectedClassesEdit, setSelectedClassesEdit] = useState<string[]>([]);

  const cleanCoursePayload = (raw: any, distributionsList: string[]) => {
    const validDists = distributionsList.map((d) => d.trim()).filter((d) => d !== "");
    return {
      name: raw.name,
      code: raw.code && raw.code.trim() !== "" ? raw.code.trim() : null,
      weekly_hours: Number(raw.weekly_hours) || 1,
      hour_distribution: validDists.length > 0 ? validDists.join(", ") : getDefaultDistribution(Number(raw.weekly_hours) || 1),
      requires_classroom: raw.requires_classroom ?? false,
      target_classes: raw.target_classes || "ALL",
    };
  };

  // Queries
  const { data: courses = [], isLoading } = useQuery({
    queryKey: ["courses", selectedSchoolId],
    queryFn: async () => {
      const res = await api.get(`/courses?school_id=${selectedSchoolId}`);
      return res.data;
    },
  });

  const { data: classes = [] } = useQuery({
    queryKey: ["classes", selectedSchoolId],
    queryFn: async () => {
      const res = await api.get(`/classes?school_id=${selectedSchoolId}`);
      return res.data;
    },
  });

  // Save Weekly Structure
  const handleSaveStructure = async () => {
    setIsSavingStructure(true);
    try {
      const parts = weeklyStructure.split("+").map((s) => Number(s.trim()) || 0);
      const maxPeriods = Math.max(...parts, 6);
      await api.put(`/settings/weekly_lesson_structure?school_id=${selectedSchoolId}`, {
        key: "weekly_lesson_structure",
        value: weeklyStructure,
        description: "Haftalık ders saat yapısı",
      });
      await api.post(`/timeslots/generate?school_id=${selectedSchoolId}`, {
        academic_year_id: selectedAcademicYearId || 1,
        days: parts.length || 5,
        periods_per_day: maxPeriods,
        lesson_duration_minutes: 40,
        break_duration_minutes: 10,
        start_time_str: "08:30",
      });
      setStructureStatus({ type: "success", text: "Haftalık ders yapısı ve zaman slotları kaydedildi!" });
      setTimeout(() => setStructureStatus(null), 4000);
    } catch (err: any) {
      setStructureStatus({ type: "error", text: "Ders yapısı kaydedilirken hata oluştu." });
      setTimeout(() => setStructureStatus(null), 4000);
    } finally {
      setIsSavingStructure(false);
    }
  };

  // Mutations
  const createMutation = useMutation({
    mutationFn: async (newCourse: typeof formData) => {
      const payload = cleanCoursePayload(newCourse, addDistributions);
      return api.post(`/courses?school_id=${selectedSchoolId}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses", selectedSchoolId] });
      setIsAddModalOpen(false);
      setFormData(initialFormState);
      setSelectedClassesAdd([]);
      setAddDistributions(["2+2+2"]);
      setErrorMessage("");
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === "string" ? detail : "Ders eklenemedi. Bilgileri kontrol edin.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (updatedCourse: any) => {
      const payload = cleanCoursePayload(updatedCourse, editDistributions);
      return api.put(`/courses/${updatedCourse.id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses", selectedSchoolId] });
      setIsEditModalOpen(false);
      setEditingCourse(null);
      setErrorMessage("");
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      setErrorMessage(typeof detail === "string" ? detail : "Ders güncellenemedi. Bilgileri kontrol edin.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return api.delete(`/courses/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["courses", selectedSchoolId] });
    },
  });

  const handleOpenEdit = (c: any) => {
    setErrorMessage("");
    const targetClsStr = c.target_classes || "ALL";
    const selectedList = targetClsStr === "ALL" ? [] : targetClsStr.split(",").map((s: string) => s.trim());
    setSelectedClassesEdit(selectedList);

    const wh = c.weekly_hours ?? 2;
    const existingDistStr = c.hour_distribution || getDefaultDistribution(wh);
    const dists = existingDistStr.split(",").map((s: string) => s.trim());
    setEditDistributions(dists.length > 0 ? dists : [getDefaultDistribution(wh)]);

    setEditingCourse({
      id: c.id,
      name: c.name || "",
      code: c.code || "",
      weekly_hours: wh,
      requires_classroom: c.requires_classroom ?? false,
      target_classes: targetClsStr,
    });
    setIsEditModalOpen(true);
  };

  const handleOpenAdd = () => {
    setErrorMessage("");
    setFormData(initialFormState);
    setSelectedClassesAdd([]);
    setAddDistributions([getDefaultDistribution(initialFormState.weekly_hours)]);
    setIsAddModalOpen(true);
  };

  const toggleClassSelectAdd = (className: string) => {
    let updated: string[];
    if (selectedClassesAdd.includes(className)) {
      updated = selectedClassesAdd.filter((c) => c !== className);
    } else {
      updated = [...selectedClassesAdd, className];
    }
    setSelectedClassesAdd(updated);
    setFormData({
      ...formData,
      target_classes: updated.length === 0 ? "ALL" : updated.join(","),
    });
  };

  const toggleClassSelectEdit = (className: string) => {
    let updated: string[];
    if (selectedClassesEdit.includes(className)) {
      updated = selectedClassesEdit.filter((c) => c !== className);
    } else {
      updated = [...selectedClassesEdit, className];
    }
    setSelectedClassesEdit(updated);
    setEditingCourse({
      ...editingCourse,
      target_classes: updated.length === 0 ? "ALL" : updated.join(","),
    });
  };

  // Distribution helpers
  const handleAddDistributionItem = (isEdit: boolean) => {
    const wh = isEdit ? editingCourse?.weekly_hours || 2 : formData.weekly_hours || 2;
    const def = getDefaultDistribution(wh);
    if (isEdit) {
      setEditDistributions([...editDistributions, def]);
    } else {
      setAddDistributions([...addDistributions, def]);
    }
  };

  const handleRemoveDistributionItem = (index: number, isEdit: boolean) => {
    if (isEdit) {
      if (editDistributions.length === 1) return;
      setEditDistributions(editDistributions.filter((_, i) => i !== index));
    } else {
      if (addDistributions.length === 1) return;
      setAddDistributions(addDistributions.filter((_, i) => i !== index));
    }
  };

  const handleDistributionChange = (index: number, val: string, isEdit: boolean) => {
    if (isEdit) {
      const updated = [...editDistributions];
      updated[index] = val;
      setEditDistributions(updated);
    } else {
      const updated = [...addDistributions];
      updated[index] = val;
      setAddDistributions(updated);
    }
  };

  const calculateTotalWeeklyFromStructure = (str: string) => {
    const parts = str.split("+").map((s) => Number(s.trim()) || 0);
    return parts.reduce((a, b) => a + b, 0);
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Ders Yönetimi</h1>
            <p className="text-sm text-slate-500">Müfredattaki dersleri tanımlayın, ders saat dağılımlarını ve hedef sınıfları ayarlayın</p>
          </div>
          <button
            onClick={handleOpenAdd}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition shadow-xs cursor-pointer"
          >
            <Plus className="h-4 w-4" />
            Yeni Ders Ekle
          </button>
        </div>

        {/* Haftalık Ders Saatleri Yapısı Card */}
        <div className="rounded-xl border border-blue-200 bg-linear-to-r from-blue-50 to-indigo-50 p-5 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-xl bg-blue-600 p-2.5 text-white shrink-0 shadow-xs">
              <Calendar className="h-5 w-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-800 text-sm">Haftalık Günlük Ders Saatleri Yapısı</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Haftanın her bir günü (Pzt-Cum) için ders sayısı formatı. (örn. Ortaokul için <code className="bg-white px-1 py-0.5 rounded border border-slate-200 text-blue-700 font-mono font-bold">6+6+6+6+6</code> = 30 Saat)
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
            {structureStatus && (
              <span
                className={`text-xs font-semibold px-2.5 py-1 rounded-md border ${
                  structureStatus.type === "success" ? "bg-emerald-50 text-emerald-700 border-emerald-200" : "bg-red-50 text-red-700 border-red-200"
                }`}
              >
                {structureStatus.text}
              </span>
            )}
            <div className="flex items-center gap-2 bg-white p-2 rounded-xl border border-slate-200 shadow-2xs">
              <Clock className="h-4 w-4 text-amber-500 shrink-0" />
              <input
                type="text"
                value={weeklyStructure}
                onChange={(e) => setWeeklyStructure(e.target.value)}
                placeholder="6+6+6+6+6"
                className="w-28 rounded-lg border border-slate-300 px-2.5 py-1 text-sm font-mono font-bold text-slate-800 text-center focus:border-blue-500 focus:outline-none"
              />
              <span className="text-xs font-semibold text-blue-800 bg-blue-100 px-2 py-1 rounded-md">
                {calculateTotalWeeklyFromStructure(weeklyStructure)} Saat/Hafta
              </span>
            </div>
            <button
              type="button"
              onClick={handleSaveStructure}
              disabled={isSavingStructure}
              className="flex items-center gap-1 bg-blue-600 hover:bg-blue-700 text-white px-3 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50 cursor-pointer"
            >
              {isSavingStructure ? "Kaydediliyor..." : "Yapıyı Kaydet"}
            </button>
          </div>
        </div>

        {/* Courses Table */}
        <div className="rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-200 text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-3.5">Ders Adı</th>
                <th className="px-6 py-3.5">Kodu</th>
                <th className="px-6 py-3.5">Ait Olduğu Sınıflar</th>
                <th className="px-6 py-3.5">Haftalık Saat</th>
                <th className="px-6 py-3.5">Ders Saat Dağılımı</th>
                <th className="px-6 py-3.5 text-right">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-400">Yükleniyor...</td>
                </tr>
              ) : courses.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-slate-400">Ders bulunamadı.</td>
                </tr>
              ) : (
                courses.map((c: any) => {
                  const targetStr = c.target_classes || "ALL";
                  const distStr = c.hour_distribution || "2+2+1+1";
                  const distList = distStr.split(",").map((s: string) => s.trim());

                  return (
                    <tr key={c.id} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 font-bold text-slate-800 flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-amber-500 shrink-0" />
                        {c.name}
                      </td>
                      <td className="px-6 py-4 font-mono text-xs text-slate-500">{c.code || "-"}</td>
                      <td className="px-6 py-4">
                        {targetStr === "ALL" ? (
                          <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-semibold text-blue-700 border border-blue-100">
                            Tüm Sınıflar (Genel)
                          </span>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {targetStr.split(",").map((clsName: string) => (
                              <span key={clsName} className="rounded-md bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-800 border border-amber-200">
                                {clsName.trim()}
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-4 font-medium">{c.weekly_hours} saat</td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1.5">
                          {distList.map((d: string, idx: number) => (
                            <span
                              key={idx}
                              className="rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-mono font-bold text-indigo-700 border border-indigo-200"
                            >
                              {d}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right space-x-1">
                        <button
                          onClick={() => handleOpenEdit(c)}
                          className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition"
                          title="Düzenle"
                        >
                          <Edit className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`${c.name} dersini silmek istediğinize emin misiniz?`)) {
                              deleteMutation.mutate(c.id);
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

        {/* Modal 1: Add Course */}
        {isAddModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto">
            <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h2 className="text-lg font-bold text-slate-800">Yeni Ders Ekle</h2>
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
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Ders Adı *</label>
                    <input
                      type="text"
                      required
                      placeholder="örn. Matematik"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Ders Kodu</label>
                    <input
                      type="text"
                      placeholder="MAT"
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Haftalık Saat</label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={formData.weekly_hours}
                    onChange={(e) => {
                      const newWh = Number(e.target.value) || 1;
                      setFormData({ ...formData, weekly_hours: newWh });
                      setAddDistributions([getDefaultDistribution(newWh)]);
                    }}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>

                {/* Ders Saat Dağılımı Options */}
                {(() => {
                  const addSum = getDistributionSum(addDistributions[0] || "");
                  const isAddValid = addSum === formData.weekly_hours;
                  return (
                    <div className="space-y-2 pt-2 border-t">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <label className="block text-xs font-semibold text-slate-700">Ders Saat Dağılımı Opsiyonları</label>
                            <span
                              className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${
                                isAddValid
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                  : "bg-red-50 text-red-700 border-red-200 animate-pulse"
                              }`}
                            >
                              {isAddValid ? `✔ Dağılım Uyumlu (${addSum} Saat)` : `⚠️ Dağılım Uyuşmuyor (${addSum} / ${formData.weekly_hours} Saat)`}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            Dağılım saatlerinin toplamı ({addSum}) haftalık toplam ders saatine ({formData.weekly_hours}) eşit olmalıdır. (örn. {formData.weekly_hours} saat için: <code className="font-mono text-blue-600 font-bold">{getDefaultDistribution(formData.weekly_hours)}</code>)
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleAddDistributionItem(false)}
                          className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200 transition cursor-pointer"
                        >
                          <Plus className="h-3.5 w-3.5" />
                          Ekle
                        </button>
                      </div>

                      <div className="space-y-2">
                        {addDistributions.map((distVal, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <input
                              type="text"
                              required
                              placeholder={`örn. ${getDefaultDistribution(formData.weekly_hours)}`}
                              value={distVal}
                              onChange={(e) => handleDistributionChange(idx, e.target.value, false)}
                              className={`flex-1 rounded-lg border p-2 text-sm font-mono focus:outline-none ${
                                isAddValid ? "border-slate-300 focus:border-blue-500" : "border-red-300 bg-red-50/30 text-red-900"
                              }`}
                            />
                            {addDistributions.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleRemoveDistributionItem(idx, false)}
                                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>

                      {!isAddValid && (
                        <p className="text-xs font-semibold text-red-600 bg-red-50 p-2.5 rounded-lg border border-red-200">
                          ⚠️ Ders saat dağılımı toplamı ({addSum} saat), haftalık ders saati ({formData.weekly_hours} saat) ile uyuşmuyor! Lütfen toplamı {formData.weekly_hours} olacak şekilde düzenleyin.
                        </p>
                      )}
                    </div>
                  );
                })()}

                {/* Target Classes Option */}
                <div className="space-y-2 pt-2 border-t">
                  <label className="block text-xs font-semibold text-slate-700">Dersin Ait Olduğu Sınıflar</label>
                  <div className="flex items-center gap-4 text-xs font-medium text-slate-700 mb-2">
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        name="target_type_add"
                        checked={formData.target_classes === "ALL"}
                        onChange={() => {
                          setSelectedClassesAdd([]);
                          setFormData({ ...formData, target_classes: "ALL" });
                        }}
                        className="text-blue-600"
                      />
                      <span>Tüm Sınıflar (Genel Ders)</span>
                    </label>
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        name="target_type_add"
                        checked={formData.target_classes !== "ALL"}
                        onChange={() => {
                          const firstCls = classes.length > 0 ? [classes[0].name] : [];
                          setSelectedClassesAdd(firstCls);
                          setFormData({ ...formData, target_classes: firstCls.join(",") });
                        }}
                        className="text-blue-600"
                      />
                      <span>Özel Sınıf Seçimi</span>
                    </label>
                  </div>

                  {formData.target_classes !== "ALL" && (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-2">
                      <p className="text-[11px] text-slate-500">Bu dersin okutulacağı sınıfları işaretleyin:</p>
                      <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto">
                        {classes.map((cls: any) => {
                          const isSel = selectedClassesAdd.includes(cls.name);
                          return (
                            <button
                              key={cls.id}
                              type="button"
                              onClick={() => toggleClassSelectAdd(cls.name)}
                              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                                isSel
                                  ? "bg-amber-500 text-white border-amber-600 shadow-xs"
                                  : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
                              }`}
                            >
                              {isSel && <Check className="h-3 w-3" />}
                              <span>{cls.name}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setIsAddModalOpen(false)}
                    className="rounded-lg border px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    disabled={createMutation.isPending || getDistributionSum(addDistributions[0] || "") !== formData.weekly_hours}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition disabled:opacity-40 cursor-pointer"
                  >
                    {createMutation.isPending ? "Kaydediliyor..." : "Kaydet"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal 2: Edit Course */}
        {isEditModalOpen && editingCourse && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 overflow-y-auto">
            <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b pb-3">
                <h2 className="text-lg font-bold text-slate-800">Ders Parametrelerini Düzenle</h2>
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
                  updateMutation.mutate(editingCourse);
                }}
                className="space-y-4"
              >
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Ders Adı *</label>
                    <input
                      type="text"
                      required
                      value={editingCourse.name}
                      onChange={(e) => setEditingCourse({ ...editingCourse, name: e.target.value })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-600 mb-1">Ders Kodu</label>
                    <input
                      type="text"
                      value={editingCourse.code}
                      onChange={(e) => setEditingCourse({ ...editingCourse, code: e.target.value.toUpperCase() })}
                      className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Haftalık Saat</label>
                  <input
                    type="number"
                    min={1}
                    max={20}
                    value={editingCourse.weekly_hours}
                    onChange={(e) => {
                      const newWh = Number(e.target.value) || 1;
                      setEditingCourse({ ...editingCourse, weekly_hours: newWh });
                      setEditDistributions([getDefaultDistribution(newWh)]);
                    }}
                    className="w-full rounded-lg border border-slate-300 p-2.5 text-sm focus:border-blue-500 focus:outline-none"
                  />
                </div>

                {/* Ders Saat Dağılımı Options Edit */}
                {(() => {
                  const editSum = getDistributionSum(editDistributions[0] || "");
                  const isEditValid = editSum === editingCourse.weekly_hours;
                  return (
                    <div className="space-y-2 pt-2 border-t">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <label className="block text-xs font-semibold text-slate-700">Ders Saat Dağılımı Opsiyonları</label>
                            <span
                              className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${
                                isEditValid
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                  : "bg-red-50 text-red-700 border-red-200 animate-pulse"
                              }`}
                            >
                              {isEditValid ? `✔ Dağılım Uyumlu (${editSum} Saat)` : `⚠️ Dağılım Uyuşmuyor (${editSum} / ${editingCourse.weekly_hours} Saat)`}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">
                            Dağılım saatlerinin toplamı ({editSum}) haftalık toplam ders saatine ({editingCourse.weekly_hours}) eşit olmalıdır. (örn. {editingCourse.weekly_hours} saat için: <code className="font-mono text-blue-600 font-bold">{getDefaultDistribution(editingCourse.weekly_hours)}</code>)
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleAddDistributionItem(true)}
                          className="flex items-center gap-1 text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 px-2.5 py-1 rounded-lg border border-blue-200 transition cursor-pointer"
                        >
                          <Plus className="h-3.5 w-3.5" />
                          Ekle
                        </button>
                      </div>

                      <div className="space-y-2">
                        {editDistributions.map((distVal, idx) => (
                          <div key={idx} className="flex items-center gap-2">
                            <input
                              type="text"
                              required
                              placeholder={`örn. ${getDefaultDistribution(editingCourse.weekly_hours)}`}
                              value={distVal}
                              onChange={(e) => handleDistributionChange(idx, e.target.value, true)}
                              className={`flex-1 rounded-lg border p-2 text-sm font-mono focus:outline-none ${
                                isEditValid ? "border-slate-300 focus:border-blue-500" : "border-red-300 bg-red-50/30 text-red-900"
                              }`}
                            />
                            {editDistributions.length > 1 && (
                              <button
                                type="button"
                                onClick={() => handleRemoveDistributionItem(idx, true)}
                                className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        ))}
                      </div>

                      {!isEditValid && (
                        <p className="text-xs font-semibold text-red-600 bg-red-50 p-2.5 rounded-lg border border-red-200">
                          ⚠️ Ders saat dağılımı toplamı ({editSum} saat), haftalık ders saati ({editingCourse.weekly_hours} saat) ile uyuşmuyor! Lütfen toplamı {editingCourse.weekly_hours} olacak şekilde düzenleyin.
                        </p>
                      )}
                    </div>
                  );
                })()}

                {/* Target Classes Option Edit */}
                <div className="space-y-2 pt-2 border-t">
                  <label className="block text-xs font-semibold text-slate-700">Dersin Ait Olduğu Sınıflar</label>
                  <div className="flex items-center gap-4 text-xs font-medium text-slate-700 mb-2">
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        name="target_type_edit"
                        checked={editingCourse.target_classes === "ALL"}
                        onChange={() => {
                          setSelectedClassesEdit([]);
                          setEditingCourse({ ...editingCourse, target_classes: "ALL" });
                        }}
                        className="text-blue-600"
                      />
                      <span>Tüm Sınıflar (Genel Ders)</span>
                    </label>
                    <label className="flex items-center gap-1.5 cursor-pointer">
                      <input
                        type="radio"
                        name="target_type_edit"
                        checked={editingCourse.target_classes !== "ALL"}
                        onChange={() => {
                          const firstCls = classes.length > 0 ? [classes[0].name] : [];
                          setSelectedClassesEdit(firstCls);
                          setEditingCourse({ ...editingCourse, target_classes: firstCls.join(",") });
                        }}
                        className="text-blue-600"
                      />
                      <span>Özel Sınıf Seçimi</span>
                    </label>
                  </div>

                  {editingCourse.target_classes !== "ALL" && (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 space-y-2">
                      <p className="text-[11px] text-slate-500">Bu dersin okutulacağı sınıfları işaretleyin:</p>
                      <div className="flex flex-wrap gap-2 max-h-36 overflow-y-auto">
                        {classes.map((cls: any) => {
                          const isSel = selectedClassesEdit.includes(cls.name);
                          return (
                            <button
                              key={cls.id}
                              type="button"
                              onClick={() => toggleClassSelectEdit(cls.name)}
                              className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                                isSel
                                  ? "bg-amber-500 text-white border-amber-600 shadow-xs"
                                  : "bg-white text-slate-700 border-slate-300 hover:border-slate-400"
                              }`}
                            >
                              {isSel && <Check className="h-3 w-3" />}
                              <span>{cls.name}</span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t">
                  <button
                    type="button"
                    onClick={() => setIsEditModalOpen(false)}
                    className="rounded-lg border px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    disabled={updateMutation.isPending || getDistributionSum(editDistributions[0] || "") !== editingCourse.weekly_hours}
                    className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition disabled:opacity-40 cursor-pointer"
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
