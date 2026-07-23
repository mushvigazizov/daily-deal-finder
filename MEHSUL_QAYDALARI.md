# Məhsul və ASIN Qaydaları — Daily Deal Finder

Bu sənəd bir problemi həmişəlik həll etmək üçündür:
**saytda mövcud olmayan Amazon məhsullarının görünməsi.**

Bu qaydalar pipeline-a və n8n workflow-lara yazılmalıdır.

---

## 1. Qızıl qayda

> **Mənbə ASIN-dir, məhsul adı deyil.**

ASIN uydurula bilməz — ya Amazon-da var, ya yoxdur.
Ona görə **hər şey ASIN-dən başlayır.**

### AI ad uydurmur

**Qadağandır:** AI-nin özündən məhsul adı düzəltməsi.

**Qayda:** saytdakı ad **əsl Amazon adına oxşar olmalıdır** — eyni marka, eyni model, eyni əsas xüsusiyyət.

| Amazon-dakı əsl ad | ✅ Düzgün | ❌ Yanlış |
|---|---|---|
| Salewa Denali II Dome Tent 2P | Salewa Denali II — 2 nəfərlik dom çadır | Premium Outdoor Adventure Tent |

AI yalnız adı **qısaldıb səliqəyə salır** — dəyişmir, yeni ad yaratmır.

---

## 2. Düzgün sıralama

Köhnə (yanlış) sıralama:

```
AI məhsul uydurur  →  ASIN axtarılır  →  sayta qoyulur
```

Yeni (düzgün) sıralama:

```
Əsl Amazon məhsulu seçilir  →  ASIN yazılır  →  AI ona məzmun yazır  →  sayta qoyulur
```

Fərq: AI artıq **nə yazacağını** yox, **kim haqqında yazacağını** bilir.

---

## 3. Məhsul seçim kriteriyaları

Hansı məhsulun sayta düşəcəyini bu meyarlar müəyyən edir.

### Mənbə: Amazon Bestseller siyahıları

Məhsullar təsadüfi seçilmir. Mənbə budur:

```
https://www.amazon.de/gp/bestsellers/<kateqoriya>
```

Bu siyahı Amazon-un öz real satış sıralamasıdır və hər saat yenilənir.

Əlavə siqnallar: **"Bestseller"** və **"Amazon's Choice"** nişanları.

### Filtrlər

| Meyar | Tələb | Niyə |
|---|---|---|
| Reytinq | **4.3 – 4.8** | Yüksək keyfiyyət |
| Rəy sayı | **ən azı 200** | Real satış sübutu |
| Qiymət | **20 – 150 €** | Yaxşı komissiya, az geri qaytarma |
| Satıcı | Marka özü və ya Amazon | Stok etibarlıdır |
| Mövcudluq | Anbarda çox var | Ölü link olmasın |
| Çeşid | Rəng/ölçü variantları var | Daha çox alıcıya uyğun gəlir |


### Anbar (stok) siqnalları

Amazon dəqiq say göstərmir, amma bunlar oxunur:

| Səhifədə yazılıb | Mənası | Qərar |
|---|---|---|
| "Auf Lager" | Bol var | ✅ Qəbul |
| "Nur noch 3 auf Lager" | Azalır, tezliklə bitəcək | ❌ Rədd |
| "Derzeit nicht verfügbar" | Yoxdur | ❌ Rədd |
| Göndərən: Amazon | Stok idarə olunur | ✅ Üstünlük |

Az stoklu məhsul bir neçə gündən sonra ölü linkə çevrilir — ona görə qəbul edilmir.

### Çeşid (variant) qaydası

Rəng və ölçü variantları olan məhsullar üstünlük təşkil edir — daha çox alıcıya uyğun gəlir.

⚠️ **Amma diqqət:** hər variantın **öz ayrıca ASIN-i** var.

| Variant | ASIN |
|---|---|
| Qara, M ölçü | B08XXXXXX1 |
| Mavi, M ölçü | B08XXXXXX2 |
| Qara, L ölçü | B08XXXXXX3 |

**Qayda:** biz **bir konkret variantı** seçirik və onun ASIN-ini yazırıq.
Saytdakı şəkil də **məhz həmin variantın** rəngi/ölçüsü olmalıdır — yoxsa alıcı gözlədiyindən fərqli səhifəyə düşür.

### ⚠️ 5.0 ulduz qəbul edilmir

Bu, gözlənilməz görünə bilər, amma:

| Reytinq | Rəy sayı | Qərar |
|---|---|---|
| 5.0 | 15 | ❌ Rədd — çox güman saxta rəylər |
| 4.6 | 3 400 | ✅ Qəbul — real və məşhur |
| 4.9 | 40 | ❌ Rədd — kifayət qədər sübut yoxdur |

