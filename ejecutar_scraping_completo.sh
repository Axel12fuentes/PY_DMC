#!/bin/bash

# Script de ejecución para el scraping masivo de 12 plataformas educativas
# Autor: Sistema de Scraping LLM-Enhanced
# Fecha: 2026-01-18

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   🚀 SCRAPER MASIVO DE PLATAFORMAS EDUCATIVAS               ║"
echo "║   12 Sitios | LLM-Powered (GPT-4o) | CSV Consolidado       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Verificar entorno virtual
if [ ! -d "dmc_env" ]; then
    echo "❌ Error: Entorno virtual no encontrado"
    echo "   Ejecuta primero: python3 -m venv dmc_env"
    exit 1
fi

# Activar entorno
source dmc_env/bin/activate

# Verificar dependencias
echo "📦 Verificando dependencias..."
pip install -q pandas playwright openai pdfplumber python-dotenv

# Verificar API Key
if [ -z "$OPENAI_API_KEY" ] && [ ! -f ".env" ]; then
    echo "⚠️  ADVERTENCIA: OPENAI_API_KEY no encontrada"
    echo "   Asegúrate de tener un archivo .env con tu API key"
    read -p "   ¿Continuar de todas formas? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  INICIANDO SCRAPING DE 12 PLATAFORMAS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📋 Plataformas a scrapear:"
echo "   [0-4]  Ya implementadas (5): Datapath, DataScience, DMC, SmartData, NewHorizons"
echo "   [5-12] Nuevas (7): BSG, WE, PUCP x3, UPC, ED Team, Platzi"
echo ""
echo "⏱️  Tiempo estimado: 4-8 horas"
echo "💰 Costo estimado: ~$10-30 USD (GPT-4o)"
echo "📊 Cursos esperados: 500-1500+ cursos"
echo ""

# Preguntar confirmación
read -p "🚦 ¿Deseas continuar con el scraping COMPLETO? (y/n): " -n 1 -r
echo
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🎯 Ejecutando scraping completo..."
    echo ""
    
    # Ejecutar con PYTHONPATH
    PYTHONPATH=. python3 run_all_scrapers.py --all
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  ✅ PROCESO COMPLETADO                                        ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "📁 Archivos generados:"
    echo "   • output/*_database.csv (CSVs individuales por plataforma)"
    echo "   • output/MASTER_courses_database_*.csv (CSV consolidado)"
    echo ""
    echo "👀 Revisa la carpeta 'output/' para ver los resultados"
    
else
    echo ""
    echo "❌ Scraping cancelado por usuario"
    echo ""
    echo "💡 Puedes ejecutar sitios individuales con:"
    echo "   PYTHONPATH=. python3 run_all_scrapers.py --site 0"
    echo ""
    echo "📋 O ver la lista completa:"
    echo "   PYTHONPATH=. python3 run_all_scrapers.py"
fi

deactivate
