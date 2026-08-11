"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import DashboardLayout from "../dashboard/layout";
import { Upload, FileSpreadsheet, CheckCircle2, AlertCircle, Download, Users, GraduationCap, BookOpen, Building2, Link as LinkIcon } from "lucide-react";

type ImportCategory = "teachers" | "classes" | "courses" | "classrooms" | "assignments";

interface CategoryMeta {
  id: ImportCategory;
  title: string;
  icon: any;
  endpoint: string;
  requiredCols: string;
  description: string;
}

export default function ImportsPage() {
  const { selectedSchoolId, selectedAcademicYearId } = useSchoolStore();
  const [activeTab, setActiveTab] = useState<ImportCategory>("teachers");
  const [file, setFile] = useState<File | null>(null);
  const [statusMessage, setStatusMessage] = useState<{ type: string; text: string; skipped?: string[] }>({ type: "", text: "" });
  const [loading, setLoading] = useState(false);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const categories: CategoryMeta[] = [
    {
      id: "teachers",
      title: "Öğretmenler",
      icon: Users,
      endpoint: "/imports/teachers",
      requiredCols: "Ad, Soyad (Opsiyonel: Branş, E-posta, Telefon, Günlük Max Ders)",
      description: "Okul öğretmen kadrosunu Excel sayfasından içe aktarın.",
    },
    {
      id: "classes",
      title: "Sınıflar",
      icon: GraduationCap,
      endpoint: "/imports/classes",
      requiredCols: "Sınıf Adı (Opsiyonel: Seviye, Şube, Öğrenci Sayısı, Günlük Max Ders)",
      description: "Şube ve sınıf gruplarını (ör. 9/A, 10/B) Excel'den aktarın.",
    },
    {
      id: "courses",
      title: "Dersler",
      icon: BookOpen,
      endpoint: "/imports/courses",
      requiredCols: "Ders Adı (Opsiyonel: Ders Kodu, Branş, Haftalık Saat, Blok Ders Saati)",
      description: "Okul müfredat derslerini ve blok ders saatlerini içe aktarın.",
    },
    {
      id: "classrooms",
      title: "Derslikler",
      icon: Building2,
      endpoint: "/imports/classrooms",
      requiredCols: "Derslik Adı (Opsiyonel: Kapasite, Derslik Türü)",
      description: "Laboratuvar, spor salonu ve derslik alanlarını yükleyin.",
    },
    {
      id: "assignments",
      title: "Ders Atamaları",
      icon: LinkIcon,
      endpoint: "/imports/assignments",
      requiredCols: "Sınıf Adı, Ders Adı, Öğretmen Ad Soyad (Opsiyonel: Özel Derslik, Haftalık Saat)",
      description: "Sınıf, ders, öğretmen ve derslik eşleştirmelerini toplu yükleyin.",
    },
  ];

  const currentCat = categories.find((c) => c.id === activeTab)!;

  const handleDownloadTemplate = () => {
    window.open(`${apiBaseUrl}/api/imports/template/${activeTab}`, "_blank");
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setStatusMessage({ type: "", text: "" });

    const formData = new FormData();
    formData.append("file", file);

    let url = `${currentCat.endpoint}?school_id=${selectedSchoolId}`;
    if (activeTab === "assignments") {
      url += `&academic_year_id=${selectedAcademicYearId}`;
    }

    try {
      const res = await api.post(url, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setStatusMessage({
        type: "success",
        text: res.data.message,
        skipped: res.data.skipped,
      });
      setFile(null);
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.response?.data?.detail || "İçe aktarım sırasında bir hata oluştu.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="max-w-4xl space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Toplu Excel İçe Aktarım</h1>
          <p className="text-sm text-slate-500">Öğretmen, sınıf, ders, derslik ve ders atama verilerini Excel ile aktarın</p>
        </div>

        {/* Category Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-slate-200 pb-3">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isActive = activeTab === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => {
                  setActiveTab(cat.id);
                  setFile(null);
                  setStatusMessage({ type: "", text: "" });
                }}
                className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition ${
                  isActive
                    ? "bg-blue-600 text-white shadow-sm"
                    : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50"
                }`}
              >
                <Icon className="h-4 w-4" />
                {cat.title}
              </button>
            );
          })}
        </div>

        {/* Active Category Meta & Download Template */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div>
            <h3 className="font-bold text-slate-800 text-base">{currentCat.title} İçe Aktarımı</h3>
            <p className="text-xs text-slate-500 mt-0.5">{currentCat.description}</p>
            <p className="text-xs text-blue-700 font-medium mt-2">Zorunlu Kolonlar: {currentCat.requiredCols}</p>
          </div>
          <button
            onClick={handleDownloadTemplate}
            className="flex items-center gap-2 shrink-0 rounded-lg bg-emerald-50 px-4 py-2.5 text-xs font-semibold text-emerald-700 border border-emerald-200 hover:bg-emerald-100 transition"
          >
            <Download className="h-4 w-4" />
            Örnek Şablon İndir (.xlsx)
          </button>
        </div>

        {statusMessage.text && (
          <div
            className={`flex flex-col gap-2 rounded-xl p-4 text-sm font-medium border ${
              statusMessage.type === "success"
                ? "bg-emerald-50 text-emerald-900 border-emerald-200"
                : "bg-red-50 text-red-900 border-red-200"
            }`}
          >
            <div className="flex items-center gap-2 font-bold">
              {statusMessage.type === "success" ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 shrink-0" />
              )}
              {statusMessage.text}
            </div>

            {statusMessage.skipped && statusMessage.skipped.length > 0 && (
              <ul className="mt-2 text-xs space-y-1 text-slate-700 list-disc pl-5">
                {statusMessage.skipped.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* File Upload Form */}
        <form onSubmit={handleUpload} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4">
          <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-300 p-8 hover:border-blue-500 transition cursor-pointer">
            <FileSpreadsheet className="h-10 w-10 text-emerald-600 mb-2" />
            <p className="text-sm font-semibold text-slate-700">{currentCat.title} Excel Dosyası Yükleyin (.xlsx)</p>
            <p className="text-xs text-slate-400 mt-1">Dosyanızı sürükleyin veya bilgisayarınızdan seçin</p>

            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="mt-4 text-xs text-slate-500"
            />
          </div>

          <button
            type="submit"
            disabled={!file || loading}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 transition disabled:opacity-50"
          >
            <Upload className="h-4 w-4" />
            {loading ? "Veriler Aktarılıyor..." : `${currentCat.title} Excel'ini Aktar`}
          </button>
        </form>
      </div>
    </DashboardLayout>
  );
}
