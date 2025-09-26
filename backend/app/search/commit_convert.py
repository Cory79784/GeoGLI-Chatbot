#!/usr/bin/env python3
"""
CSV to JSONL converter for commitment data
Converts region and country commitment CSVs to JSONL format for BM25 indexing
"""
import csv
import json
import os
from datetime import datetime
from typing import Dict, Any


def convert_csv_to_jsonl(csv_path: str, output_path: str, collection_name: str) -> bool:
    """
    Convert CSV file to JSONL format
    
    Args:
        csv_path: Input CSV file path
        output_path: Output JSONL file path  
        collection_name: Collection identifier (commit_region or commit_country)
        
    Returns:
        True if successful, False otherwise
    """
    if not os.path.exists(csv_path):
        print(f"❌ CSV file not found: {csv_path}")
        print(f"   Please ensure the file exists before running conversion.")
        return False
    
    try:
        records_converted = 0
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        with open(csv_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            
            with open(output_path, 'w', encoding='utf-8') as jsonl_file:
                for row_num, row in enumerate(reader, 1):
                    try:
                        # Determine primary key field
                        if collection_name == "commit_region":
                            primary_field = "Region"
                            id_value = row.get(primary_field, f"unknown_region_{row_num}")
                        else:  # commit_country
                            primary_field = "Country"
                            id_value = row.get(primary_field, f"unknown_country_{row_num}")
                        
                        # Build text description from commitment fields
                        text_parts = []
                        if primary_field in row and row[primary_field]:
                            text_parts.append(f"{row[primary_field]} —")
                        
                        # Add commitment data with labels
                        commitment_fields = ["LDN", "NBSAP", "NDC", "Bonn Challenge", "Single highest commitment"]
                        for field in commitment_fields:
                            if field in row and row[field]:
                                # Keep as string, don't parse units
                                value = str(row[field]).strip()
                                if value and value.lower() not in ['', 'n/a', 'na', 'null']:
                                    # Shorten field names for readability
                                    field_short = field.replace(" Challenge", "").replace(" commitment", "")
                                    text_parts.append(f"{field_short} {value}")
                        
                        # Join with semicolons
                        text = "; ".join(text_parts) + "." if len(text_parts) > 1 else text_parts[0] if text_parts else ""
                        
                        # Create JSONL record
                        record = {
                            "id": f"{collection_name}#{id_value}",
                            "collection": collection_name,
                            "text": text,
                            "source_csv": csv_path,
                            "updated_at": timestamp
                        }
                        
                        # Add primary field (region or country)
                        if collection_name == "commit_region":
                            record["region"] = row.get("Region", "")
                        else:
                            record["country"] = row.get("Country", "")
                        
                        # Add all original CSV fields as strings (preserve raw data)
                        for key, value in row.items():
                            if key not in record:  # Don't overwrite existing fields
                                record[key.lower().replace(" ", "_")] = str(value) if value else ""
                        
                        # Write JSONL line
                        jsonl_file.write(json.dumps(record, ensure_ascii=False) + '\n')
                        records_converted += 1
                        
                    except Exception as e:
                        print(f"⚠️  Error processing row {row_num} in {csv_path}: {e}")
                        continue
        
        print(f"✅ Converted {records_converted} records from {csv_path} to {output_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error converting {csv_path}: {e}")
        return False


def main():
    """Main conversion function"""
    print("🔄 Converting commitment CSV files to JSONL format...")
    
    # File paths
    conversions = [
        {
            "csv": "backend/corpus/commit_region.csv",
            "jsonl": "backend/corpus/commit_region.jsonl", 
            "collection": "commit_region"
        },
        {
            "csv": "backend/corpus/commit_country.csv",
            "jsonl": "backend/corpus/commit_country.jsonl",
            "collection": "commit_country"
        }
    ]
    
    success_count = 0
    for config in conversions:
        print(f"\n📁 Processing {config['collection']}...")
        if convert_csv_to_jsonl(config["csv"], config["jsonl"], config["collection"]):
            success_count += 1
    
    print(f"\n🎯 Conversion complete: {success_count}/{len(conversions)} files converted successfully")
    
    if success_count < len(conversions):
        print("\n💡 To create missing CSV files, you can:")
        print("   1. Add your commitment data CSV files to backend/corpus/")
        print("   2. Ensure they have columns like: Region/Country, LDN, NBSAP, NDC, 'Bonn Challenge', 'Single highest commitment'")
        print("   3. Re-run this script")


def _create_sample_csvs():
    """Create sample CSV files for testing (development only)"""
    # Sample region data
    region_data = [
        {
            "Region": "Middle East and North Africa",
            "LDN": "5.97 MHa",
            "NBSAP": "11.5 MHa", 
            "NDC": "6.9 MHa",
            "Bonn Challenge": "5 MHa",
            "Single highest commitment": "5 MHa"
        },
        {
            "Region": "Sub-Saharan Africa",
            "LDN": "45.2 MHa",
            "NBSAP": "78.3 MHa",
            "NDC": "23.1 MHa", 
            "Bonn Challenge": "15.7 MHa",
            "Single highest commitment": "15.7 MHa"
        }
    ]
    
    # Sample country data  
    country_data = [
        {
            "Country": "Saudi Arabia",
            "LDN": "2.1 MHa",
            "NBSAP": "3.5 MHa",
            "NDC": "1.8 MHa",
            "Bonn Challenge": "1.2 MHa", 
            "Single highest commitment": "1.2 MHa"
        },
        {
            "Country": "Nigeria",
            "LDN": "8.5 MHa",
            "NBSAP": "12.3 MHa",
            "NDC": "5.7 MHa",
            "Bonn Challenge": "4.0 MHa",
            "Single highest commitment": "4.0 MHa"
        }
    ]
    
    # Write sample files
    os.makedirs("backend/corpus", exist_ok=True)
    
    with open("backend/corpus/commit_region.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=region_data[0].keys())
        writer.writeheader()
        writer.writerows(region_data)
    
    with open("backend/corpus/commit_country.csv", 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=country_data[0].keys())
        writer.writeheader() 
        writer.writerows(country_data)
    
    print("📝 Created sample CSV files for testing")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--create-samples":
        _create_sample_csvs()
    else:
        main()


