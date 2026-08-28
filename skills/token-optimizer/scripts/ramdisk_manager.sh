#!/usr/bin/env bash
# ramdisk_manager.sh: Gestor de Ramdisk en /dev/shm para AGY.
# Utiliza memoria compartida POSIX de Linux (/dev/shm) para proporcionar 4-8 GiB de almacenamiento
# en RAM ultrarrápido (15 GB/s) a $0 costo de CPU y sin requerir permisos de superusuario (sudo).
# Uso: ./ramdisk_manager.sh [mount|sync|status]

RAMDISK_PATH="/dev/shm/agy-ramdisk"
CACHE_SRC="$HOME/.agents/cache"

case "${1:-status}" in
    mount)
        echo "==> 🚀 Inicializando Ramdisk en $RAMDISK_PATH..."
        mkdir -p "$RAMDISK_PATH/cache"
        if [ -d "$CACHE_SRC" ]; then
            cp -ru "$CACHE_SRC/"* "$RAMDISK_PATH/cache/" 2>/dev/null || true
        fi
        echo "✅ Ramdisk en RAM activo y sincronizado en $RAMDISK_PATH."
        ;;
    sync)
        echo "==> 💾 Sincronizando Ramdisk a almacenamiento persistente..."
        mkdir -p "$CACHE_SRC"
        if [ -d "$RAMDISK_PATH/cache" ]; then
            cp -ru "$RAMDISK_PATH/cache/"* "$CACHE_SRC/" 2>/dev/null || true
        fi
        echo "✅ Caché en RAM respaldada en $CACHE_SRC."
        ;;
    status)
        echo "======================================================================"
        echo "⚡ ESTADO DE MEMORIA RAM Y RAMDISK (/dev/shm)"
        echo "======================================================================"
        df -h /dev/shm | awk 'NR==1 || NR==2'
        echo "----------------------------------------------------------------------"
        if [ -d "$RAMDISK_PATH" ]; then
            SIZE=$(du -sh "$RAMDISK_PATH" 2>/dev/null | cut -f1)
            echo "✓ Ramdisk Activo en $RAMDISK_PATH (Tamaño actual: $SIZE)"
        else
            echo "- Ramdisk no montado (Usa './ramdisk_manager.sh mount' para activarlo)"
        fi
        echo "======================================================================"
        ;;
    *)
        echo "Uso: $0 [mount|sync|status]"
        exit 1
        ;;
esac
