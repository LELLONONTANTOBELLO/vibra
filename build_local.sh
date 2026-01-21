#!/bin/bash
# Script per compilare l'APK in locale con Docker
# Funziona su Windows/Mac/Linux con Docker installato

echo "=== Build APK con Docker ==="

# Verifica Docker
if ! command -v docker &> /dev/null; then
    echo "ERRORE: Docker non installato. Installalo da https://www.docker.com/get-started"
    exit 1
fi

# Pulisci build precedenti
rm -rf .buildozer bin

# Compila con Docker (immagine ufficiale Buildozer)
docker run --rm -v "$(pwd)":/app \
    kivy/buildozer:latest \
    buildozer android debug

# Copia APK nella cartella bin
mkdir -p bin
find .buildozer -name "*.apk" -exec cp {} bin/ \;

echo "=== APK compilato in bin/ ==="
ls -lh bin/*.apk