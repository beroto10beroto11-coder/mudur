"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useSchoolStore } from "@/stores/schoolStore";
import {
  Users,
  GraduationCap,
  BookOpen,
  Building2,
  AlertTriangle,
  CheckCircle,
  Calendar,
} from "lucide-react";

export default function DashboardPage() {
  const { selectedSchoolId } = useSchoolStore();

  const { data: stats, isLoading } = useQuery({
    queryKey: ["dashboard-stats", selectedSchoolId],
    queryFn: async () => {
      const res = await api.get(`/reports/dashboard-stats?school_id=${selectedSchoolId}`);
      return res.data;
    },
  });

  if (isLoading) {
    return <div className="p-8 text-slate-500">İstatistikler yükleniyor...</div>;
  }

  const statCards = [
    { title: "Toplam Öğretmen", value: stats?.total_teachers || 0, icon: Users, color: "bg-blue-500" },
    { title: "Toplam Sınıf", value: stats?.total_classes || 0, icon: GraduationCap, color: "bg-emerald-500" },
    { title: "Toplam Ders", value: stats?.total_courses || 0, icon: BookOpen, color: "bg-amber-500" },
    { title: "Toplam Derslik", value: stats?.total_classrooms || 0, icon: Building2, color: "bg-indigo-500" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Yönetim Paneli</h1>
        <p className="text-sm text-slate-500">Okul ders programı genel durumu ve temel göstergeler</p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.title} className="flex items-center justify-between rounded-xl bg-white p-6 shadow-sm border border-slate-200">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{card.title}</p>
                <p className="mt-2 text-3xl font-bold text-slate-800">{card.value}</p>
              </div>
              <div className={`rounded-lg p-3 text-white ${card.color}`}>
                <Icon className="h-6 w-6" />
              </div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-blue-600" />
            Son Oluşturulan Program
          </h3>

          {stats?.latest_timetable_name ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm text-slate-600">Program Adı</span>
                <span className="font-semibold text-slate-800">{stats.latest_timetable_name}</span>
              </div>
              <div className="flex justify-between items-center py-2 border-b">
                <span className="text-sm text-slate-600">Durum</span>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800">
                  <CheckCircle className="h-3.5 w-3.5" />
                  {stats.latest_timetable_status}
                </span>
              </div>
              <div className="flex justify-between items-center py-2">
                <span className="text-sm text-slate-600">Açık Çakışma Sayısı</span>
                <span className={`font-semibold ${stats.open_conflicts_count > 0 ? "text-red-600" : "text-emerald-600"}`}>
                  {stats.open_conflicts_count}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500 py-4">Henüz oluşturulmuş bir ders programı bulunmuyor.</p>
          )}
        </div>

        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            Sistem Bildirimleri & Durum
          </h3>
          <ul className="space-y-3 text-sm text-slate-600">
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              OR-Tools CP-SAT Solver Servisi Aktif
            </li>
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              Redis & Celery Arka Plan Kuyruğu Bağlı
            </li>
            <li className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              PostgreSQL Otomatik Yedekleme Aktif (03:00)
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
