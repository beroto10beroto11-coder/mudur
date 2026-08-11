"""
Scheduler Veri Modelleri
========================
Girdi JSON şemalarını ve çıktı yapılarını tanımlar.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, field_validator, model_validator


# ─────────────────────────────────────────────────────────────────────────────
# GIRDI MODELLERİ
# ─────────────────────────────────────────────────────────────────────────────

class ZamanYapisi(BaseModel):
    """Okulun genel zaman yapısı."""
    gunler: List[str]
    """Gün isimleri; sıra önemlidir (0-indexed → indeks=gün_no)."""
    gunluk_ders_saatleri: List[int]
    """Her güne ait maksimum ders saati sayısı."""

    @model_validator(mode="after")
    def kontrol_esitlik(self) -> "ZamanYapisi":
        if len(self.gunler) != len(self.gunluk_ders_saatleri):
            raise ValueError(
                "gunler ve gunluk_ders_saatleri listeleri aynı uzunlukta olmalı."
            )
        return self

    @property
    def toplam_haftalik_saat(self) -> int:
        return sum(self.gunluk_ders_saatleri)


class Sube(BaseModel):
    """Bir şubeyi (sınıf grubunu) temsil eder."""
    sube_id: str
    sinif_seviyesi: int
    ad: str


class Ogretmen(BaseModel):
    """Bir öğretmeni ve müsaitlik bilgisini temsil eder."""
    ogretmen_id: str
    ad: str
    soyad: str
    branslar: List[str]
    """Bu öğretmenin verebileceği branş kodları (örn. ["MAT", "GEO"])."""
    girebilecegi_subeler: List[str]
    """Bu öğretmenin girebileceği sube_id listesi."""
    musaitlik: Dict[str, List[bool]]
    """
    Anahtar: gün adı, Değer: o günün her saati için bool listesi.
    True = müsait, False = müsait değil.
    """

    @field_validator("musaitlik")
    @classmethod
    def kontrol_musaitlik(cls, v: Dict[str, List[bool]]) -> Dict[str, List[bool]]:
        for gun, saatler in v.items():
            if not isinstance(saatler, list):
                raise ValueError(f"{gun} için müsaitlik bir liste olmalı.")
        return v

    def musait_mi(self, gun: str, saat_index: int) -> bool:
        """Saat index 0-tabanlıdır."""
        gunluk = self.musaitlik.get(gun)
        if gunluk is None or saat_index >= len(gunluk):
            return False
        return gunluk[saat_index]

    @property
    def tam_ad(self) -> str:
        return f"{self.ad} {self.soyad}"


class Ders(BaseModel):
    """Bir ders tanımını temsil eder."""
    ders_id: str
    ders_adi: str
    kod: str
    """Branş kodu (örn. "MAT"). Öğretmen eşleştirmede kullanılır."""
    gecerli_sube_ids: List[str]
    """Bu dersin uygulandığı şube listesi."""
    haftalik_saat: int
    """Toplam haftalık ders saati."""
    gunluk_dagilim: List[int]
    """
    Her eleman bir bloğun uzunluğunu belirtir.
    Örn. [2, 2, 1, 1] → 4 blok; 2 ardışık + 2 ardışık + 1 + 1.
    Toplam == haftalik_saat olmalı.
    """

    @model_validator(mode="after")
    def kontrol_dagilim(self) -> "Ders":
        if sum(self.gunluk_dagilim) != self.haftalik_saat:
            raise ValueError(
                f"Ders '{self.ders_id}': gunluk_dagilim toplamı "
                f"({sum(self.gunluk_dagilim)}) haftalik_saat "
                f"({self.haftalik_saat}) ile eşit olmalı."
            )
        if any(b <= 0 for b in self.gunluk_dagilim):
            raise ValueError(
                f"Ders '{self.ders_id}': gunluk_dagilim içinde sıfır veya "
                "negatif blok olamaz."
            )
        return self

    @property
    def blok_sayisi(self) -> int:
        return len(self.gunluk_dagilim)


class SchedulerInput(BaseModel):
    """Tam çizelgeleme girdisi."""
    zaman_yapisi: ZamanYapisi
    subeler: List[Sube]
    ogretmenler: List[Ogretmen]
    dersler: List[Ders]

    # ─── Opsiyonel ayarlar ───────────────────────────────────────────────────
    maks_cozum_suresi_saniye: int = 300
    """CP-SAT solver için maksimum çalışma süresi (saniye)."""
    paralel_isci_sayisi: Optional[int] = None
    """
    Paralel arama işçisi sayısı. None ise CPU sayısına göre otomatik.
    """

    # ─── Soft constraint ağırlıkları ─────────────────────────────────────────
    agirlik_ogretmen_bosluk: int = 10
    """Öğretmenin günlük boşluk (pencere) cezası ağırlığı."""
    agirlik_dengeli_dagilim: int = 3
    """Günlük ders yoğunluğu dengesizliği cezası ağırlığı."""


# ─────────────────────────────────────────────────────────────────────────────
# ÇIKTI MODELLERİ
# ─────────────────────────────────────────────────────────────────────────────

class SubeSlot(BaseModel):
    """Şube programındaki tek bir ders saati."""
    saat: int
    """1-tabanlı ders saati numarası."""
    ders_id: str
    ogretmen_id: str


class SubeProgram(BaseModel):
    """Tek bir şubenin haftalık programı."""
    sube_id: str
    program: Dict[str, List[SubeSlot]]
    """Anahtar: gün adı → o günkü ders listesi."""


class OgretmenSlot(BaseModel):
    """Öğretmen programındaki tek bir saat."""
    saat: int
    """1-tabanlı ders saati numarası."""
    ders_id: Optional[str] = None
    sube_id: Optional[str] = None
    durum: str = "DOLU"
    """'DOLU' veya 'BOŞ'."""


class OgretmenProgram(BaseModel):
    """Tek bir öğretmenin haftalık programı."""
    ogretmen_id: str
    program: Dict[str, List[OgretmenSlot]]


class FeasibilityIhlali(BaseModel):
    """Ön doğrulama ihlali."""
    tur: str
    """
    'YETERSIZ_OGRETMEN' | 'SUBE_SAAT_UYUMSUZLUGU'
    """
    mesaj: str
    detay: dict = {}


class SchedulerResult(BaseModel):
    """Solver çalışmasının sonucu."""
    basarili: bool
    durum: str
    """
    'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE' | 'VALIDATION_ERROR'
    """
    sure_saniye: float
    hedef_deger: Optional[float] = None

    # Başarı durumunda dolu, aksi hâlde boş
    sube_programlari: List[SubeProgram] = []
    ogretmen_programlari: List[OgretmenProgram] = []

    # Hata / uyarı durumunda dolu
    ihlaller: List[FeasibilityIhlali] = []
    teshis_mesajlari: List[str] = []
