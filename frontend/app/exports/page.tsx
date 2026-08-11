"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import DashboardLayout from "../dashboard/layout";
import { Download, FileSpreadsheet, FileText, Printer, Users, GraduationCap, Building2 } from "lucide-react";

export default function ExportsPage() {
  const { selectedSchoolId, selectedAcademicYearId } = useSchoolStore();
  const [selectedTimetableId, setSelectedTimetableId] = useState<number | null>(null);
  const [selectedTeacherId, setSelectedTeacherId] = useState<number | undefined>();
  const [selectedClassId, setSelectedClassId] = useState<number | undefined>();

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const { data: timetables = [] } = useQuery({
    queryKey: ["timetables", selectedSchoolId, selectedAcademicYearId],
    queryFn: async () => {
      const res = await api.get(
        `/timetables?school_id=${selectedSchoolId}&academic_year_id=${selectedAcademicYearId}`
      );
      return res.data;
    },
  });

  const { data: teachers = [] } = useQuery({
    queryKey: ["teachers", selectedSchoolId],
    queryFn: async () => (await api.get(`/teachers?school_id=${selectedSchoolId}`)).data,
  });

  const { data: classes = [] } = useQuery({
    queryKey: ["classes", selectedSchoolId],
    queryFn: async () => (await api.get(`/classes?school_id=${selectedSchoolId}`)).data,
  });

  useEffect(() => {
    if (timetables.length > 0 && !selectedTimetableId) {
      setSelectedTimetableId(timetables[0].id);
    }
  }, [timetables, selectedTimetableId]);

  const openExport = (endpoint: string) => {
    if (!selectedTimetableId) return;
    const url = `${apiBaseUrl}/api/exports${endpoint}${endpoint.includes("?") ? "&" : "?"}timetable_id=${selectedTimetableId}`;
    window.open(url, "_blank");
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dışa Aktarım & Çıktı Yönetimi</h1>
          <p className="text-sm text-slate-500">Okul genel, öğretmen ve sınıf programlarının Excel ve A4 PDF çıktıları</p>
        </div>

        {/* Timetable Selector */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex-1">
            <label className="block text-xs font-semibold text-slate-600 mb-1">Aktif Ders Programı Seçin</label>
            <select
              value={selectedTimetableId || ""}
              onChange={(e) => setSelectedTimetableId(Number(e.target.value))}
              className="w-full max-w-md rounded-lg border border-slate-300 p-2.5 text-sm font-semibold text-slate-800 bg-slate-50 focus:bg-white"
            >
              {timetables.map((t: any) => (
                <option key={t.id} value={t.id}>{t.name} ({t.status})</option>
              ))}
            </select>
          </div>
        </div>

        {!selectedTimetableId ? (
          <div className="rounded-xl border border-dashed border-slate-300 p-8 text-center text-slate-400">
            Dışa aktarım yapabilmek için lütfen yukarıdan bir ders programı seçin.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {/* 1. OKUL GENEL PROGRAMI */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between space-y-4 hover:border-blue-300 transition">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-blue-50 p-3 text-blue-600">
                    <Building2 className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">Okul Genel Programı</h3>
                    <p className="text-xs text-slate-500">Tüm okul ders yerleşim matrisi</p>
                  </div>
                </div>
                <p className="text-xs text-slate-600">Tüm şube ve öğretmenlerin ortak haftalık ders programını içerir.</p>
              </div>

              <div className="space-y-2 pt-2 border-t">
                <button
                  onClick={() => openExport("/excel/school-schedule")}
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-emerald-700 transition"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  Excel Olarak İndir
                </button>
                <button
                  onClick={() => openExport("/pdf/school-schedule")}
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-red-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-red-700 transition"
                >
                  <FileText className="h-4 w-4" />
                  A4 PDF / Yazdır
                </button>
              </div>
            </div>

            {/* 2. ÖĞRETMEN PROGRAMLARI */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between space-y-4 hover:border-blue-300 transition">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-amber-50 p-3 text-amber-600">
                    <Users className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">Öğretmen Programları</h3>
                    <p className="text-xs text-slate-500">Tekil veya toplu öğretmen programları</p>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Öğretmen Seçin (İsteğe Bağlı)</label>
                  <select
                    value={selectedTeacherId || ""}
                    onChange={(e) => setSelectedTeacherId(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-xs font-medium bg-slate-50"
                  >
                    <option value="">-- Tüm Öğretmenler --</option>
                    {teachers.map((t: any) => (
                      <option key={t.id} value={t.id}>{t.full_name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t">
                <button
                  onClick={() =>
                    selectedTeacherId
                      ? openExport(`/excel/teacher-schedule?teacher_id=${selectedTeacherId}`)
                      : openExport("/excel/all-teachers")
                  }
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-emerald-700 transition"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  {selectedTeacherId ? "Seçili Öğretmen Excel" : "Tüm Öğretmenler Excel"}
                </button>
                <button
                  onClick={() =>
                    selectedTeacherId
                      ? openExport(`/pdf/teacher-schedule?teacher_id=${selectedTeacherId}`)
                      : openExport("/pdf/teacher-schedule")
                  }
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-red-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-red-700 transition"
                >
                  <FileText className="h-4 w-4" />
                  {selectedTeacherId ? "Seçili Öğretmen PDF" : "Tüm Öğretmenler PDF"}
                </button>
              </div>
            </div>

            {/* 3. SINIF PROGRAMLARI */}
            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm flex flex-col justify-between space-y-4 hover:border-blue-300 transition">
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-indigo-50 p-3 text-indigo-600">
                    <GraduationCap className="h-6 w-6" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800">Sınıf Programları</h3>
                    <p className="text-xs text-slate-500">Tekil veya toplu sınıf programları</p>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-600 mb-1">Sınıf Seçin (İsteğe Bağlı)</label>
                  <select
                    value={selectedClassId || ""}
                    onChange={(e) => setSelectedClassId(e.target.value ? Number(e.target.value) : undefined)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-xs font-medium bg-slate-50"
                  >
                    <option value="">-- Tüm Sınıflar --</option>
                    {classes.map((c: any) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t">
                <button
                  onClick={() =>
                    selectedClassId
                      ? openExport(`/excel/class-schedule?class_id=${selectedClassId}`)
                      : openExport("/excel/all-classes")
                  }
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-emerald-700 transition"
                >
                  <FileSpreadsheet className="h-4 w-4" />
                  {selectedClassId ? "Seçili Sınıf Excel" : "Tüm Sınıflar Excel"}
                </button>
                <button
                  onClick={() =>
                    selectedClassId
                      ? openExport(`/pdf/class-schedule?class_id=${selectedClassId}`)
                      : openExport("/pdf/class-schedule")
                  }
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-red-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-red-700 transition"
                >
                  <FileText className="h-4 w-4" />
                  {selectedClassId ? "Seçili Sınıf PDF" : "Tüm Sınıflar PDF"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
