#!/usr/bin/env python3
"""
OPTIBAT Flags Analysis Script
Analyzes all .txt files in the statistics directory to identify OPTIBAT flags present in each client file.
"""

import os
import re
from collections import defaultdict
from typing import Dict, List, Set


def extract_client_name(filename: str) -> str:
    """Extract client name from filename, removing date and extension."""
    # Remove the file extension and timestamp
    name = filename.replace('-STATISTICS_VIEW_SUMMARY.txt', '')
    # Remove date pattern (YYYY-MM-DD HH MM SS)
    name = re.sub(r'-\d{4}-\d{2}-\d{2} \d{2} \d{2} \d{2}', '', name)
    return name.strip()


def find_optibat_flags(variable_names: List[str]) -> Set[str]:
    """Find all OPTIBAT-related flags in the list of variable names."""
    flags_found = set()
    
    # Define the flags to look for (with variations)
    flag_patterns = {
        'OPTIBAT_ON': ['OPTIBAT_ON'],
        'OPTIBAT_READY': ['OPTIBAT_READY', 'Flag_Ready', 'Ready'],
        'OPTIBAT_COMMUNICATION': ['OPTIBAT_COMMUNICATION', 'Communication_ECS'],
        'OPTIBAT_SUPPORT': ['OPTIBAT_SUPPORT', 'Support_Flag_Copy'],
        'OPTIBAT_MACROSTATES': ['OPTIBAT_MACROSTATES', 'Macrostates_Flag_Copy'],
        'OPTIBAT_RESULTS': ['OPTIBAT_RESULTS', 'Resultexistance_Flag_Copy'],
        'OPTIBAT_WATCHDOG': ['OPTIBAT_WATCHDOG'],
    }
    
    # Convert variable names to lowercase for case-insensitive comparison
    var_names_lower = [var.lower() for var in variable_names]
    
    # Check for each flag pattern
    for flag_category, patterns in flag_patterns.items():
        for pattern in patterns:
            if pattern.lower() in var_names_lower:
                # Find the exact match to preserve original case
                for var in variable_names:
                    if var.lower() == pattern.lower():
                        flags_found.add(var)
                        break
    
    # Look for any other OPTIBAT-related flags that might not be in our predefined list
    for var in variable_names:
        if 'OPTIBAT' in var.upper() and var not in flags_found:
            flags_found.add(var)
    
    return flags_found


