# Vercel Deployment Guide

Proyek Fetcher ini telah dikonfigurasi untuk dapat dideploy ke Vercel. Vercel akan menjalankan frontend (React/Vite) sebagai file statis dan backend (FastAPI) sebagai Serverless Functions.

## Langkah-langkah Deployment

1. **Persiapan Repository**
   Pastikan Anda telah melakukan commit dan push semua perubahan terbaru ke repository GitHub Anda.

2. **Import ke Vercel**
   - Buka dashboard Vercel (https://vercel.com/dashboard)
   - Klik **Add New...** > **Project**
   - Pilih repository `Fetcher` dari GitHub Anda dan klik **Import**

3. **Konfigurasi Build**
   Vercel biasanya akan mendeteksi pengaturan secara otomatis berkat file `vercel.json`. Namun, pastikan pengaturan berikut benar:
   
   - **Framework Preset**: Other
   - **Build Command**: `./build.sh` (Penting: override build command default dengan script ini)
   - **Output Directory**: `frontend/dist`
   - **Install Command**: (Biarkan kosong, sudah ditangani oleh build.sh)

4. **Environment Variables**
   Tambahkan environment variables berikut di bagian **Environment Variables** pada pengaturan Vercel:
   
   - `FETCHER_PORT` = `8000` (Opsional, Vercel mengatur port sendiri, tapi baik untuk konsistensi)
   - `FETCHER_DOWNLOAD_DIR` = `/tmp` (Penting: Vercel Serverless Functions hanya memiliki akses tulis ke direktori `/tmp`)
   - `FETCHER_MAX_CONCURRENT` = `3`
   - `FETCHER_RATE_LIMIT` = `60`

5. **Deploy**
   Klik **Deploy** dan tunggu proses build selesai.

## Catatan Penting untuk Vercel (Serverless)

- **Sistem File Sementara**: Serverless Functions di Vercel bersifat *stateless*. File yang diunduh ke `/tmp` hanya akan bertahan selama eksekusi function tersebut. Fitur history mungkin tidak akan berfungsi dengan baik antar request karena file akan hilang setelah function selesai.
- **Batas Waktu Eksekusi (Timeout)**: Vercel memiliki batas waktu eksekusi (10 detik untuk Hobby plan, 60 detik untuk Pro plan). Unduhan file besar mungkin akan gagal jika melebihi batas waktu ini.
- **Keterbatasan FFmpeg**: Vercel Serverless environment (AWS Lambda) mungkin tidak memiliki `ffmpeg` terinstal secara default. Konversi ke MP3 mungkin gagal kecuali Anda menggunakan buildpack khusus atau Lambda layer yang menyertakan FFmpeg.
- **Server-Sent Events (SSE)**: SSE (`/api/download/{id}/progress`) mungkin tidak berfungsi dengan baik di lingkungan serverless karena Vercel akan mem-buffer response atau memutus koneksi yang berjalan lama.

Jika Anda membutuhkan performa maksimal untuk mengunduh file besar atau mengonversi media, disarankan untuk mendeploy aplikasi ini ke VPS (seperti DigitalOcean, Linode, AWS EC2) menggunakan Docker atau langsung di OS.
