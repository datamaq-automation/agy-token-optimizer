# Guía de Aceleración en Hardware Local (iGPU Vulkan, CPU AVX2 y RAMDisk)

> **Tipo de Documento:** Diátaxis / How-To Guide  
> **Objetivo:** Instrucciones paso a paso para configurar y exprimir al 100% la aceleración gráfica Vulkan, el paralelismo de CPU y el disco en RAM en el ecosistema AGY.

---

## 1. Verificación del Hardware del Sistema

Antes de aplicar la configuración, comprueba la presencia de los componentes:

```bash
# 1. Comprobar hilos de CPU y soporte AVX2
lscpu | grep -E "Model name|CPU\(s\):|Thread"

# 2. Comprobar memoria disponible en RAMDisk tmpfs (/dev/shm)
df -h /dev/shm

# 3. Comprobar tarjeta gráfica integrada y soporte Vulkan
vulkaninfo | grep -E "deviceName|deviceType|driverName"
cat /sys/class/drm/card0/device/mem_info_vram_total
```
*Valores esperados:* Dispositivo `AMD Radeon Vega 11 Graphics`, driver `radv` (Mesa) y 2 GiB de VRAM (`2147483648` bytes).

---

## 2. Activación de la iGPU Vega 11 en Ollama (Vulkan Compute)

Por defecto, Ollama descarta GPUs integradas a menos que se configure explícitamente la variable `OLLAMA_IGPU_ENABLE=1`.

### Paso 1: Crear archivo de override en systemd
```bash
sudo mkdir -p /etc/systemd/system/ollama.service.d

cat << 'OVERRIDE_EOF' | sudo tee /etc/systemd/system/ollama.service.d/igpu.conf
[Service]
Environment="OLLAMA_IGPU_ENABLE=1"
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_NUM_THREADS=8"
OVERRIDE_EOF
```

### Paso 2: Recargar y reiniciar el servicio
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Paso 3: Verificar que el modelo corre en GPU
Ejecuta una petición de prueba y consulta el procesador asignado:
```bash
curl -s http://localhost:11434/api/generate -d '{"model": "qwen2.5-coder:1.5b", "prompt": "hola", "stream": false}' > /dev/null
ollama ps
```
*Salida esperada:*
```text
NAME                  ID              SIZE      PROCESSOR       CONTEXT
qwen2.5-coder:1.5b    d7372fd82851    1.2 GB    100% GPU (Vulkan)   4096
```

---

## 3. Uso del Workspace y Caché en RAMDisk (`/dev/shm`)

El adaptador `RAMDiskOptimizer` permite clonar el repositorio en la memoria RAM para eliminar la latencia de disco:

### Paso 1: Sincronizar hacia /dev/shm
```bash
python3 skills/token-optimizer/scripts/build_ramdisk_workspace.py .
```
La ruta activa de trabajo se ubica en `/dev/shm/agy-workspace/agy-token-optimizer`.

### Paso 2: Ejecutar tests y linters a 15 GB/s
```bash
pytest /dev/shm/agy-workspace/agy-token-optimizer/tests
```

---

## 4. Búsqueda Vectorial Acelerada con SIMD

Para consultas de similitud semántica sobre embeddings de 768 dimensiones sin sobrecargar la CPU:
* El script `simd_vector_accelerator.py` aprovecha las instrucciones AVX2 mediante `numpy` y la extensión C `sqlite_vec`.
* Ejecución:
  ```bash
  python3 skills/token-optimizer/scripts/simd_vector_accelerator.py "<consulta>"
  ```