**Qayda:** 5.0 reytinq özü-özlüyündə etibar yaratmır. Etibar yaradan **rəy sayıdır**.

### "Ən çox axtarılan" haqqında

Amazon axtarış statistikasını açıq paylaşmır. Onun əvəzinə bu göstəricilər istifadə olunur:

| Göstərici | Harada |
|---|---|
| Bestseller sıralaması (BSR) | Məhsul səhifəsində, "Amazon Bestseller-Rang" |
| Amazon axtarış təklifləri | Axtarış xanasına yazanda çıxan siyahı |
| Mövsümi tələb | Google Trends |

BSR nə qədər kiçikdirsə (məs. #1 – #100), məhsul o qədər çox satılır.

---

## 4. Məhsulun sayta düşmə şərtləri

Bir məhsul yalnız bu 4 şərt ödənəndə saytda görünə bilər:

| № | Şərt | Sahə |
|---|---|---|
| 1 | Əsl ASIN var (10 simvol) | `amazon_asin` |
| 2 | Əl ilə təsdiqlənib | `asin_verified: true` |
| 3 | Link növü məhsuldur | `amazon_link_type: "product"` |
| 4 | Ad əsl Amazon adına uyğundur (marka + model) | `title` |
| 5 | Şəkil və məzmun hazırdır | `image`, `description` |

Bir şərt belə pozulursa → məhsul **gizlədilir**, silinmir.

---

## 5. Yeni sahə: `status`

Hər məhsulda bu sahə olmalıdır:

| Dəyər | Mənası | Saytda görünür? |
|---|---|---|
| `live` | Hər şey qaydasındadır | ✅ Bəli |
| `hidden` | Problem var (ASIN yox, link xarab) | ❌ Xeyr |
| `draft` | Hələ hazırlanır | ❌ Xeyr |

**Vacib:** heç bir məhsul silinmir. Problemli olan sadəcə `hidden` olur.
Belə olsa məlumat itmir və sonra düzəldilə bilər.

---

## 6. ASIN necə əlavə olunur (əl ilə, bir dəfəlik)

Hər yeni məhsul üçün:

1. amazon.de saytını aç
2. Əsl məhsulu tap və səhifəsini aç
3. Ünvan sətrindən `/dp/XXXXXXXXXX` hissəsini götür
4. Həmin 10 simvolu `amazon_asin` sahəsinə yaz
5. `asin_verified: true` yaz
6. `verification_source: "manual"` və tarixi yaz

Bir məhsul üçün təxminən **30 saniyə** çəkir.

⚠️ **Niyə əl ilə?** Amazon avtomatik yoxlamaları tez-tez bloklayır.
Ona görə ilk daxiletmə əl ilə olmalıdır — bu, 100% etibarlı yeganə yoldur.

---

## 7. Avtomatik nəzarət (pipeline-ın sonunda)

Quality Validator hər dəfə bunları yoxlamalıdır:

- [ ] `amazon_asin` var və 10 simvoldur
- [ ] `asin_verified` = true
- [ ] `amazon_url` formatı: `https://www.amazon.de/dp/ASIN`
- [ ] `amazon_link_type` = "product"
- [ ] Şəkil faylı həqiqətən mövcuddur

Şərt pozulursa → validator həmin məhsulu avtomatik `status: hidden` edir
və hesabatda adını yazır.

**Nəticə:** saytda heç vaxt xarab link görünmür.

---

## 8. Aylıq yoxlama

Amazon məhsulları zamanla yox ola bilər.

Ayda bir dəfə:
- Bütün linklər yoxlanılır
- Xarab olanlar `hidden` edilir
- Telegram-a hesabat gəlir

---

## 9. Qısa xülasə

| Qayda | Bir cümlə ilə |
|---|---|
| 1 | ASIN olmadan məhsul yoxdur |
| 2 | ASIN əl ilə, əsl Amazon səhifəsindən götürülür |
| 3 | AI ad uydurmur — ad əsl Amazon adına oxşar olmalıdır |
| 4 | Problemli məhsul silinmir, gizlədilir |
| 5 | Validator hər dəfə yoxlayır |
| 6 | Yalnız bestseller, 4.3+ ulduz və 200+ rəyi olan məhsullar |
| 7 | Stok bol olmalıdır; variantlı məhsulda bir konkret ASIN seçilir |

---

*Bu qaydalar layihənin əsasıdır. Yeni məhsul əlavə edən hər workflow bunlara tabe olmalıdır.*
