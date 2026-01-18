# 🚀 Sistema de Scraping Masivo - Proyecto DMC Benchmarking

Sistema de extracción automática de datos de 12 plataformas educativas usando LLM (GPT-4o) para análisis competitivo.

## 📊 Cliente: DMC
**Objetivo:** Benchmarking de cursos, especializaciones y diplomados contra la competencia.

## 🎯 Plataformas Scrapeadas (12 total)

### Existentes (Migradas a Enhanced)
1. **Datapath.ai** - Bootcamps y talleres IA
2. **DataScience Peru** - Cursos de ciencia de datos
3. **DMC** - Cliente base (para comparación)
4. **SmartData** - Especializaciones en data
5. **NewHorizons** - Certificaciones internacionales

### Nuevas
6. **BSG Institute** - Programas especializados
7. **WE Educación** - Cursos corporativos
8. **PUCP InfoPUCP** - Cursos TIC
9. **PUCP Educación Continua - Cursos**
10. **PUCP Educación Continua - Programas**
11. **UPC Postgrado** - Programas especializados
12. **ED Team** - Cursos online tech
13. **Platzi** - Escuelas y rutas de aprendizaje

## 🧠 Tecnología

### LLM-Enhanced Architecture
- **GPT-4o** para descubrimiento de catálogos (robusto a cambios de diseño)
- **GPT-4o-mini** para extracción de HTML y PDFs
- **Zero selectores CSS** - Inmune a rediseños web

### Características
- ✅ **Paginación automática** (hasta 30 páginas por sitio)
- ✅ **Descarga de brochures** (local en `scrapers/downloads/`)
- ✅ **Extracción de PDFs** con LLM
- ✅ **Sistema de checkpoints** - Reanudable tras cortes
- ✅ **CSV consolidado** - Todos los sitios en un archivo

## 📁 Estructura de Archivos

```
dmc_project/
├── scrapers/
│   ├── downloads/          # PDFs descargados (LOCAL, no Drive)
│   │   ├── datapath/
│   │   ├── dmc/
│   │   ├── platzi/
│   │   └── ...
│   ├── enhanced_universal_scraper.py
│   └── ...
├── utils/
│   └── llm_helper.py       # LLM centralizado (3 métodos)
├── output/
│   ├── datapath_database.csv
│   ├── dmc_database.csv
│   ├── platzi_database.csv
│   ├── ...
│   ├── MASTER_courses_database_[timestamp].csv  # ← CSV FINAL
│   └── .scraping_checkpoint.json  # Checkpoint para resume
├── run_all_scrapers.py     # Orquestador principal
└── ejecutar_scraping_completo.sh  # Script bash
```

## 🚀 Ejecución

### Método Recomendado (Script Interactivo)
```bash
cd /home/johnny/Documentos/moodle-sync/dmc_project
./ejecutar_scraping_completo.sh
```

### Método Directo (Python)
```bash
# Ver opciones
PYTHONPATH=. ./dmc_env/bin/python3 run_all_scrapers.py

# Scrapear TODOS los sitios
PYTHONPATH=. ./dmc_env/bin/python3 run_all_scrapers.py --all

# Scrapear uno específico (ej: Platzi = índice 12)
PYTHONPATH=. ./dmc_env/bin/python3 run_all_scrapers.py --site 12

# ⚡ REANUDAR tras corte de internet/error
PYTHONPATH=. ./dmc_env/bin/python3 run_all_scrapers.py --resume --all

# Solo consolidar CSVs existentes
PYTHONPATH=. ./dmc_env/bin/python3 run_all_scrapers.py --consolidate-only
```

## ♻️ Sistema de Resiliencia

### Checkpoints Automáticos
El sistema guarda un checkpoint después de completar cada plataforma en:
```
output/.scraping_checkpoint.json
```

### ¿Cómo funciona el Resume?
1. **Corte de internet** → El script se detiene
2. **Reconectas** → Ejecutas con `--resume --all`
3. **Sistema lee checkpoint** → Salta plataformas ya completadas
4. **Continúa desde donde quedó**

### Ejemplo
```bash
# Ejecutas primera vez
PYTHONPATH=. ./dmc_env/bin/python3 run_all_scrapers.py --all
# ✓ Datapath (OK - checkpoint guardado)
# ✓ DataScience (OK - checkpoint guardado)
# ✓ DMC (OK - checkpoint guardado)
# ❌ SmartData (corte de internet)

# Reanudar
PYTHONPATH=. ./dmc_env/bin/python3 run_all_scrapers.py --resume --all
# ⏭️ Saltando Datapath (ya completado)
# ⏭️ Saltando DataScience (ya completado)
# ⏭️ Saltando DMC (ya completado)
# 🎯 Continuando con SmartData...
```

## ⏱️ Estimaciones

| Métrica | Valor |
|---------|-------|
| **Tiempo total** | 6-12 horas |
| **Cursos esperados** | 500-1500+ |
| **Llamadas LLM** | 3000-8000 |
| **Costo OpenAI** | $15-40 USD |
| **Max páginas por sitio** | 30 (configurable) |

## 📊 CSV Consolidado Final

### Archivo
```
output/MASTER_courses_database_YYYYMMDD_HHMMSS.csv
```

### Columnas Homologadas
- `source_site` - Plataforma origen
- `course_name` - Nombre del curso/programa
- `course_type` - Bootcamp | Especialización | Curso | Diplomado
- `price_raw` - Precio actual (con símbolo)
- `price_currency` - PEN | USD | EUR
- `price_original` - Precio antes de descuento
- `duration` - Duración (horas, semanas, meses)
- `start_date` - Fecha de inicio
- `instructor` - Instructor/profesor
- `modality` - Online | En vivo | Híbrido | Presencial
- `certification` - Certificación otorgada
- `methodology` - Metodología del curso
- `content` - Módulos/contenido extraído
- `url` - URL del curso
- `brochure_url` - Estado del brochure

## 💾 Brochures

**Ubicación:** Todos los PDFs se guardan LOCALMENTE:
```
scrapers/downloads/
├── datapath/
│   └── Bootcamp_Data_Engineer.pdf
├── dmc/
│   └── Excel_Avanzado.pdf
├── platzi/
│   └── Escuela_Data_Science.pdf
└── ...
```

**NO se suben a Google Drive** - Todo queda en la carpeta del proyecto.

## 🛡️ Manejo de Errores

### Si un sitio falla
- ✅ El sistema **continúa** con el siguiente
- ✅ Logs detallados del error
- ✅ Checkpoint guardado hasta el último exitoso
- ✅ Puedes reanudar después

### Si cancelas (CTRL+C)
- ✅ El sistema **guarda checkpoint**
- ✅ Mensaje con instrucciones de resume
- ✅ No pierdes el progreso

## 🎓 Próximos Pasos (Post-Scraping)

1. **Análisis de datos** - Cargar CSV consolidado
2. **Benchmarking** - Comparar DMC vs competencia
3. **Visualización** - Dashboards de precios/duración/certificaciones
4. **Insights** - Brechas de mercado, oportunidades

---

## 🔧 Configuración

### Variables de Entorno
```bash
# .env
OPENAI_API_KEY=sk-...
```

### Dependencias
```bash
pip install playwright openai pdfplumber python-dotenv pandas
playwright install chromium
```

---

**📅 Última actualización:** 2026-01-18  
**👨‍💻 Desarrollado para:** DMC - Benchmarking de mercado educativo tech
