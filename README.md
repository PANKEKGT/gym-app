# 🏋️ GymPro Web — Kurulum Kılavuzu

## Yerel Test (bilgisayarda)

```bash
pip install flask
python app.py
# Tarayıcıda: http://localhost:5000
```

---

## 🚀 Railway ile Ücretsiz Online Yayınlama

### Adım 1 — GitHub hesabı
https://github.com adresinde ücretsiz hesap açın (varsa atlayın).

### Adım 2 — Bu klasörü GitHub'a yükleyin
1. https://github.com/new → yeni repo oluşturun (ör. `gym-app`)
2. Bilgisayarınıza **GitHub Desktop** indirin: https://desktop.github.com
3. Repoyu klonlayın, içine bu klasörün dosyalarını kopyalayın
4. "Commit to main" → "Push origin" butonuna basın

### Adım 3 — Railway'e bağlayın
1. https://railway.app → "Start a New Project"
2. "Deploy from GitHub repo" seçin
3. `gym-app` reponuzu seçin
4. Otomatik deploy başlar (~2 dakika)
5. "Settings" → "Domains" → "Generate Domain" → linkiniz hazır!

### Sonuç
`https://gym-app-xxx.railway.app` gibi bir link alırsınız.
Bu linki telefonunuzdan açabilirsiniz. ✅

---

## Notlar
- Railway ücretsiz planda ayda 500 saat çalışma hakkı tanır
- Veriler `gym_data.json` dosyasında saklanır
- Railway'de kalıcı depolama için "Volume" eklemeniz gerekebilir
