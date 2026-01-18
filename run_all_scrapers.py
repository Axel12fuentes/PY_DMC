"""
Script maestro para scrapear TODAS las plataformas educativas (12 sitios).
Genera CSVs individuales + un CSV consolidado homologado.
"""
import sys
import os
import pandas as pd
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scrapers.enhanced_universal_scraper import EnhancedUniversalScraper

# ============= CONFIGURACIÓN DE TODOS LOS SITIOS =============
SCRAPERS_CONFIG = [
    # === Sitios ya implementados (ahora con enhanced scraper) ===
    {
        "name": "Datapath.ai",
        "catalog_url": "https://cursos.datapath.ai/",
        "dir_name": "datapath",
        "max_pages": 30  # Aumentado para máxima cobertura
    },
    {
        "name": "DataScience Peru",
        "catalog_url": "https://www.datascience.pe/lista-cursos",
        "dir_name": "datascience",
        "max_pages": 30
    },
    {
        "name": "DMC",
        "catalog_url": "https://dmc.pe/cursos/",
        "dir_name": "dmc",
        "max_pages": 30
    },
    {
        "name": "SmartData",
        "catalog_url": "https://smartdata.com.pe/cursos/",
        "dir_name": "smartdata",
        "max_pages": 30
    },
    {
        "name": "NewHorizons",
        "catalog_url": "https://www.newhorizons.edu.pe/",
        "dir_name": "newhorizons",
        "max_pages": 30
    },
    
    # === Nuevos sitios ===
    {
        "name": "BSG Institute",
        "catalog_url": "https://bsginstitute.com/",
        "dir_name": "bsg",
        "max_pages": 30
    },
    {
        "name": "WE Educación",
        "catalog_url": "https://we-educacion.com/",
        "dir_name": "we_educacion",
        "max_pages": 30
    },
    {
        "name": "PUCP InfoPUCP",
        "catalog_url": "https://infopucp.pucp.edu.pe/",
        "dir_name": "pucp_info",
        "max_pages": 30  # Aumentado de 8 a 30
    },
    {
        "name": "PUCP Educación Continua - Cursos",
        "catalog_url": "https://educacioncontinua.pucp.edu.pe/tipo-de-actividad/cursos/",
        "dir_name": "pucp_educon_cursos",
        "max_pages": 30
    },
    {
        "name": "PUCP Educación Continua - Programas",
        "catalog_url": "https://educacioncontinua.pucp.edu.pe/tipo-de-actividad/programas/",
        "dir_name": "pucp_educon_programas",
        "max_pages": 30
    },
    {
        "name": "UPC Postgrado",
        "catalog_url": "https://postgrado.upc.edu.pe/landings/programas-especializados/",
        "dir_name": "upc",
        "max_pages": 30
    },
    {
        "name": "ED Team",
        "catalog_url": "https://ed.team/cursos",
        "dir_name": "edteam",
        "max_pages": 30
    },
    {
        "name": "Platzi",
        "catalog_url": "https://platzi.com/cursos/",
        "dir_name": "platzi",
        "max_pages": 30
    }
]

