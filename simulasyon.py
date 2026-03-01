import pygame
import random
import sys
import time
import math
from datetime import datetime, timedelta

# --- AYARLAR ---
GENISLIK, YUKSEKLIK = 1200, 850
FPS = 60
BESIN_SAYISI = 150 # Besin odağını artırmak için sayı yükseltildi

TUR_VERILERI = {
    "Amip": [(50, 255, 120), "Daire", 0.1, 7],
    "Kamçılı": [(255, 50, 50), "Üçgen", 0.8, 6],
    "Radyolar": [(180, 50, 255), "Yıldız", 0.05, 9],
    "Spirok": [(255, 255, 0), "Elips", 0.4, 5],
    "Kalkanlı": [(50, 150, 255), "Kare", 0.05, 11],
    "Okçu": [(255, 150, 50), "Ok", 0.7, 6],
    "Kristal": [(200, 200, 255), "Altıgen", 0.1, 8],
    "Parames": [(100, 255, 200), "Kapsül", 0.2, 10],
    "Vorti": [(255, 100, 180), "Spiral", 0.2, 6],
    "Nektron": [(150, 150, 150), "Baklava", 0.5, 5],
    "Hibrit": [(255, 255, 255), "Hibrit", 0.4, 8]
}

MEVSIMLER = [
    {"ad": "BAHAR", "renk": (10, 25, 15), "tuketim": 0.02, "besin": 60},
    {"ad": "ZEHIR", "renk": (35, 10, 45), "tuketim": 0.08, "besin": 40},
    {"ad": "SU", "renk": (5, 20, 45), "tuketim": 0.03, "besin": 50},
    {"ad": "BUZ", "renk": (25, 25, 35), "tuketim": 0.05, "besin": 30}
]

