import { create } from "zustand";

interface SchoolState {
  selectedSchoolId: number;
  selectedAcademicYearId: number;
  setSchoolId: (id: number) => void;
  setAcademicYearId: (id: number) => void;
}

export const useSchoolStore = create<SchoolState>((set) => ({
  selectedSchoolId: 1,
  selectedAcademicYearId: 1,
  setSchoolId: (id) => set({ selectedSchoolId: id }),
  setAcademicYearId: (id) => set({ selectedAcademicYearId: id }),
}));