def consolidate_csvs():
    """Consolida todos los CSVs individuales en uno solo homologado."""
    output_dir = "output"
    all_data = []
    
    print("\n" + "="*80)
    print("📊 CONSOLIDANDO CSVs...")
    print("="*80)
    
    for config in SCRAPERS_CONFIG:
        # Buscar el CSV usando el source_name (santizado)
        import re
        # Sanitizar nombre para match
        sanitized_name = re.sub(r'[^a-z0-9_]', '_', config['name'].lower().replace(' ', '_'))
        sanitized_name = re.sub(r'_+', '_', sanitized_name).strip('_')
        
        csv_file = f"{output_dir}/{sanitized_name}_database.csv"
        
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file)
                if len(df) == 0:
                    print(f"⚠️  Vacío: {config['name']}")
                    continue
                    
                # Asegurar que tenga la columna source_site
                if 'source_site' not in df.columns:
                    df['source_site'] = config['name']
                
                print(f"✓ {config['name']}: {len(df)} cursos")
                all_data.append(df)
            except Exception as e:
                print(f"⚠️  Error leyendo {csv_file}: {e}")
        else:
            print(f"⚠️  No encontrado: {csv_file}")
    
    if all_data:
        # Combinar todos
        consolidated_df = pd.concat(all_data, ignore_index=True)
        
        # Homologar columnas (asegurar orden consistente)
        standard_columns = [
            'source_site', 'course_name', 'course_type', 'price_raw', 
            'price_currency', 'price_original', 'duration', 'start_date',
            'instructor', 'modality', 'certification', 'methodology', 
            'content', 'url', 'brochure_url'
        ]
        
        # Agregar columnas faltantes con N/A
        for col in standard_columns:
            if col not in consolidated_df.columns:
                consolidated_df[col] = 'N/A'
        
        # Reordenar
        consolidated_df = consolidated_df[standard_columns]
        
        # Eliminar duplicados por URL
        consolidated_df = consolidated_df.drop_duplicates(subset=['url'], keep='first')
        
        # Guardar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        consolidated_file = f"{output_dir}/MASTER_courses_database_{timestamp}.csv"
        consolidated_df.to_csv(consolidated_file, index=False, encoding='utf-8-sig')
        
        print(f"\n✅ CSV CONSOLIDADO CREADO:")
        print(f"   📁 {consolidated_file}")
        print(f"   📊 Total de cursos únicos: {len(consolidated_df)}")
        print(f"   🏢 Plataformas: {consolidated_df['source_site'].nunique()}")
        
        # Resumen por plataforma
        print(f"\n📈 Distribución por plataforma:")
        summary = consolidated_df['source_site'].value_counts()
        for site, count in summary.items():
            print(f"   • {site}: {count} cursos")
        
        return consolidated_file
    else:
        print("\n❌ No se encontraron CSVs para consolidar")
        return None

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description='Scraper MAESTRO de todas las plataformas educativas')
    parser.add_argument('--site', type=int, help='Índice del sitio a scrapear (0-12)', default=None)
    parser.add_argument('--all', action='store_true', help='Scrapear TODOS los sitios (12 total)')
    parser.add_argument('--consolidate-only', action='store_true', help='Solo consolidar CSVs existentes')
    parser.add_argument('--resume', action='store_true', help='Reanudar desde el último checkpoint')
    parser.add_argument('--test', action='store_true', help='MODO PRUEBA: Solo 2 cursos por sitio')
    
    args = parser.parse_args()
    
    # Archivo de checkpoint para resiliencia
    checkpoint_file = "output/.scraping_checkpoint.json"
    
    if args.consolidate_only:
        consolidate_csvs()
        sys.exit(0)
    
    sites_to_scrape = []
    completed_sites = []
    
    # Cargar checkpoint si existe y se solicita resume
    if args.resume and os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)
                completed_sites = checkpoint.get('completed', [])
                print(f"\n♻️  MODO RESUME: {len(completed_sites)} sitios ya completados")
                for site in completed_sites:
                    print(f"   ✓ {site}")
        except:
            pass
    
    if args.all:
        sites_to_scrape = SCRAPERS_CONFIG
        
        if args.test:
            print(f"\n🧪 MODO PRUEBA: Scrapeando {len(SCRAPERS_CONFIG)} plataformas (2 cursos c/u)")
            print("⏱️  Tiempo estimado: 30-60 minutos")
            print("💰 Llamadas LLM estimadas: ~50-100 (GPT-4o)")
            print("🎯 Objetivo: Verificar funcionamiento del sistema")
        else:
            print(f"\n🚀 MODO COMPLETO: Scrapeando {len(SCRAPERS_CONFIG)} plataformas")
            print("⏱️  Tiempo estimado: 6-12 horas (max_pages=30)")
            print("💰 Llamadas LLM estimadas: ~3000-8000 (GPT-4o)")
            print("🎯 Objetivo: Benchmarking para DMC - Máxima cobertura")
        
        if completed_sites:
            remaining = len(sites_to_scrape) - len(completed_sites)
            print(f"♻️  Sitios restantes: {remaining}")
        
        input("\n⚡ Presiona ENTER para continuar o CTRL+C para cancelar...")
    elif args.site is not None:
        if 0 <= args.site < len(SCRAPERS_CONFIG):
            sites_to_scrape = [SCRAPERS_CONFIG[args.site]]
        else:
            print(f"❌ Índice {args.site} fuera de rango (0-{len(SCRAPERS_CONFIG)-1})")
            sys.exit(1)
    else:
        print("📋 PLATAFORMAS DISPONIBLES:")
        print("="*80)
        for i, config in enumerate(SCRAPERS_CONFIG):
            status = "✓ Ya implementado" if i < 5 else "⭐ Nuevo"
            print(f"  [{i:2d}] {config['name']:40s} {status}")
        print("="*80)
        print("\n💡 USO:")
        print("  python3 run_all_scrapers.py --site 0     # Scrapear Datapath")
        print("  python3 run_all_scrapers.py --all        # Scrapear TODOS (recomendado)")
        print("  python3 run_all_scrapers.py --resume     # Reanudar scraping interrumpido")
        print("  python3 run_all_scrapers.py --consolidate-only  # Solo unificar CSVs")
        print("\n💾 Los brochures se guardan en: scrapers/downloads/[sitio]/")
        sys.exit(0)
    
    # ========== EJECUCIÓN DE SCRAPERS ==========
    total_courses = 0
    
    for idx, config in enumerate(sites_to_scrape, 1):
        # Skip si ya está completado (resume mode)
        if config['name'] in completed_sites:
            print(f"\n⏭️  Saltando {config['name']} (ya completado)")
            continue
            
        print(f"\n{'='*80}")
        print(f"🎯 [{idx}/{len(sites_to_scrape)}] {config['name']}")
        print(f"{'='*80}\n")
        
        try:
            scraper = EnhancedUniversalScraper(
                site_name=config['name'],
                catalog_url=config['catalog_url'],
                download_dir_name=config['dir_name'],
                max_pagination=config['max_pages'],
                max_courses=2 if args.test else None  # Limitar a 2 en modo prueba
            )
            
            scraper.parse_catalog()
            scraper.save_data()
            
            courses_count = len(scraper.data)
            total_courses += courses_count
            print(f"\n✅ {config['name']}: {courses_count} cursos extraídos")
            
            # Guardar checkpoint
            completed_sites.append(config['name'])
            with open(checkpoint_file, 'w') as f:
                json.dump({'completed': completed_sites}, f)
            print(f"💾 Checkpoint guardado")
            
        except KeyboardInterrupt:
            print(f"\n⚠️  Cancelado por usuario")
            print(f"💡 Puedes reanudar con: python3 run_all_scrapers.py --resume --all")
            break
        except Exception as e:
            print(f"\n❌ Error en {config['name']}: {e}")
            import traceback
            traceback.print_exc()
            print(f"\n💡 Continuando con siguiente plataforma...")
    
    # ========== CONSOLIDACIÓN FINAL ==========
    print(f"\n{'='*80}")
    print(f"✅ SCRAPING COMPLETADO")
    print(f"   Total de cursos extraídos en esta ejecución: {total_courses}")
    print(f"{'='*80}")
    
    consolidate_csvs()
    
    # Limpiar checkpoint si completó todo
    if len(completed_sites) == len(SCRAPERS_CONFIG) and os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)
        print("\n🧹 Checkpoint limpiado (scraping 100% completo)")
    
    print(f"\n{'='*80}")
    print("🎉 PROCESO COMPLETO")
    print("📁 Brochures descargados en: scrapers/downloads/")
    print(f"{'='*80}")


