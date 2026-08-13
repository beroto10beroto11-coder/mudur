"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import DashboardLayout from "../dashboard/layout";
import { Play, AlertCircle, Save, Loader2, Clock, CheckCircle2 } from "lucide-react";

interface StagedMove {
  lessonId: number;
  day: number;
  period: number;
}

export default function TimetablePage() {
  const queryClient = useQueryClient();
  const { selectedSchoolId, selectedAcademicYearId } = useSchoolStore();
  const [selectedTimetableId, setSelectedTimetableId] = useState<number | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [filterTeacher, setFilterTeacher] = useState<number | undefined>();
  const [filterClass, setFilterClass] = useState<number | undefined>();
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Unsaved changes state
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [pendingMove, setPendingMove] = useState<StagedMove | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // Polling refs
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

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
      const latest = timetables[0];
      setSelectedTimetableId(latest.id);
      if (latest.status === "GENERATING") {
        startMonitoring(latest.id);
      }
    }
  }, [timetables]);

  const { data: lessons = [], refetch: refetchLessons } = useQuery({
    queryKey: ["timetable-lessons", selectedTimetableId, filterTeacher, filterClass],
    queryFn: async () => {
      if (!selectedTimetableId) return [];
      let url = `/timetables/${selectedTimetableId}/lessons`;
      const params = new URLSearchParams();
      if (filterTeacher) params.append("teacher_id", filterTeacher.toString());
      if (filterClass) params.append("class_id", filterClass.toString());
      if (params.toString()) url += `?${params.toString()}`;
      const res = await api.get(url);
      return res.data;
    },
    enabled: !!selectedTimetableId,
  });

  // Unload protection
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = "Kaydedilmemiş değişiklikleriniz var. Ayrılmak istiyor musunuz?";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [hasUnsavedChanges]);

  // Elapsed timer
  useEffect(() => {
    let timer: ReturnType<typeof setInterval>;
    if (isGenerating) {
      timer = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    } else {
      setElapsedSeconds(0);
    }
    return () => clearInterval(timer);
  }, [isGenerating]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const startMonitoring = (ttId: number) => {
    setIsGenerating(true);
    setProgress(10);

    // Try WebSocket first (works with Redis), fallback to HTTP polling
    const wsUrl = (process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000") + `/api/timetables/ws/${ttId}`;
    let wsConnected = false;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => { wsConnected = true; };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.percent) setProgress(Math.min(95, data.percent));
          if (data.status === "GENERATED" || data.status === "FAILED") {
            finishGeneration(data.status === "GENERATED");
            ws.close();
          }
        } catch {}
      };

      ws.onerror = () => {
        if (!wsConnected) startPolling(ttId);
      };

      // If WebSocket doesn't connect in 2 seconds, fallback to polling
      setTimeout(() => {
        if (!wsConnected || ws.readyState !== WebSocket.OPEN) {
          startPolling(ttId);
        }
      }, 2000);
    } catch {
      startPolling(ttId);
    }
  };

  const startPolling = (ttId: number) => {
    if (pollingRef.current) clearInterval(pollingRef.current);

    pollingRef.current = setInterval(async () => {
      try {
        const res = await api.get(`/timetables/${ttId}`);
        const status = res.data?.status;

        // Animate progress bar while waiting
        setProgress((p) => Math.min(92, p + 4));

        if (status === "GENERATED") {
          finishGeneration(true);
        } else if (status === "FAILED") {
          finishGeneration(false);
        }
      } catch {
        // keep polling
      }
    }, 3000);
  };

  const finishGeneration = (success: boolean) => {
    setIsGenerating(false);
    setProgress(100);
    if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
    if (wsRef.current) { wsRef.current.close(); wsRef.current = null; }
    queryClient.invalidateQueries({ queryKey: ["timetables"] });
    refetchLessons();
    if (success) {
      setSuccessMessage("✅ Ders programı başarıyla oluşturuldu!");
      setTimeout(() => setSuccessMessage(""), 5000);
    } else {
      setErrorMessage("❌ Solver çözüm bulamadı. Lütfen ders atamalarını ve müsaitlik ayarlarını kontrol edin.");
    }
  };

  const generateMutation = useMutation({
    mutationFn: async () => {
      return api.post(`/timetables/generate?school_id=${selectedSchoolId}`, {
        academic_year_id: selectedAcademicYearId,
        name: `Ders Programı #${Date.now().toString().slice(-4)}`,
      });
    },
    onSuccess: (res) => {
      const ttId = res.data.id;
      setSelectedTimetableId(ttId);
      setErrorMessage("");
      startMonitoring(ttId);
    },
    onError: () => {
      setErrorMessage("Program oluşturma başlatılamadı. Lütfen tekrar deneyin.");
    },
  });

  const commitMoveMutation = useMutation({
    mutationFn: async (moveData: StagedMove) => {
      return api.patch(`/timetables/${selectedTimetableId}/lessons/${moveData.lessonId}`, {
        new_day: moveData.day,
        new_period: moveData.period,
      });
    },
    onSuccess: () => {
      setErrorMessage("");
      setHasUnsavedChanges(false);
      setPendingMove(null);
      setIsSaving(false);
      refetchLessons();
    },
    onError: (err: any) => {
      setIsSaving(false);
      setErrorMessage(err.response?.data?.detail || "Ders taşıma başarısız oldu (Çakışma).");
    },
  });

  const handleStageMove = (lessonId: number, day: number, period: number) => {
    setPendingMove({ lessonId, day, period });
    setHasUnsavedChanges(true);
    setErrorMessage("");
  };

  const handleSaveToDatabase = () => {
    if (pendingMove) {
      setIsSaving(true);
      commitMoveMutation.mutate(pendingMove);
    } else {
      setHasUnsavedChanges(false);
    }
  };

  const handleDiscardChanges = () => {
    setPendingMove(null);
    setHasUnsavedChanges(false);
    refetchLessons();
  };

  const days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"];
  const periods = [1, 2, 3, 4, 5, 6, 7, 8];

  const getLessonAt = (day: number, period: number) => {
    if (pendingMove && pendingMove.day === day && pendingMove.period === period) {
      const orig = lessons.find((l: any) => l.id === pendingMove.lessonId);
      if (orig) return { ...orig, day, period, isStaged: true };
    }
    const lesson = lessons.find((l: any) => l.day === day && l.period === period);
    if (pendingMove && lesson && lesson.id === pendingMove.lessonId) return null;
    return lesson;
  };

  return (
    <DashboardLayout>
      <div className="space-y-5">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">Ders Programı Editörü</h1>
            <p className="text-sm text-slate-500">Otomatik solver çıktısını görün ve manuel drag & drop düzenlemeler yapın</p>
          </div>

          <div className="flex items-center gap-2">
            {hasUnsavedChanges && (
              <div className="flex items-center gap-1.5 rounded-lg border border-amber-200 bg-amber-50 px-2.5 py-1.5 text-xs font-semibold text-amber-800">
                <span className="h-2 w-2 rounded-full bg-amber-500 animate-ping inline-block"></span>
                Kaydedilmemiş Değişiklik
                <button onClick={handleDiscardChanges} className="ml-1 text-slate-400 hover:text-red-600 transition">✕</button>
              </div>
            )}

            <button
              onClick={handleSaveToDatabase}
              disabled={!hasUnsavedChanges || isSaving}
              className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-blue-700 transition disabled:opacity-40 shadow-xs"
            >
              {isSaving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
              {isSaving ? "Kaydediliyor..." : "Kaydet"}
            </button>

            <button
              onClick={() => generateMutation.mutate()}
              disabled={isGenerating}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3.5 py-2 text-xs font-semibold text-white hover:bg-emerald-700 transition disabled:opacity-50 shadow-xs"
            >
              {isGenerating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
              {isGenerating ? "Çözülüyor..." : "Otomatik Program Oluştur"}
            </button>
          </div>
        </div>

        {/* Filtreler */}
        <div className="flex flex-wrap gap-3 items-center bg-white border border-slate-200 rounded-xl px-4 py-3 shadow-xs">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Filtrele:</span>

          <div className="flex items-center gap-1.5">
            <label className="text-xs text-slate-600 font-medium">Program:</label>
            <select
              value={selectedTimetableId || ""}
              onChange={(e) => setSelectedTimetableId(Number(e.target.value) || null)}
              className="rounded-lg border border-slate-300 text-xs px-2 py-1.5 bg-white"
            >
              {timetables.map((tt: any) => (
                <option key={tt.id} value={tt.id}>{tt.name}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <label className="text-xs text-slate-600 font-medium">Sınıf:</label>
            <select
              value={filterClass || ""}
              onChange={(e) => setFilterClass(Number(e.target.value) || undefined)}
              className="rounded-lg border border-slate-300 text-xs px-2 py-1.5 bg-white"
            >
              <option value="">Tümü</option>
              {classes.map((cls: any) => (
                <option key={cls.id} value={cls.id}>{cls.name}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <label className="text-xs text-slate-600 font-medium">Öğretmen:</label>
            <select
              value={filterTeacher || ""}
              onChange={(e) => setFilterTeacher(Number(e.target.value) || undefined)}
              className="rounded-lg border border-slate-300 text-xs px-2 py-1.5 bg-white"
            >
              <option value="">Tümü</option>
              {teachers.map((t: any) => (
                <option key={t.id} value={t.id}>{t.full_name}</option>
              ))}
            </select>
          </div>

          {(filterClass || filterTeacher) && (
            <button
              onClick={() => { setFilterClass(undefined); setFilterTeacher(undefined); }}
              className="text-xs text-red-500 hover:text-red-700 font-medium"
            >
              ✕ Filtreyi Temizle
            </button>
          )}
        </div>

        {/* Alerts */}
        {errorMessage && (
          <div className="flex items-start gap-2 rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs font-semibold text-red-700">
            <AlertCircle className="h-4 w-4 shrink-0 mt-0.5 text-red-500" />
            {errorMessage}
          </div>
        )}
        {successMessage && (
          <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 text-xs font-semibold text-emerald-700">
            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            {successMessage}
          </div>
        )}

        {/* Solver Progress Bar (Redis/Celery or Thread) */}
        {isGenerating && (
          <div className="rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 p-4 shadow-xs space-y-2.5">
            <div className="flex items-center justify-between text-xs font-semibold text-blue-950">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                <span>OR-Tools CP-SAT Portfolio Search ile Hesaplanıyor...</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1 font-mono text-slate-500 text-[11px]">
                  <Clock className="h-3 w-3" />
                  {elapsedSeconds}sn
                </span>
                <span className="font-bold text-blue-700">%{Math.round(progress)}</span>
              </div>
            </div>
            <div className="w-full h-1.5 bg-blue-200/80 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-500 rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-[11px] text-blue-800/70 font-medium">
              Öğretmen çakışmaları, müsaitlikler ve blok dersler optimum şekilde hesaplanıyor...
            </p>
          </div>
        )}

        {/* Timetable Grid */}
        <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm overflow-x-auto">
          {lessons.length === 0 && !isGenerating ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-400 gap-3">
              <Play className="h-10 w-10 text-slate-300" />
              <p className="text-sm font-medium">Ders programı henüz oluşturulmadı.</p>
              <p className="text-xs">Yukarıdaki "Otomatik Program Oluştur" butonuna basın.</p>
            </div>
          ) : (
            <table className="w-full border-collapse text-center text-xs">
              <thead>
                <tr className="bg-slate-100 text-slate-700 font-bold uppercase">
                  <th className="border p-3 w-20">Ders Saati</th>
                  {days.map((dayName) => (
                    <th key={dayName} className="border p-3 min-w-[155px]">{dayName}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {periods.map((p) => (
                  <tr key={p} className="h-20">
                    <td className="border font-bold bg-slate-50 text-slate-600">{p}. Ders</td>
                    {days.map((_, dIdx) => {
                      const lesson = getLessonAt(dIdx, p);
                      return (
                        <td
                          key={dIdx}
                          className="border p-1.5 transition relative hover:bg-slate-50"
                          onDragOver={(e) => e.preventDefault()}
                          onDrop={(e) => {
                            const lessonId = e.dataTransfer.getData("lessonId");
                            if (lessonId) handleStageMove(Number(lessonId), dIdx, p);
                          }}
                        >
                          {lesson ? (
                            <div
                              draggable
                              onDragStart={(e) => e.dataTransfer.setData("lessonId", lesson.id.toString())}
                              className={`h-full w-full rounded-lg p-2 text-left cursor-move transition ${
                                lesson.isStaged
                                  ? "bg-amber-50 border-2 border-amber-400 shadow-sm"
                                  : "bg-blue-50 border border-blue-200 hover:border-blue-400 shadow-xs"
                              }`}
                            >
                              <div className="flex justify-between items-start gap-1">
                                <p className="font-bold text-blue-900 text-[11px] line-clamp-1 flex-1">{lesson.course_name}</p>
                                {lesson.isStaged && <span className="h-2 w-2 rounded-full bg-amber-500 animate-ping shrink-0 mt-0.5" />}
                              </div>
                              <p className="text-[10px] text-slate-600 mt-0.5 line-clamp-1">{lesson.teacher_name}</p>
                              <div className="flex justify-between items-center mt-1 text-[10px] text-slate-400 font-medium">
                                <span>{lesson.class_name}</span>
                                {lesson.classroom_name && (
                                  <span className="rounded bg-slate-200 px-1 py-0.5">{lesson.classroom_name}</span>
                                )}
                              </div>
                            </div>
                          ) : (
                            <div className="h-full w-full rounded border border-dashed border-slate-200 flex items-center justify-center text-slate-300 hover:border-slate-400 text-[10px]">
                              Boş
                            </div>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
