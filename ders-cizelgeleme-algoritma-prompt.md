# Görev: Okul Ders Çizelgeleme Algoritması (OR-Tools CP-SAT)

## Bağlam

Bir okul yönetim uygulaması geliştiriyorum. Uygulamada öğretmen, sınıf/şube, ders ve müsaitlik verileri zaten toplanıyor. Senden istediğim: bu verileri girdi olarak alıp, **her şube için** ve **her öğretmen için** çakışmasız, eksiksiz, kurallara uygun haftalık ders programı üreten bir **Python algoritması (Google OR-Tools CP-SAT solver kullanarak)** yazman.

Bu klasik bir School Timetabling / Constraint Satisfaction Problem'dir. Google OR-Tools CP-SAT solver'ı kullanılacak (pip: `ortools`).

---

## 1. Girdi Veri Modeli

Aşağıdaki JSON yapılarını girdi olarak kabul eden bir sistem tasarla (örnek şema, alan adlarını mantıklı biçimde düzenleyebilirsin):

### 1.1 Genel Zaman Yapısı
```json
{
  "gunler": ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"],
  "gunluk_ders_saatleri": [7, 7, 7, 7, 7]
}
```
- Her gün için kaç ders saati olduğu değişken olabilir (7+7+7+7+7 örnek, farklı okullarda farklı olabilir). Genel/global ayardır, tüm okul için geçerlidir.

### 1.2 Şubeler (Sınıflar)
```json
{
  "sube_id": "9A",
  "sinif_seviyesi": 9,
  "ad": "9/A"
}
```

### 1.3 Öğretmenler
```json
{
  "ogretmen_id": "T001",
  "ad": "Ahmet",
  "soyad": "Yılmaz",
  "branslar": ["MAT"],
  "girebilecegi_subeler": ["9A", "9B", "9C", "10A", "10B", "11A", "11B", "12A", "12B"],
  "musaitlik": {
    "Pazartesi": [true, true, true, true, true, true, true],
    "Salı": [true, true, true, true, true, true, true],
    "Çarşamba": [true, true, true, true, true, true, true],
    "Perşembe": [true, true, true, true, true, true, true],
    "Cuma": [true, true, false, false, false, false, true]
  }
}
```
- `musaitlik` dizisindeki her eleman bir ders saatine (1. ders, 2. ders, ...) karşılık gelir. `false` = o saatte kesinlikle atanamaz (izinli/kapalı/başka okulda görevli vb. — sebep önemli değil, sistem sadece uygun/değil olarak kullanır).

### 1.4 Ders Tanımları (ÖNEMLİ — sınıf seviyesine özel olabilir)
```json
{
  "ders_id": "MAT9",
  "ders_adi": "Matematik",
  "kod": "MAT",
  "gecerli_sube_ids": ["9A", "9B", "9C"],
  "haftalik_saat": 6,
  "gunluk_dagilim": [2, 2, 1, 1]
}
```
- **Kritik nokta:** Bir ders "Tüm Sınıflar (Genel)" olabileceği gibi, sadece belirli sınıf seviyesi/şubelere özel de tanımlanabilir (örn. `MAT9`, `MAT10` gibi farklı ders kayıtları, farklı haftalık saat/dağılım ile). Yani aynı branş (MAT) farklı sınıf seviyelerinde farklı `ders_id` ve farklı parametrelerle var olabilir. Algoritma bunu ders bazında (ders_id bazında), şubeye özel liste üzerinden okumalı — "genel" diye özel bir mantık kurma, her ders kendi `gecerli_sube_ids` listesini taşır (genel ise tüm şubeler o listede olur).
- `gunluk_dagilim: [2, 2, 1, 1]` şu anlama gelir: bu ders haftada 4 farklı günde işlenir; verilen günlerde sırasıyla **2 ardışık saat, 2 ardışık saat, 1 saat, 1 saat** olacak şekilde bloklanır. Toplamı `haftalik_saat`e eşit olmalı (2+2+1+1=6 ✓). Hangi günlere denk geleceğine solver karar verir (dizideki sıra gün sırası anlamına gelmez, sadece blok yapısını tanımlar) — **ama aynı derse ait bloklar farklı günlere dağılmalı, aynı gün içinde iki blok olamaz** (örn. bir gün 2 saat Matematik olduysa, aynı gün başka saatte tekrar Matematik olamaz).
- 2'li bloklar mutlaka **ardışık (art arda) 2 ders saati** olmalı (örn. 3. ve 4. ders), araya başka ders girmemeli.

