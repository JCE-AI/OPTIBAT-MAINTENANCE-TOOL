import pandas as pd
from collections import defaultdict

# Datos de los clientes y sus flags
clientes_flags = {
    'ABG DALLA': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE', 'OPTIBAT_WATCHDOG'],
    'ABG DHAR': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'ABG PALI': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'ANGUS': [],
    'CEMEX FM1 BALCONES': ['OPTIBAT_ON', 'Flag_Ready', 'Communication_ECS', 'Support_Flag_Copy', 'Macrostates_Flag_Copy', 'Resultexistance_Flag_Copy', 'OPTIBAT_WATCHDOG'],
    'CRH LEMONA': ['OPTIBAT_ON', 'OPTIBAT_Ready_fromPLANT', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'MOLINS ALION COLOMBIA': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'MOLINS-BCN-BARACELONA': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'TITAN ALEXANDRIA CM7': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES'],
    'TITAN ALEXANDRIA CM8': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES'],
    'TITAN ALEXANDRIA CM9': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES'],
    'TITAN-KOSJERIC-CM1': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'TITAN-KOSJERIC-KILN': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'TITAN-KOSJERIC-RM1': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'TITAN-PENNSUCO-FM3': ['OPTIBAT_ON', 'OPTIBAT_READY', 'KILN_OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'TITAN-PENNSUCO-KILN': ['OPTIBAT_ON', 'OPTIBAT_READY', 'KILN_OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'TITAN-PENNSUCO-VRM': ['OPTIBAT_ON', 'OPTIBAT_READY', 'OPTIBAT_COMMUNICATION', 'OPTIBAT_SUPPORT', 'OPTIBAT_MACROSTATES', 'OPTIBAT_RESULTEXISTANCE'],
    'TITAN-ROANOKE-FM10': ['OPTIBAT_READY', 'Communication_Flag'],
    'TITAN-ROANOKE-KILN': ['OPTIBAT_READY', 'Communication_Flag'],
    'TITAN-ROANOKE-RM1': ['OPTIBAT_READY', 'Communication_Flag'],
    'TITAN-SHARR-CM2': ['OPTIBAT_READY'],
    'TITAN-SHARR-KILN': ['OPTIBAT_READY'],
    'TITAN-SHARR-RM2': ['OPTIBAT_READY']
}

# Agrupar clientes por configuración de flags idéntica
grupos = defaultdict(list)
for cliente, flags in clientes_flags.items():
    # Crear una clave única para cada combinación de flags
    flags_key = '|'.join(sorted(flags)) if flags else 'SIN_FLAGS'
    grupos[flags_key].append(cliente)

# Crear informe de grupos
print("RESUMEN DE ACTIVOS CON CONFIGURACIONES IDÉNTICAS DE FLAGS")
print("=" * 60)
print()

grupo_num = 1
for flags_config, clientes in grupos.items():
    if len(clientes) > 1:  # Solo mostrar grupos con más de un cliente
        print(f"GRUPO {grupo_num}: {len(clientes)} activos con configuración idéntica")
        print("-" * 60)
        print(f"Activos: {', '.join(clientes)}")
        if flags_config != 'SIN_FLAGS':
            flags_list = flags_config.split('|')
            print(f"Flags comunes ({len(flags_list)}):")
            for flag in flags_list:
                print(f"  - {flag}")
        else:
            print("Flags comunes: NINGUNA")
        print()
        grupo_num += 1

# Guardar resumen en archivo
output_path = r'C:\Users\JuanCruz\Desktop_Local\mtto streamlit\STATISTICS FLAGS\RESUMEN_GRUPOS_FLAGS.txt'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("RESUMEN DE ACTIVOS CON CONFIGURACIONES IDÉNTICAS DE FLAGS\n")
    f.write("=" * 60 + "\n")
    f.write(f"Fecha de análisis: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}\n")
    f.write("=" * 60 + "\n\n")
    
    grupo_num = 1
    for flags_config, clientes in sorted(grupos.items(), key=lambda x: len(x[1]), reverse=True):
        if len(clientes) > 1:
            f.write(f"GRUPO {grupo_num}: {len(clientes)} activos con configuración idéntica\n")
            f.write("-" * 60 + "\n")
            f.write(f"Activos: {', '.join(sorted(clientes))}\n")
            
            if flags_config != 'SIN_FLAGS':
                flags_list = flags_config.split('|')
                f.write(f"\nFlags comunes ({len(flags_list)}):\n")
                for flag in flags_list:
                    f.write(f"  - {flag}\n")
            else:
                f.write("\nFlags comunes: NINGUNA\n")
            
            f.write("\n" + "=" * 60 + "\n\n")
            grupo_num += 1
    
    # Agregar sección de activos únicos
    f.write("ACTIVOS CON CONFIGURACIÓN ÚNICA\n")
    f.write("-" * 60 + "\n")
    for flags_config, clientes in sorted(grupos.items(), key=lambda x: x[0]):
        if len(clientes) == 1:
            cliente = clientes[0]
            if flags_config != 'SIN_FLAGS':
                flags_list = flags_config.split('|')
                f.write(f"\n{cliente}: {len(flags_list)} flags\n")
                for flag in flags_list:
                    f.write(f"  - {flag}\n")
            else:
                f.write(f"\n{cliente}: SIN FLAGS\n")
    
    # Estadísticas finales
    f.write("\n" + "=" * 60 + "\n")
    f.write("ESTADÍSTICAS FINALES\n")
    f.write("-" * 60 + "\n")
    f.write(f"Total de activos analizados: 23\n")
    f.write(f"Grupos con configuración idéntica: {sum(1 for g in grupos.values() if len(g) > 1)}\n")
    f.write(f"Activos con configuración única: {sum(1 for g in grupos.values() if len(g) == 1)}\n")
    f.write(f"Activos agrupados: {sum(len(g) for g in grupos.values() if len(g) > 1)}\n")

print(f"\nResumen guardado en: {output_path}")