def analyze_file(filepath: str) -> tuple:
    """Analyze a single file and return client name and found flags."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()
            
        if len(lines) < 2:
            return None, None
            
        # Get the second line (VarName line) and split by tabs
        varname_line = lines[1].strip()
        if not varname_line.startswith('VarName'):
            return None, None
            
        # Split by tab and remove the 'VarName' prefix
        parts = varname_line.split('\t')
        if len(parts) < 2:
            return None, None
            
        variable_names = parts[1:]  # Skip the 'VarName' label
        
        # Extract client name from filename
        filename = os.path.basename(filepath)
        client_name = extract_client_name(filename)
        
        # Find OPTIBAT flags
        flags = find_optibat_flags(variable_names)
        
        return client_name, flags
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None, None


def main():
    """Main function to analyze all files and generate summary."""
    
    # Directory containing the files
    directory = r"C:\Users\JuanCruz\Desktop_Local\mtto streamlit\STATISTICS FLAGS\statistics"
    
    # Dictionary to store results
    client_flags = {}
    all_flags_found = set()
    
    # Process all .txt files
    print("OPTIBAT FLAGS ANALYSIS")
    print("=" * 60)
    print("Analyzing files...")
    
    txt_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    
    if not txt_files:
        print("No .txt files found in directory!")
        return
    
    processed_count = 0
    for filename in sorted(txt_files):
        filepath = os.path.join(directory, filename)
        client_name, flags = analyze_file(filepath)
        
        if client_name and flags is not None:
            client_flags[client_name] = flags
            all_flags_found.update(flags)
            processed_count += 1
            print(f"  ✓ Processed: {client_name}")
    
    print(f"\nProcessed {processed_count} files successfully.")
    print(f"Found {len(all_flags_found)} unique OPTIBAT flags across all clients.")
    
    # Generate summary report
    print("\n" + "=" * 80)
    print("OPTIBAT FLAGS SUMMARY REPORT")
    print("=" * 80)
    
    # Sort flags for consistent output
    sorted_flags = sorted(all_flags_found)
    
    print(f"\nALL OPTIBAT FLAGS FOUND ({len(sorted_flags)} total):")
    print("-" * 50)
    for i, flag in enumerate(sorted_flags, 1):
        print(f"{i:2d}. {flag}")
    
    print(f"\nCLIENT-BY-CLIENT ANALYSIS ({len(client_flags)} clients):")
    print("=" * 80)
    
    for client_name in sorted(client_flags.keys()):
        flags = client_flags[client_name]
        print(f"\n🏭 {client_name}")
        print("-" * len(client_name))
        
        if flags:
            print(f"   Flags found: {len(flags)}")
            for flag in sorted(flags):
                print(f"   ✓ {flag}")
        else:
            print("   ❌ No OPTIBAT flags found")
    
    # Generate flags presence matrix
    print(f"\nFLAGS PRESENCE MATRIX")
    print("=" * 80)
    
    # Create a matrix showing which clients have which flags
    print("CLIENT NAME".ljust(35), end="")
    for flag in sorted_flags[:8]:  # Show first 8 flags to fit in terminal
        print(flag[:12].center(13), end="")
    print()
    
    print("-" * 35, end="")
    for _ in range(min(8, len(sorted_flags))):
        print("-" * 13, end="")
    print()
    
    for client_name in sorted(client_flags.keys()):
        flags = client_flags[client_name]
        print(client_name[:34].ljust(35), end="")
        
        for flag in sorted_flags[:8]:
            if flag in flags:
                print("     ✓".center(13), end="")
            else:
                print("     -".center(13), end="")
        print()
    
    # Statistics summary
    print(f"\nSTATISTICS SUMMARY")
    print("=" * 50)
    
    flag_counts = defaultdict(int)
    for flags in client_flags.values():
        for flag in flags:
            flag_counts[flag] += 1
    
    print(f"Total clients analyzed: {len(client_flags)}")
    print(f"Total unique flags found: {len(all_flags_found)}")
    print(f"Average flags per client: {sum(len(flags) for flags in client_flags.values()) / len(client_flags):.1f}")
    
    print(f"\nMOST COMMON FLAGS:")
    for flag, count in sorted(flag_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(client_flags)) * 100
        print(f"  {flag}: {count}/{len(client_flags)} clients ({percentage:.1f}%)")
    
    print(f"\nCLIENTS WITHOUT OPTIBAT FLAGS:")
    clients_without_flags = [name for name, flags in client_flags.items() if not flags]
    if clients_without_flags:
        for client in clients_without_flags:
            print(f"  ❌ {client}")
    else:
        print("  ✓ All clients have at least one OPTIBAT flag")
    
    # Save results to file
    output_file = os.path.join(directory, "OPTIBAT_FLAGS_ANALYSIS_SUMMARY.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("OPTIBAT FLAGS ANALYSIS SUMMARY\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"SUMMARY STATISTICS:\n")
        f.write(f"- Total clients analyzed: {len(client_flags)}\n")
        f.write(f"- Total unique flags found: {len(all_flags_found)}\n")
        f.write(f"- Average flags per client: {sum(len(flags) for flags in client_flags.values()) / len(client_flags):.1f}\n\n")
        
        f.write("CLIENT FLAGS MAPPING:\n")
        f.write("-" * 50 + "\n")
        for client_name in sorted(client_flags.keys()):
            flags = client_flags[client_name]
            f.write(f"\n{client_name}:\n")
            if flags:
                for flag in sorted(flags):
                    f.write(f"  - {flag}\n")
            else:
                f.write("  - No OPTIBAT flags found\n")
        
        f.write(f"\nFLAG USAGE STATISTICS:\n")
        f.write("-" * 30 + "\n")
        for flag, count in sorted(flag_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(client_flags)) * 100
            f.write(f"{flag}: {count}/{len(client_flags)} ({percentage:.1f}%)\n")
    
    print(f"\n💾 Summary saved to: {output_file}")


if __name__ == "__main__":
    from datetime import datetime
    main()