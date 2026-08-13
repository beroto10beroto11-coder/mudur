"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import {
  Calendar,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Download,
  FileSpreadsheet,
  FileText,
  FileType,
  Loader2,
  ChevronRight,
  Info,
  Zap,
} from "lucide-react";
import DashboardLayout from "../dashboard/layout";

type OutputFormat = "excel" | "pdf" | "word";

interface ValidationResponse {
  valid: boolean;
  errors: string[];
  warnings: string[];
}

interface AcademicYear {
  id: number;
  name: string;
}

export default function SchedulerPage() {
  const { selectedSchoolId } = useSchoolStore();
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<OutputFormat>("excel");
  const [isGenerating, setIsGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [generateSuccess, setGenerateSuccess] = useState<string | null>(null);

  // Akademik yıllar
  const { data: academicYears = [] } = useQuery<AcademicYear[]>({
    queryKey: ["academic_years", selectedSchoolId],
    queryFn: async () => (await api.get(`/schools/${selectedSchoolId}/academic-years`)).data,
    enabled: !!selectedSchoolId,
  });

  useEffect(() => {
    if (academicYears.length > 0 && !selectedYear) {
      setSelectedYear(academicYears[0].id);
    }
  }, [academicYears, selectedYear]);

  // Validasyon
  const {
    data: validation,
    isLoading: validating,
    refetch: revalidate,
  } = useQuery<ValidationResponse>({
    queryKey: ["scheduler_validate", selectedSchoolId, selectedYear],
    queryFn: async () =>
      (
        await api.get(
          `/scheduler/validate?school_id=${selectedSchoolId}&academic_year_id=${selectedYear}`
        )
      ).data,
    enabled: !!selectedSchoolId && !!selectedYear,
    staleTime: 0,
  });

  const handleGenerate = async () => {
    if (!selectedYear || !selectedSchoolId) return;
    setIsGenerating(true);
    setGenerateError(null);
    setGenerateSuccess(null);

    try {
      const response = await api.post(
        `/scheduler/generate?school_id=${selectedSchoolId}`,
        {
          academic_year_id: selectedYear,
          format: selectedFormat,
          time_limit_seconds: 120,
        },
        { responseType: "blob" }
      );

      // Dosyayı indir
      const extMap: Record<OutputFormat, string> = {
        excel: "xlsx",
        pdf: "pdf",
        word: "docx",
      };
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `ders_programi.${extMap[selectedFormat]}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      const lessonCount = response.headers["x-lesson-count"] || "?";
      const warnCount = response.headers["x-warning-count"] || "0";
      setGenerateSuccess(
        `✅ Program başarıyla oluşturuldu! ${lessonCount} ders bloğu atandı.` +
          (Number(warnCount) > 0 ? ` ⚠️ ${warnCount} uyarı — dosyanın Uyarılar sayfasını inceleyin.` : "")
      );
    } catch (err: any) {
      const detail =
        err.response?.data instanceof Blob
          ? await err.response.data.text().then((t: string) => {
              try {
                return JSON.parse(t).detail;
              } catch {
                return t;
              }
            })
          : err.response?.data?.detail || err.message;
      setGenerateError(`❌ Hata: ${detail}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const formatOptions: { id: OutputFormat; label: string; icon: any; desc: string; color: string }[] = [
    {
      id: "excel",
      label: "Excel (.xlsx)",
      icon: FileSpreadsheet,
      desc: "Her sınıf ve öğretmen ayrı sheet, Uyarılar sayfası",
      color: "from-emerald-500 to-green-600",
    },
    {
      id: "pdf",
      label: "PDF",
      icon: FileText,
      desc: "Yazdırmaya hazır, A4 yatay sayfa düzeni",
      color: "from-red-500 to-rose-600",
    },
    {
      id: "word",
      label: "Word (.docx)",
      icon: FileType,
      desc: "Düzenlenebilir format, tablo yapısı korunur",
      color: "from-blue-500 to-indigo-600",
    },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-violet-600 to-purple-700 shadow-lg">
              <Zap className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-800">Otomatik Ders Programı</h1>
              <p className="text-sm text-slate-500">
                OR-Tools CP-SAT algoritması ile kısıt tabanlı otomatik program üretimi
              </p>
            </div>
          </div>
        </div>

        {/* Akademik Yıl Seçimi */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6">
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <Calendar className="h-4 w-4 text-violet-600" />
            Akademik Yıl
          </h2>
          <select
            value={selectedYear || ""}
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            className="w-full max-w-xs rounded-xl border border-slate-300 p-2.5 text-sm focus:border-violet-500 focus:outline-none focus:ring-2 focus:ring-violet-100"
          >
            {academicYears.map((y) => (
              <option key={y.id} value={y.id}>
                {y.name}
              </option>
            ))}
          </select>
        </div>

        {/* Veri Doğrulama Paneli */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Info className="h-4 w-4 text-blue-600" />
              Veri Tutarlılık Raporu
            </h2>
            <button
              onClick={() => revalidate()}
              className="text-xs text-violet-600 hover:underline font-semibold"
            >
              Yenile
            </button>
          </div>

          {validating ? (
            <div className="flex items-center gap-3 text-slate-500 text-sm py-4">
              <Loader2 className="h-5 w-5 animate-spin text-violet-500" />
              Veriler kontrol ediliyor...
            </div>
          ) : !validation ? (
            <p className="text-sm text-slate-400">Akademik yıl seçin.</p>
          ) : (
            <div className="space-y-3">
              {/* Genel durum */}
              <div
                className={`flex items-center gap-3 rounded-xl p-3 ${
                  validation.valid
                    ? "bg-emerald-50 border border-emerald-200"
                    : "bg-red-50 border border-red-200"
                }`}
              >
                {validation.valid ? (
                  <CheckCircle className="h-5 w-5 text-emerald-600 shrink-0" />
                ) : (
                  <XCircle className="h-5 w-5 text-red-600 shrink-0" />
                )}
                <span
                  className={`text-sm font-semibold ${
                    validation.valid ? "text-emerald-700" : "text-red-700"
                  }`}
                >
                  {validation.valid
                    ? "Tüm veriler tutarlı — program üretilebilir."
                    : `${validation.errors.length} kritik hata bulundu — program üretilemez.`}
                </span>
              </div>

              {/* Hatalar */}
              {validation.errors.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-xs font-bold text-red-600 uppercase tracking-wide">
                    Kritik Hatalar ({validation.errors.length})
                  </p>
                  {validation.errors.map((e, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 rounded-lg bg-red-50 border border-red-100 p-2.5 text-xs text-red-800"
                    >
                      <XCircle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-red-500" />
                      {e}
                    </div>
                  ))}
                </div>
              )}

              {/* Uyarılar */}
              {validation.warnings.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-xs font-bold text-amber-600 uppercase tracking-wide">
                    Uyarılar ({validation.warnings.length})
                  </p>
                  {validation.warnings.map((w, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-100 p-2.5 text-xs text-amber-800"
                    >
                      <AlertTriangle className="h-3.5 w-3.5 mt-0.5 shrink-0 text-amber-500" />
                      {w}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Format Seçimi */}
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm p-6">
          <h2 className="text-sm font-semibold text-slate-700 mb-4 flex items-center gap-2">
            <Download className="h-4 w-4 text-violet-600" />
            Çıktı Formatı
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {formatOptions.map((opt) => {
              const Icon = opt.icon;
              const selected = selectedFormat === opt.id;
              return (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => setSelectedFormat(opt.id)}
                  className={`relative flex flex-col items-start gap-2 rounded-xl border-2 p-4 text-left transition-all ${
                    selected
                      ? "border-violet-500 bg-violet-50 shadow-md"
                      : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                  }`}
                >
                  <div
                    className={`p-2 rounded-lg bg-gradient-to-br ${opt.color} shadow-sm`}
                  >
                    <Icon className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className={`text-sm font-bold ${selected ? "text-violet-700" : "text-slate-700"}`}>
                      {opt.label}
                    </p>
                    <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{opt.desc}</p>
                  </div>
                  {selected && (
                    <div className="absolute top-3 right-3">
                      <CheckCircle className="h-4 w-4 text-violet-600" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Sonuç mesajları */}
        {generateSuccess && (
          <div className="flex items-start gap-3 rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-sm text-emerald-800">
            <CheckCircle className="h-5 w-5 mt-0.5 shrink-0 text-emerald-600" />
            {generateSuccess}
          </div>
        )}
        {generateError && (
          <div className="flex items-start gap-3 rounded-xl bg-red-50 border border-red-200 p-4 text-sm text-red-800">
            <XCircle className="h-5 w-5 mt-0.5 shrink-0 text-red-600" />
            {generateError}
          </div>
        )}

        {/* Oluştur Butonu */}
        <div className="flex justify-end">
          <button
            onClick={handleGenerate}
            disabled={isGenerating || !selectedYear}
            className={`flex items-center gap-3 rounded-xl px-8 py-3.5 text-sm font-bold text-white shadow-lg transition-all ${
              isGenerating || !selectedYear
                ? "bg-slate-300 cursor-not-allowed"
                : "bg-gradient-to-r from-violet-600 to-purple-700 hover:from-violet-700 hover:to-purple-800 hover:shadow-xl active:scale-95"
            }`}
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Çözüm hesaplanıyor...
              </>
            ) : (
              <>
                <Zap className="h-5 w-5" />
                Ders Programı Oluştur
                <ChevronRight className="h-4 w-4" />
              </>
            )}
          </button>
        </div>

        {/* Bilgi Kutusu */}
        <div className="rounded-2xl border border-slate-100 bg-slate-50 p-5 text-xs text-slate-500 space-y-1.5">
          <p className="font-semibold text-slate-600">Algoritma Hakkında</p>
          <p>
            OR-Tools CP-SAT kısıt sağlama algoritması kullanılmaktadır. Müsaitlik, branş uyumu,
            çakışma, ardışık blok ve doluluk kuralları aynı anda çözülür.
          </p>
          <p>
            Çözüm bulunamayan (ders, sınıf) çiftleri durdurma yapmadan atlanır; indirilen
            dosyanın <strong>Uyarılar</strong> sayfasında nedenleriyle listelenir.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}
