"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Users,
  GraduationCap,
  BookOpen,
  Building2,
  Calendar,
  Clock,
  Grid,
  ShieldCheck,
  Upload,
  Download,
  Database,
  FileText,
  Settings,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Öğretmenler", href: "/teachers", icon: Users },
  { name: "Sınıflar", href: "/classes", icon: GraduationCap },
  { name: "Dersler", href: "/courses", icon: BookOpen },
  { name: "Derslikler", href: "/classrooms", icon: Building2 },
  { name: "Öğretmen Müsaitlik", href: "/availability", icon: Clock },
  { name: "Zaman Slotları", href: "/timeslots", icon: Grid },
  { name: "Ders Programı", href: "/timetable", icon: Grid },
  { name: "Nöbet Sistemi", href: "/duties", icon: ShieldCheck },
  { name: "Excel İçe Aktar", href: "/imports", icon: Upload },
  { name: "Excel / PDF Dışa Aktar", href: "/exports", icon: Download },
  { name: "Yedekleme", href: "/backup", icon: Database },
  { name: "Audit Log", href: "/audit", icon: FileText },
  { name: "Ayarlar", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-full w-64 flex-col border-r bg-slate-900 text-white">
      <div className="flex h-16 items-center justify-center border-b border-slate-800 px-4">
        <h1 className="text-xl font-bold tracking-wider text-blue-400">OKUL SCHEDULER</h1>
      </div>
      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