class Organizma:
    def __init__(self, x=None, y=None, tur=None, genetik=None):
        self.pos = pygame.Vector2(x or random.randint(100, 1100), y or random.randint(100, 750))
        self.tur = tur or random.choice(list(TUR_VERILERI.keys())[:-1])
        veriler = TUR_VERILERI[self.tur]
        
        if genetik:
            self.hiz_geni = max(0.3, min(2.5, genetik['hiz'] + random.uniform(-0.1, 0.1)))
            self.boyut = max(4, min(14, genetik['boyut'] + random.uniform(-0.5, 0.5)))
            self.renk = genetik.get('renk', veriler[0])
        else:
            self.hiz_geni = random.uniform(0.6, 1.4) * (veriler[2] + 0.5)
            self.boyut = veriler[3]
            self.renk = veriler[0]

        self.enerji = 100.0
        self.hayatta = True
        self.hiz = pygame.Vector2(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2))
        self.pulse = random.uniform(0, 6.2)
        self.max_omur = random.randint(1200, 2500)
        self.dogum_an = time.time()

    def guncelle(self, digerleri, besinler, mevsim, t_scale):
        self.pulse += 0.05 * t_scale
        
        # Tutarsız ve Serbest Hareket (Brownian Benzeri)
        drift = pygame.Vector2(random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1))
        self.hiz += drift * t_scale
        
        # Enerji Tüketimi (Hareket maliyeti yüksek)
        tuketim = (mevsim["tuketim"] + (self.hiz.length() * 0.02)) * t_scale
        self.enerji -= tuketim
        
        if self.enerji <= 0: self.hayatta = False; return

        # Akışkan Direnç
        self.hiz *= (0.97 ** t_scale)
        
        # Gıda Odaklı Navigasyon
        gorus = 180 if self.enerji < 50 else 100
        target_found = False
        for b in besinler:
            diff = b - self.pos
            if diff.length_squared() < gorus**2:
                self.hiz += diff.normalize() * 0.08 * t_scale
                target_found = True
                if diff.length_squared() < 400:
                    self.enerji = min(160, self.enerji + mevsim["besin"])
                    b.update(random.randint(20, 1180), random.randint(20, 830))
                break # En yakın gıdaya odaklan

        # Hibritleşme (Çok nadir)
        if not target_found:
            for d in digerleri[:10]:
                if d != self and self.tur != d.tur and self.enerji > 110 and d.enerji > 110:
                    if random.random() < 0.0005 * t_scale:
                        return ("hibrit", d)

        if self.hiz.length() > self.hiz_geni: self.hiz.scale_to_length(self.hiz_geni)
        self.pos += self.hiz * t_scale
        self.pos.x %= GENISLIK; self.pos.y %= YUKSEKLIK
        return None

    def ciz(self, ekran):
        px, py = int(self.pos.x), int(self.pos.y)
        r = int(self.boyut + math.sin(self.pulse)*1.0)
        oran = max(0.4, min(1.0, self.enerji / 100))
        c = tuple(int(k * oran) for k in self.renk)
        sekil = TUR_VERILERI[self.tur][1]

        # Şekil Çizimleri
        if sekil == "Hibrit":
            pygame.draw.circle(ekran, c, (px, py), r)
            pygame.draw.circle(ekran, (200,200,200), (px, py), r+2, 1)
        elif sekil == "Daire": pygame.draw.circle(ekran, c, (px, py), r)
        elif sekil == "Üçgen": pygame.draw.polygon(ekran, c, [(px, py-r), (px-r, py+r), (px+r, py+r)])
        elif sekil == "Kare": pygame.draw.rect(ekran, c, (px-r, py-r, r*2, r*2))
        elif sekil == "Yıldız":
            for i in range(3):
                a = i * math.pi / 1.5
                pygame.draw.line(ekran, c, (px-r*math.cos(a), py-r*math.sin(a)), (px+r*math.cos(a), py+r*math.sin(a)), 2)
        elif sekil == "Elips": pygame.draw.ellipse(ekran, c, (px-r*1.2, py-r//2, r*2.4, r))
        elif sekil == "Altıgen":
            pts = [(px + r * math.cos(a), py + r * math.sin(a)) for a in [i*math.pi/3 for i in range(6)]]
            pygame.draw.polygon(ekran, c, pts)
        else: pygame.draw.circle(ekran, c, (px, py), r) # Diğerleri için varsayılan

        # CAN BARI
        bar_w = 16
        pygame.draw.rect(ekran, (40, 40, 40), (px - bar_w//2, py - r - 8, bar_w, 3))
        pygame.draw.rect(ekran, (0, 255, 100) if self.enerji > 30 else (255, 50, 0), 
                         (px - bar_w//2, py - r - 8, int(bar_w * (self.enerji/100)), 3))

def ana_dongu():
    pygame.init()
    ekran = pygame.display.set_mode((GENISLIK, YUKSEKLIK))
    saat = pygame.time.Clock()
    font = pygame.font.SysFont("Consolas", 13, bold=True)
    
    sim_zamani = datetime.now()
    time_scale = 1.0
    # Başlangıçta Sadece 10 Varlık!
    varliklar = [Organizma() for _ in range(10)]
    besinler = [pygame.Vector2(random.randint(20, 1180), random.randint(20, 830)) for _ in range(BESIN_SAYISI)]
    
    input_rect = pygame.Rect(GENISLIK-120, 20, 100, 25)
    user_text, max_pop, active_input = '400', 400, False
    pop_history = {k: [] for k in TUR_VERILERI.keys()}
    mevsim_idx, mevsim_timer = 0, 0

    while True:
        dt = saat.tick(FPS) / 1000.0
        sim_zamani += timedelta(seconds=dt * time_scale)
        mevsim_timer += 1 * time_scale
        if mevsim_timer > 1200: mevsim_idx = (mevsim_idx + 1) % len(MEVSIMLER); mevsim_timer = 0
        m_aktif = MEVSIMLER[mevsim_idx]
        ekran.fill(m_aktif["renk"])

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                active_input = input_rect.collidepoint(event.pos)
                if pygame.Rect(GENISLIK-120, 60, 100, 25).collidepoint(event.pos):
                    for _ in range(10): varliklar.append(Organizma())
            if event.type == pygame.KEYDOWN and active_input:
                if event.key == pygame.K_RETURN: active_input = False
                elif event.key == pygame.K_BACKSPACE: user_text = user_text[:-1]
                else: user_text += event.unicode
                try: max_pop = int(user_text)
                except: pass

        counts = {k: 0 for k in TUR_VERILERI.keys()}
        for v in varliklar: counts[v.tur] += 1
        
        yeni_nesil = []
        for v in varliklar:
            res = v.guncelle(varliklar, besinler, m_aktif, time_scale)
            
            if res and res[0] == "hibrit":
                d = res[1]
                v.enerji -= 60; d.enerji -= 60
                yeni_nesil.append(Organizma(v.pos.x, v.pos.y, "Hibrit", {
                    'hiz': (v.hiz_geni + d.hiz_geni)/2, 'boyut': (v.boyut + d.boyut)/2,
                    'renk': tuple((v.renk[i]+d.renk[i])//2 for i in range(3))
                }))
            elif v.enerji > 140 and len(varliklar) < max_pop:
                v.enerji -= 70
                yeni_nesil.append(Organizma(v.pos.x+3, v.pos.y+3, v.tur, {'hiz': v.hiz_geni, 'boyut': v.boyut}))

        varliklar = [v for v in varliklar if v.hayatta]
        varliklar.extend(yeni_nesil)
        
        # Grafik Verisi
        if int(mevsim_timer) % 50 == 0:
            for k in TUR_VERILERI.keys():
                pop_history[k].append(counts[k])
                if len(pop_history[k]) > 140: pop_history[k].pop(0)

        for b in besinler: pygame.draw.circle(ekran, (0, 100, 150), b, 2)
        for v in varliklar: v.ciz(ekran)

        # UI & GRAFİK
        graph_area = pygame.Rect(250, YUKSEKLIK - 110, 750, 90)
        pygame.draw.rect(ekran, (5, 5, 10), graph_area)
        for t_ad, t_renk_data in TUR_VERILERI.items():
            history = pop_history[t_ad]
            if len(history) > 1:
                pts = [(graph_area.x + (i * 5.4), graph_area.y + 90 - (val * 90 / (max_pop/2))) for i, val in enumerate(history)]
                pygame.draw.lines(ekran, t_renk_data[0], False, pts, 1)

        pygame.draw.rect(ekran, (15, 15, 25), (10, 10, 200, 340))
        ui_txt = [f"SAAT : {sim_zamani.strftime('%H:%M:%S')}", f"MEVSIM: {m_aktif['ad']}", f"POP: {len(varliklar)}", "-"*18]
        for i, t in enumerate(ui_txt): ekran.blit(font.render(t, True, (200,200,200)), (20, 20 + i*18))
        for i, (t, s) in enumerate(counts.items()):
            ekran.blit(font.render(f"{t[:7]}: {s}", True, TUR_VERILERI[t][0]), (20, 100 + i*18))

        pygame.draw.rect(ekran, (40,40,50), input_rect); pygame.draw.rect(ekran, (0, 255, 150) if active_input else (100,100,100), input_rect, 1)
        ekran.blit(font.render(user_text, True, (255,255,255)), (input_rect.x+5, input_rect.y+5))
        pygame.draw.rect(ekran, (0, 80, 150), (GENISLIK-120, 60, 100, 25)); ekran.blit(font.render("EKLE", True, (255,255,255)), (GENISLIK-90, 65))

        pygame.display.flip()

if __name__ == "__main__":
    ana_dongu()