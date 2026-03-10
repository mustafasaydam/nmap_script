#!/usr/bin/env python3
import argparse
import os
import sys
import json
import glob
from datetime import datetime

# Modülleri import et
from scanner import PortScanner
from comparator import PortComparator

def list_previous_scans():
    """Önceki tarama dosyalarını listele"""
    scan_files = glob.glob("scan_*.json")
    return sorted(scan_files, reverse=True) if scan_files else []

def get_latest_scan(exclude_current=None):
    """En son tarama dosyasını getir"""
    scans = list_previous_scans()
    if exclude_current and exclude_current in scans:
        scans.remove(exclude_current)
    return scans[0] if scans else None

def print_banner():
    """Banner yazdır"""
    print("""
    ╔══════════════════════════════════════════════╗
    ║     Port Tarama ve Analiz Aracı              ║
    ║     Internal Network Security Scanner         ║
    ║     Kali Linux için optimize edildi          ║
    ╚══════════════════════════════════════════════╝
    """)

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description='Internal Network Port Scanner')
    parser.add_argument('--targets', '-t', help='Hedef IP adresleri (örn: 192.168.1.0/24)')
    parser.add_argument('--ports', '-p', default='1-1000', help='Taranacak portlar (varsayılan: 1-1000)')
    parser.add_argument('--compare', '-c', metavar='FILE', help='Karşılaştırma yapılacak eski tarama dosyası')
    parser.add_argument('--list', '-l', action='store_true', help='Önceki taramaları listele')
    parser.add_argument('--quick', '-q', action='store_true', help='Hızlı tarama (top 100 port)')
    parser.add_argument('--output', '-o', help='Çıktı dosya adı (JSON formatında)')
    parser.add_argument('--auto-compare', '-a', action='store_true', help='Otomatik olarak son tarama ile karşılaştır')
    parser.add_argument('--no-html', action='store_true', help='HTML raporu oluşturma')
    
    args = parser.parse_args()
    
    # Önceki taramaları listele
    if args.list:
        scans = list_previous_scans()
        if scans:
            print("\n📋 Önceki Tarama Dosyaları:")
            print("-" * 50)
            for i, scan in enumerate(scans, 1):
                try:
                    with open(scan, 'r') as f:
                        data = json.load(f)
                        date = datetime.fromisoformat(data['scan_date']).strftime("%Y-%m-%d %H:%M:%S")
                    print(f"  {i}. {scan} ({date})")
                except:
                    print(f"  {i}. {scan} (tarih okunamadı)")
        else:
            print("\n⚠️ Henüz hiç tarama dosyası yok.")
        return
    
    # Hedef kontrolü
    if not args.targets:
        args.targets = input("\n[?] Hedef IP adreslerini girin [192.168.1.0/24]: ").strip()
        if not args.targets:
            args.targets = "192.168.1.0/24"
    
    # Tarama portları
    if args.quick:
        print("[+] Hızlı tarama modu (top 100 port)")
        args.ports = "1-1000"
    else:
        if not args.ports:
            port_input = input("[?] Taranacak port aralığı [1-1000]: ").strip()
            if port_input:
                args.ports = port_input
    
    # Scanner oluştur
    scanner = PortScanner()
    
    # Tarama yap
    print("\n" + "="*60)
    print("YENİ TARAMA BAŞLIYOR".center(60))
    print("="*60)
    
    results = scanner.scan_targets(args.targets, args.ports)
    
    if not results:
        print("\n❌ Tarama başarısız oldu!")
        return
    
    # Sonuçları göster
    scanner.display_summary(results)
    
    # Sonuçları kaydet
    if args.output:
        filename = args.output
        if not filename.endswith('.json'):
            filename += '.json'
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n[+] Sonuçlar kaydedildi: {filename}")
    else:
        filename = scanner.save_results(results)
    
    # Karşılaştırma yap
    compare_with = None
    
    if args.compare:
        compare_with = args.compare
    elif args.auto_compare:
        compare_with = get_latest_scan(exclude_current=filename)
        if compare_with:
            print(f"\n[+] Son tarama ile karşılaştırılıyor: {compare_with}")
        else:
            print("\n[-] Karşılaştırma yapılacak eski tarama bulunamadı.")
    else:
        # Kullanıcıya sor
        previous_scans = list_previous_scans()
        if len(previous_scans) >= 2:
            our_scan = filename.split('/')[-1]
            other_scans = [s for s in previous_scans if s != our_scan]
            
            if other_scans:
                answer = input("\n[?] Son tarama ile karşılaştırma yapmak ister misiniz? (e/H): ").strip().lower()
                if answer in ['e', 'evet', 'y', 'yes']:
                    compare_with = other_scans[0]
    
    # Karşılaştırma yap
    if compare_with:
        print("\n" + "="*60)
        print("KARŞILAŞTIRMA RAPORU".center(60))
        print("="*60)
        
        old_scan = scanner.load_results(compare_with)
        if old_scan:
            comparator = PortComparator(old_scan, results)
            comparator.compare()
            comparator.generate_report()
    
    print("\n" + "="*60)
    print("✅ İŞLEM TAMAMLANDI".center(60))
    print("="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Kullanıcı tarafından durduruldu.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Hata: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
