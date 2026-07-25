#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube Downloader to MP3
Script para descargar videos de YouTube y convertirlos a MP3
Compatible con Termux y Pydroid
"""

import os
import sys
import subprocess
import json
import re
import time
import shutil
from pathlib import Path
from datetime import datetime
import platform

# Colores para la terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    WHITE = '\033[97m'
    MAGENTA = '\033[35m'

class YouTubeDownloader:
    def __init__(self):
        self.download_dir = self.get_download_directory()
        self.downloaded_files = []
        self.ytdlp_path = self.find_ytdlp()
        self.ffmpeg_path = self.find_ffmpeg()
        
    def get_download_directory(self):
        """Determina el directorio de descarga adecuado"""
        # Rutas posibles en orden de prioridad
        possible_paths = [
            "/storage/emulated/0/Termux music",
            "/storage/emulated/0/Music/YouTube",
            "/sdcard/Music/YouTube",
            os.path.join(os.path.expanduser("~"), "Music", "YouTube"),
            os.path.join(os.getcwd(), "descargas_youtube")
        ]
        
        for path in possible_paths:
            try:
                # Intentar crear el directorio
                os.makedirs(path, exist_ok=True)
                # Verificar si se puede escribir
                test_file = os.path.join(path, "test.txt")
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return path
            except:
                continue
        
        # Si todo falla, usar directorio local
        local_path = os.path.join(os.getcwd(), "descargas_youtube")
        os.makedirs(local_path, exist_ok=True)
        return local_path
    
    def find_ytdlp(self):
        """Busca yt-dlp en el sistema"""
        # Verificar si está instalado como módulo
        try:
            import yt_dlp
            return "module"
        except ImportError:
            pass
        
        # Buscar en PATH
        ytdlp_paths = ["yt-dlp", "ytdlp"]
        for cmd in ytdlp_paths:
            if shutil.which(cmd):
                return cmd
        
        # Buscar en ubicaciones comunes de Termux
        termux_paths = [
            "/data/data/com.termux/files/usr/bin/yt-dlp",
            "/data/data/com.termux/files/usr/bin/ytdlp"
        ]
        for path in termux_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def find_ffmpeg(self):
        """Busca ffmpeg en el sistema"""
        if shutil.which("ffmpeg"):
            return "ffmpeg"
        
        # Buscar en ubicaciones comunes de Termux
        termux_paths = [
            "/data/data/com.termux/files/usr/bin/ffmpeg"
        ]
        for path in termux_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def check_dependencies(self):
        """Verifica las dependencias necesarias"""
        missing = []
        
        # Verificar yt-dlp
        if self.ytdlp_path is None:
            missing.append("yt-dlp")
        
        # Verificar ffmpeg
        if self.ffmpeg_path is None:
            missing.append("ffmpeg")
        
        if missing:
            print(f"\n{Colors.RED}❌ Faltan dependencias:{Colors.END}")
            for dep in missing:
                if dep == "yt-dlp":
                    print(f"  {Colors.YELLOW}• yt-dlp: Herramienta para descargar videos{Colors.END}")
                    print(f"    {Colors.CYAN}Instalación en Termux:{Colors.END} pkg install yt-dlp")
                    print(f"    {Colors.CYAN}Instalación en otros sistemas:{Colors.END} pip install yt-dlp")
                elif dep == "ffmpeg":
                    print(f"  {Colors.YELLOW}• ffmpeg: Herramienta para convertir audio{Colors.END}")
                    print(f"    {Colors.CYAN}Instalación en Termux:{Colors.END} pkg install ffmpeg")
                    print(f"    {Colors.CYAN}Instalación en otros sistemas:{Colors.END} pip install ffmpeg-python")
            
            input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.END}")
            return False
        else:
            print(f"\n{Colors.GREEN}✅ Todas las dependencias están instaladas{Colors.END}")
            return True
    
    def show_banner(self):
        """Muestra el banner del programa"""
        os.system('cls' if os.name == 'nt' else 'clear')
        banner = f"""
{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════════╗
║                                                       ║
║   🎵  YOUTUBE DOWNLOADER TO MP3  🎵                   ║
║                                                       ║
║   Descarga videos de YouTube y conviértelos a MP3    ║
║                                                       ║
╚═══════════════════════════════════════════════════════════╝{Colors.END}
        """
        print(banner)
        print(f"{Colors.WHITE}📁 Directorio de descarga: {self.download_dir}{Colors.END}")
        print(f"{Colors.WHITE}🖥️  Sistema: {platform.system()} {platform.release()}{Colors.END}")
        print()
    
    def show_menu(self):
        """Muestra el menú principal"""
        print(f"\n{Colors.BOLD}┌─────────── MENÚ PRINCIPAL ───────────┐{Colors.END}")
        print(f"{Colors.CYAN}1.{Colors.END} 📥 Descargar video individual")
        print(f"{Colors.CYAN}2.{Colors.END} 📋 Descargar playlist")
        print(f"{Colors.CYAN}3.{Colors.END} 📂 Ver archivos descargados")
        print(f"{Colors.CYAN}4.{Colors.END} 🔧 Verificar dependencias")
        print(f"{Colors.CYAN}5.{Colors.END} 📁 Cambiar directorio de descarga")
        print(f"{Colors.CYAN}6.{Colors.END} ❌ Salir")
        print(f"{Colors.BOLD}└────────────────────────────────────────┘{Colors.END}")
        
        return input(f"\n{Colors.GREEN}🔹 Selecciona una opción (1-6): {Colors.END}")
    
    def get_video_info(self, url):
        """Obtiene información del video sin descargarlo"""
        try:
            if self.ytdlp_path == "module":
                import yt_dlp
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return {
                        'title': info.get('title', 'Desconocido'),
                        'channel': info.get('uploader', 'Desconocido'),
                        'duration': info.get('duration', 0),
                        'views': info.get('view_count', 0),
                        'upload_date': info.get('upload_date', 'Desconocida'),
                        'thumbnail': info.get('thumbnail', '')
                    }
            else:
                # Usar yt-dlp desde línea de comandos
                cmd = [self.ytdlp_path, '--dump-json', '--no-warnings', '--quiet', url]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    info = json.loads(result.stdout.strip().split('\n')[-1])
                    return {
                        'title': info.get('title', 'Desconocido'),
                        'channel': info.get('uploader', 'Desconocido'),
                        'duration': info.get('duration', 0),
                        'views': info.get('view_count', 0),
                        'upload_date': info.get('upload_date', 'Desconocida'),
                        'thumbnail': info.get('thumbnail', '')
                    }
                return None
        except Exception as e:
            print(f"{Colors.RED}❌ Error al obtener información: {e}{Colors.END}")
            return None
    
    def format_duration(self, seconds):
        """Convierte segundos a formato HH:MM:SS"""
        if not seconds:
            return "Desconocida"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    
    def format_date(self, date_str):
        """Formatea la fecha YYYYMMDD"""
        if not date_str or date_str == 'Desconocida':
            return "Desconocida"
        try:
            date = datetime.strptime(date_str, '%Y%m%d')
            return date.strftime('%d/%m/%Y')
        except:
            return date_str
    
    def format_size(self, size_bytes):
        """Convierte bytes a formato legible"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def show_video_info(self, info):
        """Muestra información del video"""
        if not info:
            print(f"{Colors.RED}❌ No se pudo obtener información del video{Colors.END}")
            return
        
        print(f"\n{Colors.BOLD}╔═══════════════════════════════════════════╗{Colors.END}")
        print(f"{Colors.BOLD}║       INFORMACIÓN DEL VIDEO              ║{Colors.END}")
        print(f"{Colors.BOLD}╚═══════════════════════════════════════════╝{Colors.END}")
        print(f"{Colors.CYAN}📌 Título:{Colors.END} {info['title']}")
        print(f"{Colors.CYAN}🎤 Canal:{Colors.END} {info['channel']}")
        print(f"{Colors.CYAN}⏱️  Duración:{Colors.END} {self.format_duration(info['duration'])}")
        print(f"{Colors.CYAN}👁️  Vistas:{Colors.END} {info['views']:,}")
        print(f"{Colors.CYAN}📅 Fecha:{Colors.END} {self.format_date(info['upload_date'])}")
        print(f"{Colors.BOLD}╔═══════════════════════════════════════════╗{Colors.END}")
    
    def select_quality(self):
        """Permite seleccionar la calidad del audio"""
        qualities = {
            '1': {'name': '🔥 Mejor calidad', 'bitrate': '320k', 'format': 'bestaudio/best'},
            '2': {'name': '🎧 Buena calidad', 'bitrate': '192k', 'format': 'bestaudio[abr<=192]/bestaudio'},
            '3': {'name': '📱 Calidad normal', 'bitrate': '128k', 'format': 'bestaudio[abr<=128]/bestaudio'},
            '4': {'name': '💾 Baja calidad', 'bitrate': '64k', 'format': 'bestaudio[abr<=64]/bestaudio'}
        }
        
        print(f"\n{Colors.BOLD}┌─────────── CALIDAD DE AUDIO ───────────┐{Colors.END}")
        for key, value in qualities.items():
            print(f"{Colors.CYAN}{key}.{Colors.END} {value['name']}")
        print(f"{Colors.BOLD}└──────────────────────────────────────────┘{Colors.END}")
        
        while True:
            choice = input(f"\n{Colors.GREEN}🔹 Selecciona calidad (1-4): {Colors.END}")
            if choice in qualities:
                return qualities[choice]
            print(f"{Colors.RED}❌ Opción inválida. Intenta de nuevo.{Colors.END}")
    
    def download_video(self, url, quality, include_thumbnail=True, is_playlist=False):
        """Descarga el video y lo convierte a MP3"""
        try:
            # Configurar opciones de descarga
            output_template = os.path.join(self.download_dir, '%(title)s.%(ext)s')
            
            if is_playlist:
                output_template = os.path.join(self.download_dir, '%(playlist)s/%(title)s.%(ext)s')
                os.makedirs(os.path.join(self.download_dir, 'playlist'), exist_ok=True)
            
            ydl_opts = {
                'format': quality['format'],
                'outtmpl': output_template,
                'quiet': False,
                'no_warnings': False,
                'ignoreerrors': True,
                'no_color': False,
                'progress_hooks': [self.progress_hook],
                'postprocessors': [
                    {
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': quality['bitrate'].replace('k', ''),
                    },
                ],
            }
            
            # Añadir thumbnail si está activado
            if include_thumbnail:
                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegThumbnailsConvertor',
                    'format': 'jpg',
                })
                ydl_opts['postprocessors'].append({
                    'key': 'EmbedThumbnail',
                })
            
            # Añadir metadatos
            ydl_opts['postprocessors'].append({
                'key': 'FFmpegMetadata',
                'add_metadata': True,
            })
            
            print(f"\n{Colors.GREEN}▶️  Descargando y convirtiendo...{Colors.END}")
            
            # Iniciar descarga
            if self.ytdlp_path == "module":
                import yt_dlp
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            else:
                # Usar línea de comandos
                cmd = [self.ytdlp_path]
                for key, value in ydl_opts.items():
                    if isinstance(value, list):
                        cmd.append(f'--{key}')
                        for item in value:
                            cmd.append(f'--{key}')
                            for k, v in item.items():
                                if isinstance(v, str):
                                    cmd.append(f'--{k}')
                                    cmd.append(v)
                    else:
                        cmd.append(f'--{key}')
                        if isinstance(value, str):
                            cmd.append(value)
                cmd.append(url)
                
                subprocess.run(cmd, check=True)
            
            print(f"\n{Colors.GREEN}✅ ¡Descarga completada exitosamente!{Colors.END}")
            
            # Listar archivos descargados
            self.list_downloaded_files()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}⚠️  Descarga cancelada por el usuario{Colors.END}")
        except Exception as e:
            print(f"\n{Colors.RED}❌ Error durante la descarga: {e}{Colors.END}")
    
    def progress_hook(self, d):
        """Hook para mostrar progreso de descarga"""
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', '0 MiB/s').strip()
                eta = d.get('_eta_str', '0s').strip()
                print(f"\r{Colors.CYAN}📥 Descargando: {percent}  ⚡ {speed}  ⏱️ {eta}{Colors.END}", end='')
            except:
                pass
        elif d['status'] == 'finished':
            print(f"\n{Colors.GREEN}✅ Archivo descargado{Colors.END}")
    
    def list_downloaded_files(self):
        """Lista los archivos descargados con su tamaño"""
        print(f"\n{Colors.BOLD}┌─────────── ARCHIVOS DESCARGADOS ───────────┐{Colors.END}")
        
        if not os.path.exists(self.download_dir):
            print(f"{Colors.YELLOW}📂 No hay archivos descargados{Colors.END}")
            return
        
        files = []
        for root, dirs, filenames in os.walk(self.download_dir):
            for filename in filenames:
                if filename.endswith('.mp3'):
                    filepath = os.path.join(root, filename)
                    size = os.path.getsize(filepath)
                    files.append((filename, size))
        
        if not files:
            print(f"{Colors.YELLOW}📂 No hay archivos MP3 descargados{Colors.END}")
            return
        
        files.sort(key=lambda x: x[0])
        for filename, size in files:
            # Truncar nombre largo
            if len(filename) > 40:
                filename = filename[:37] + '...'
            print(f"{Colors.CYAN}🎵{Colors.END} {filename} - {self.format_size(size)}")
        
        print(f"{Colors.BOLD}└────────────────────────────────────────────┘{Colors.END}")
        print(f"{Colors.WHITE}📊 Total: {len(files)} archivos{Colors.END}")
    
    def download_playlist(self):
        """Descarga una playlist completa"""
        url = input(f"\n{Colors.GREEN}🔹 Ingresa la URL de la playlist: {Colors.END}")
        
        if not url:
            print(f"{Colors.RED}❌ URL no proporcionada{Colors.END}")
            return
        
        print(f"\n{Colors.CYAN}🔍 Obteniendo información de la playlist...{Colors.END}")
        
        # Obtener información de la playlist
        info = self.get_video_info(url)
        if not info:
            print(f"{Colors.RED}❌ No se pudo obtener información de la playlist{Colors.END}")
            return
        
        # Preguntar calidad
        quality = self.select_quality()
        
        # Preguntar por thumbnail
        include_thumbnail = input(f"\n{Colors.GREEN}🔹 ¿Incluir portada? (s/n): {Colors.END}").lower() == 's'
        
        # Descargar playlist
        self.download_video(url, quality, include_thumbnail, is_playlist=True)
    
    def change_directory(self):
        """Cambia el directorio de descarga"""
        print(f"\n{Colors.CYAN}📁 Directorio actual: {self.download_dir}{Colors.END}")
        new_dir = input(f"\n{Colors.GREEN}🔹 Ingresa nuevo directorio (o Enter para mantener): {Colors.END}")
        
        if new_dir:
            try:
                os.makedirs(new_dir, exist_ok=True)
                self.download_dir = new_dir
                print(f"{Colors.GREEN}✅ Directorio cambiado a: {new_dir}{Colors.END}")
            except Exception as e:
                print(f"{Colors.RED}❌ Error al cambiar directorio: {e}{Colors.END}")
        
        input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.END}")
    
    def run(self):
        """Ejecuta el programa principal"""
        while True:
            self.show_banner()
            
            # Verificar dependencias primero
            if not self.check_dependencies():
                input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.END}")
                continue
            
            option = self.show_menu()
            
            if option == '1':
                # Descargar video individual
                url = input(f"\n{Colors.GREEN}🔹 Ingresa la URL del video: {Colors.END}")
                
                if not url:
                    print(f"{Colors.RED}❌ URL no proporcionada{Colors.END}")
                    input(f"{Colors.YELLOW}Presiona Enter para continuar...{Colors.END}")
                    continue
                
                print(f"\n{Colors.CYAN}🔍 Obteniendo información del video...{Colors.END}")
                info = self.get_video_info(url)
                
                if info:
                    self.show_video_info(info)
                else:
                    print(f"{Colors.RED}❌ No se pudo obtener información del video{Colors.END}")
                
                quality = self.select_quality()
                
                include_thumbnail = input(f"\n{Colors.GREEN}🔹 ¿Incluir portada? (s/n): {Colors.END}").lower() == 's'
                
                self.download_video(url, quality, include_thumbnail)
                
                input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.END}")
            
            elif option == '2':
                self.download_playlist()
                input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.END}")
            
            elif option == '3':
                self.list_downloaded_files()
                input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.END}")
            
            elif option == '4':
                self.check_dependencies()
                input(f"\n{Colors.YELLOW}Presiona Enter para continuar...{Colors.END}")
            
            elif option == '5':
                self.change_directory()
            
            elif option == '6':
                print(f"\n{Colors.GREEN}👋 ¡Gracias por usar el descargador de YouTube!{Colors.END}")
                break
            
            else:
                print(f"{Colors.RED}❌ Opción inválida{Colors.END}")
                time.sleep(1)

if __name__ == "__main__":
    try:
        downloader = YouTubeDownloader()
        downloader.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Programa terminado por el usuario{Colors.END}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error inesperado: {e}{Colors.END}")
        sys.exit(1)