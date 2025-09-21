import pandas as pd
import os

# Read the original Excel file
original_file = 'INFORME_FLAGS_CLIENTES-tomardeaqui.xlsx'
df = pd.read_excel(original_file, sheet_name='Flags por Cliente')

print("Original Excel file loaded successfully!")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print("\nCurrent status:")
print(df)

# Dictionary with the missing flags based on our analysis of the .txt files
missing_flags_update = {
    'ABG DHAR': {
        'Communication_ECS': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'ABG PALI': {
        'Communication_ECS': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'ANGUS': {  # CRITICAL - All flags missing
        'OPTIBAT_ON': 'NO',         # Not found in txt file
        'Flag_Ready': 'NO',         # Not found in txt file
        'Communication_ECS': 'NO',  # Not found in txt file
        'Support_Flag_Copy': 'NO',  # Not found in txt file
        'Macrostates_Flag_Copy': 'NO',  # Not found in txt file
        'Resultexistance_Flag_Copy': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'CRH LEMONA': {
        'Communication_ECS': 'KILN_OPTIBAT_COMMUNICATION',  # Found variant
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'MOLINS ALION COLOMBIA': {
        'Communication_ECS': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'YES'   # Found as OPTIBAT_WATCHDOG
    },
    'MOLINS-BCN-BARACELONA': {
        'Communication_ECS': 'KILN_OPTIBAT_COMMUNICATION',  # Found variant
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'TITAN ALEXANDRIA CM7': {
        'Resultexistance_Flag_Copy': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'NO'            # Not found in txt file
    },
    'TITAN ALEXANDRIA CM8': {
        'Resultexistance_Flag_Copy': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'NO'            # Not found in txt file
    },
    'TITAN ALEXANDRIA CM9': {
        'Resultexistance_Flag_Copy': 'YES',  # Found as Resultexistance_Flag_Copy
        'OPTIBAT_WATCHDOG': 'YES'            # Found as OPTIBAT_WATCHDOG
    },
    'TITAN-KOSJERIC-CM1': {
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'TITAN-KOSJERIC-KILN': {
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'TITAN-KOSJERIC-RM1': {
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'TITAN-PENNSUCO-FM3': {
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'TITAN-PENNSUCO-KILN': {
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'TITAN-PENNSUCO-VRM': {
        'OPTIBAT_WATCHDOG': 'NO'    # Not found in txt file
    },
    'TITAN-ROANOKE-KILN': {
        'Flag_Ready': 'NO',                 # Not found in txt file
        'Support_Flag_Copy': 'NO',          # Not found in txt file
        'Macrostates_Flag_Copy': 'NO',      # Not found in txt file
        'Resultexistance_Flag_Copy': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'NO'            # Not found in txt file
    },
    'TITAN-SHARR-CM2': {  # This was the incomplete one mentioned
        'Flag_Ready': 'OPTIBAT_READY',          # Found as OPTIBAT_READY
        'Communication_ECS': 'OPTIBAT_COMMUNICATION',  # Found as OPTIBAT_COMMUNICATION
        'Support_Flag_Copy': 'YES',             # Found as Support_Flag_Copy
        'Macrostates_Flag_Copy': 'YES',         # Found as Macrostates_Flag_Copy
        'Resultexistance_Flag_Copy': 'YES',     # Found as Resultexistance_Flag_Copy
        'OPTIBAT_WATCHDOG': 'YES'               # Found as OPTIBAT_WATCHDOG
    },
    'TITAN-SHARR-KILN': {
        'Flag_Ready': 'OPTIBAT_READY',          # Found as OPTIBAT_READY
        'Communication_ECS': 'OPTIBAT_COMMUNICATION',  # Found as OPTIBAT_COMMUNICATION
        'Support_Flag_Copy': 'YES',             # Found as Support_Flag_Copy
        'Macrostates_Flag_Copy': 'YES',         # Found as Macrostates_Flag_Copy
        'Resultexistance_Flag_Copy': 'YES',     # Found as Resultexistance_Flag_Copy
        'OPTIBAT_WATCHDOG': 'YES'               # Found as OPTIBAT_WATCHDOG
    },
    'TITAN-SHARR-RM2': {
        'Flag_Ready': 'OPTIBAT_READY',          # Found as OPTIBAT_READY
        'Communication_ECS': 'OPTIBAT_COMMUNICATION',  # Found as OPTIBAT_COMMUNICATION
        'Support_Flag_Copy': 'YES',             # Found as Support_Flag_Copy
        'Macrostates_Flag_Copy': 'YES',         # Found as Macrostates_Flag_Copy
        'Resultexistance_Flag_Copy': 'YES',     # Found as Resultexistance_Flag_Copy
        'OPTIBAT_WATCHDOG': 'YES'               # Found as OPTIBAT_WATCHDOG
    },
    'TITAN-ROANOKE-FM10': {
        'Flag_Ready': 'NO',                 # Not found in txt file
        'Support_Flag_Copy': 'NO',          # Not found in txt file
        'Macrostates_Flag_Copy': 'NO',      # Not found in txt file
        'Resultexistance_Flag_Copy': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'NO'            # Not found in txt file
    },
    'TITAN-ROANOKE-RM1': {
        'Flag_Ready': 'NO',                 # Not found in txt file
        'Support_Flag_Copy': 'NO',          # Not found in txt file
        'Macrostates_Flag_Copy': 'NO',      # Not found in txt file
        'Resultexistance_Flag_Copy': 'NO',  # Not found in txt file
        'OPTIBAT_WATCHDOG': 'NO'            # Not found in txt file
    }
}

# Update the DataFrame with missing information
for client, flags in missing_flags_update.items():
    # Find the client row
    client_row = df[df['Cliente'] == client]
    if not client_row.empty:
        client_idx = client_row.index[0]
        
        print(f"\nUpdating {client}:")
        for flag, value in flags.items():
            current_value = df.loc[client_idx, flag]
            if pd.isna(current_value) or current_value == '':
                df.loc[client_idx, flag] = value
                print(f"  - {flag}: {current_value} → {value}")
            else:
                print(f"  - {flag}: Already set to '{current_value}' (keeping existing)")

# Recalculate Total_Flags column
if 'Total_Flags' in df.columns:
    flag_columns = ['OPTIBAT_ON', 'Flag_Ready', 'Communication_ECS', 
                   'Support_Flag_Copy', 'Macrostates_Flag_Copy', 
                   'Resultexistance_Flag_Copy', 'OPTIBAT_WATCHDOG']
    
    for idx, row in df.iterrows():
        total_flags = 0
        for flag_col in flag_columns:
            if not pd.isna(row[flag_col]) and row[flag_col] not in ['', 'NO']:
                total_flags += 1
        df.loc[idx, 'Total_Flags'] = total_flags

# Save the updated file
output_file = 'INFORME_FLAGS_CLIENTES_ACTUALIZADO.xlsx'
df.to_excel(output_file, sheet_name='Flags por Cliente', index=False, engine='openpyxl')

print(f"\n✅ Updated Excel file saved as: {output_file}")
print(f"\nFinal completion status:")
print(df[['Cliente', 'Total_Flags']].to_string(index=False))

# Show which clients were updated
updated_clients = list(missing_flags_update.keys())
print(f"\n📝 Clients updated in this session:")
for client in updated_clients:
    print(f"  - {client}")