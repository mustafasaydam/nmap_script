# Tüm portları tara (1-65535)
python3 main.py -t 192.168.1.0/24 -p 1-65535 -a

# Hızlı modda bile olsa tüm portları tara
python3 main.py -t 192.168.1.0/24 -p 1-65535 -q -a

# Belirli bir IP aralığında tüm portları tara
python3 main.py -t 10.0.0.1-254 -p 1-65535 -a

# Çıktı dosyası belirterek
python3 main.py -t 192.168.1.0/24 -p 1-65535 -o full_scan.json -a
