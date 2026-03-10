#!/usr/bin/env python3
import argparse
import os
import sys
import json
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich import print as rprint
from scanner import PortScanner
from comparator import PortComparator
import glob

console = Console()

def list_previous_scans():
    """Önceki tarama dosyalarını listele"""
    scan_files = glob.glob("scan_*.json")
    if not scan_files:
        return []
    return sorted(scan_files, reverse=True)

def main():
    # Banner
    console.print(Panel.fit(
        "[bold cyan]🔍 Port Tarama ve Analiz Aracı[/bold cyan]\n"
        "[dim]Internal Network Security Scanner[/dim]",
        border_style="cyan"
    ))
    
    parser = argparse.ArgumentParser(description='Internal Network Port Scanner')
    parser.add_argument('--targets', '-t', help='Hedef IP adresleri (örn: 192.168.1.0/24)')
    parser.add_argument('--ports', '-p', default='1-1000', help='Taranacak portlar (varsayılan: 1-1000)')
    parser.add_argument('--compare', '-c', help='Karşılaştırma yapılacak eski tarama dosyası')
    parser.add_argument('--list', '-l', action='store_true', help='Önceki taramaları listele')
    parser.add_argument('--quick', '-q', action='store_true', help='Hızlı tarama (top 100 port)')
    parser.add_argument('--output', '-o', help='Çıktı dosya adı (JSON formatında)')
    
    args = parser.parse_args()
    
    # Önceki taramaları listele
    if args.list:
        scans = list_previous_scans()
        if scans:
            console.print("\n[bold]📋 Önceki Tarama Dosyaları:[/bold]")
            for i, scan in enumerate(scans, 1):
                console.print(f"  {i}. {scan}")
        else:
            console.print("[yellow]⚠️ Henüz hiç tarama dosyası yok.[/yellow]")
        return
    
    # Hedef kontrolü
    if not args.targets:
        args.targets = Prompt.ask("[cyan]Hedef IP adreslerini girin[/cyan]", default="192.168.1.0/24")
    
    # Tarama portları
    if args.quick:
        ports = "top100"
        args.ports = "1-1000"  # Nmap top100 için
    else:
        if not args.ports:
            args.ports = Prompt.ask("[cyan]Taranacak port aralığı[/cyan]", default="1-1000")
    
    # Scanner oluştur
    scanner = PortScanner()
    
    # Tarama yap
    console.rule("[bold cyan]Yeni Tarama Başlıyor[/bold cyan]")
    results = scanner.scan_targets(args.targets, args.ports)
    
    if not results:
        console.print("[red]❌ Tarama başarısız oldu![/red]")
        return
    
    # Sonuçları kaydet - output parametresi varsa onu kullan
    if args.output:
        filename = args.output
        # Eğer .json uzantısı yoksa ekle
        if not filename.endswith('.json'):
            filename += '.json'
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        console.print(f"[green]📁 Sonuçlar kaydedildi: {filename}[/green]")
    else:
        filename = scanner.save_results(results)
    
    # Karşılaştırma yap
    if args.compare:
        old_scan = scanner.load_results(args.compare)
        if old_scan:
            console.rule("[bold yellow]Karşılaştırma Raporu[/bold yellow]")
            comparator = PortComparator(old_scan, results)
            comparator.compare()
            comparator.generate_report()
    else:
        # Son tarama ile karşılaştırmak ister mi?
        previous_scans = list_previous_scans()
        if len(previous_scans) >= 2:  # En az 2 tarama olmalı
            # En son tarama bizim yaptığımız, ondan bir öncekini al
            our_scan = filename.split('/')[-1]  # Sadece dosya adı
            other_scans = [s for s in previous_scans if s != our_scan]
            
            if other_scans and Confirm.ask("\n[cyan]Son tarama ile karşılaştırma yapmak ister misiniz?[/cyan]"):
                latest_scan = other_scans[0]  # En son diğer tarama
                old_scan = scanner.load_results(latest_scan)
                if old_scan:
                    comparator = PortComparator(old_scan, results)
                    comparator.compare()
                    comparator.generate_report()
    
    console.print("\n[bold green]✅ İşlem tamamlandı![/bold green]")
    if args.output:
        console.print(f"[bold]📄 Rapor dosyası: {args.output}[/bold]")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Kullanıcı tarafından durduruldu.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ Beklenmeyen hata: {str(e)}[/red]")
        sys.exit(1)