---

## 2. Ön-Doğrulama (Solver'ı Çalıştırmadan Önce)

Solver'ı kurmadan önce şu kontrolü yap ve olabilirlik raporu üret:

1. **Branş/ders bazında kapasite kontrolü:** Her `ders_id` için gereken toplam saat = `haftalik_saat × ilgili şube sayısı`. Bu dersi verebilecek (branşı uygun + o şubeye girebilen + müsaitlik uygun) öğretmenlerin toplam sağlayabileceği saat kapasitesiyle karşılaştır. Kapasite yetersizse, çizelgelemeye başlamadan **"Yetersiz Öğretmen" raporu** üret: hangi ders/sınıf seviyesinde kaç saat açık, kaç saat karşılanabiliyor, hangi öğretmen(ler) eksik.
2. **Şube-saat kontrolü:** Her şube için, o şubeye ait tüm derslerin toplam haftalık saati, okulun toplam haftalık ders saatine (örn. 35) eşit mi? Eşit değilse uyarı ver (boş saat kalacak veya taşacak demektir).
3. Bu ön kontrol geçmeden CP-SAT modelini kurma; kullanıcıya (uygulama tarafında) önce bu raporu döndür.

---

## 3. CP-SAT Model Tasarımı

### 3.1 Karar Değişkenleri
Her (ders_id'nin bir bloğu, şube) için, bu bloğun başlayacağı (gün, başlangıç_saat) kombinasyonunu temsil eden Boolean değişkenler tanımla. Örneğin:
```
x[ders_id, sube_id, blok_index, gun, saat] = 1  →  bu blok bu gün bu saatte başlıyor
```
2 saatlik bloklarda "başlangıç saati" seçilince otomatik olarak sonraki saat de kaplanmış sayılmalı (ardışıklık bu şekilde modellenir).

Ayrıca her blok için **hangi öğretmenin** verdiğini seçen değişkenler:
```
y[ders_id, sube_id, blok_index, ogretmen_id] = 1  →  bu bloğu bu öğretmen veriyor
```

### 3.2 Sert Kısıtlar (Hard Constraints)
- Her şube, aynı (gün, saat) diliminde en fazla 1 derste olabilir (çakışma yok).
- Her öğretmen, aynı (gün, saat) diliminde en fazla 1 şubede olabilir (çakışma yok).
- Öğretmen sadece `musaitlik = true` olan saatlere atanabilir.
- Öğretmen sadece kendi `branslar` listesindeki dersleri ve kendi `girebilecegi_subeler` listesindeki şubeleri alabilir.
- Her dersin her bloğu haftada tam 1 kez, `gunluk_dagilim`e uygun uzunlukta (1 veya 2 ardışık saat) atanmalı.
- Aynı derse ait farklı bloklar aynı güne denk gelemez (örn. Matematik'in 2+2+1+1 dağılımındaki 4 blok, 4 farklı günde olmalı).
- 2 saatlik bloklar mutlaka aynı gün ardışık 2 saatte olmalı (araya başka ders giremez).
- Bir şubenin haftalık programında, o şubeye tanımlı tüm dersler için ayrılan tüm saatler doldurulmalı (boş saat kalmamalı) — bu, şube bazında toplam ders saati = toplam okul saatine eşit olacak şekilde ders tanımlarının zaten baştan doğru girilmiş olmasını gerektirir (bkz. Bölüm 2, madde 2).

### 3.3 Yumuşak Kısıtlar (Soft Constraints — Objective/Penalty)
Aşağıdakileri objective fonksiyonunda ceza puanı (minimize edilecek) olarak ekle, ağırlıklarını parametre yapılabilir şekilde kodla (örn. `WEIGHT_TEACHER_GAP = 10`):
- **Öğretmen boşluk (pencere) minimizasyonu:** Bir öğretmenin bir gün içindeki ilk ve son dersi arasında kalan boş saatler minimize edilsin.
- **Şube boşluk minimizasyonu:** Aynı mantık şubeler için de (öğrenciler için) uygulanabilir, ancak zaten "boş saat kalmayacak" hard constraint olduğu için burada daha çok öğretmen boşlukları öne çıkar.
- **Dengeli dağılım:** Ağır derslerin (örn. çok saatli dersler) haftanın tamamına yayılması, tek bir güne yığılmaması tercih edilsin (bu zaten `gunluk_dagilim` ile kısmen sağlanıyor ama farklı derslerin aynı güne çakışıp yoğunluk yaratmaması için ek bir denge terimi eklenebilir).
- (Varsa ileride) öğretmen tercih saatleri — şimdilik veri modelinde yok, ama kod genişletilebilir şekilde yazılsın.

---

## 4. Çıktı Formatı

İki ayrı görünüm/tablo seti üretilmeli (aynı çözümden türetilecek, iki farklı gruplama):

### 4.1 Şube Bazlı Çıktı
Her şube için, gün × saat matrisi şeklinde: hangi saatte hangi ders, hangi öğretmen tarafından işleniyor.
```json
{
  "sube_id": "9A",
  "program": {
    "Pazartesi": [
      {"saat": 1, "ders_id": "MAT9", "ogretmen_id": "T001"},
      {"saat": 2, "ders_id": "MAT9", "ogretmen_id": "T001"},
      ...
    ],
    ...
  }
}
```

### 4.2 Öğretmen Bazlı Çıktı
Her öğretmen için, gün × saat matrisi: hangi saatte hangi şubede, hangi ders.
```json
{
  "ogretmen_id": "T001",
  "program": {
    "Pazartesi": [
      {"saat": 1, "ders_id": "MAT9", "sube_id": "9A"},
      {"saat": 2, "ders_id": "MAT9", "sube_id": "9A"},
      {"saat": 3, "durum": "BOŞ"},
      ...
    ],
    ...
  }
}
```

Boş kalan öğretmen saatleri `"durum": "BOŞ"` şeklinde açıkça işaretlenmeli (bu şubeler için olmamalı, öğretmenler için normal).

---

## 5. Beklenen Kod Yapısı

- `ortools.sat.python.cp_model` kullanılacak.
- Veri girişini yukarıdaki JSON şemalarına göre parse eden bir katman.
- Bölüm 2'deki ön-doğrulama fonksiyonu (`validate_feasibility()`), çözümsüzlükleri insan-okunur rapor olarak döndürsün.
- Model kurulum fonksiyonu (`build_model()`), kısıtları Bölüm 3'e göre ekleyecek.
- `solver.Solve(model)` sonrası, `cp_model.OPTIMAL` veya `cp_model.FEASIBLE` durumlarında Bölüm 4'teki iki formatı da üreten dönüştürücü fonksiyonlar (`export_by_class()`, `export_by_teacher()`).
- Çözüm bulunamazsa (`INFEASIBLE`), hangi kısıtların gevşetilebileceğine dair (örn. hangi öğretmen/ders/şube kombinasyonunda tıkanma olduğu) bir hata ayıklama/teşhis çıktısı — mümkünse OR-Tools'un `AddAssumption` / infeasibility analizi ile, değilse en azından Bölüm 2'deki kapasite raporunu tekrar çalıştırarak.
- Kod, yeni kısıt eklemeye (örn. ileride öğretmen tercihleri, derslik kısıtları) açık, modüler şekilde yazılsın.
- Makul ölçekte (9 şube, ~35 saat/hafta, 10-30 öğretmen) çözüm süresi kabul edilebilir olmalı; gerekirse `solver.parameters.max_time_in_seconds` ile sınır konulsun ve `solver.parameters.num_search_workers` ile paralel arama açılsın.

---

## 6. Önemli Hatırlatmalar (Kesinlikle Unutulmamalı)

- **Çıktı hem şube bazlı hem öğretmen bazlı olmak üzere tam iki ayrı tablo seti içermeli.** Sadece birini üretmek yetersiz.
- Ders tanımları sınıf seviyesine/şubeye özel olabilir ("genel" özel bir durum değil, sadece `gecerli_sube_ids` tüm şubeleri kapsıyorsa genel gibi davranır).
- 2 saatlik bloklar mutlaka ardışık olmalı, araya başka ders giremez.
- Aynı ders aynı gün içinde birden fazla kez (ayrı bloklar olarak) yer alamaz.
- Hiçbir şubenin hiçbir saati boş kalmamalı; tüm dersler eksiksiz ve doğru saatte yerleşmeli.
- Öğretmen çakışması ve şube çakışması olmayacak şekilde kesin garanti (hard constraint, ihlal edilemez).
