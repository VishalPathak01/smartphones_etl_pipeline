import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import re
import numpy as np
import pandas as pd
from config import DATA_DIR

# mappings for consistency
BRAND_MAPPING = {
    "Moto": "Motorola",
    "Samaung": "Samsung",   # typo in source data
}
PROCESSORS_CORES_MAP = {
    "Octa Core Processor": "Octa Core",
    "Hexa Core Processor": "Hexa Core",
    "Dual Core Processor": "Dual Core",
    "Single Core Processor": "Single Core",
    "Nine Core": "Nine Cores",
    "Nine-Cores": "Nine Cores",
}
TB_GB_MAP = {
    "1 TB": "1000 GB",
    "1.5 TB": "1500 GB",
    "2 TB": "2000 GB",
    "3 TB": "3000 GB",
}


# other helpful functions
def assign_numeric_rear_camera_count(row):
    """Map camera keywords to a numeric count."""
    cam = row["Camera"].lower()
    if "penta" in cam:
        return 5
    if "quad" in cam:
        return 4
    if "triple" in cam:
        return 3
    if "dual" in cam:
        return 2
    return 1

def calculate_total_mp(cam):
    """Sum rear and front MP values from a camera description string."""
    rear_segment = cam.split("Rear")[0] if "Rear" in cam else cam
    front_segment = cam.split("&", 1)[1] if "&" in cam else ""

    rear_mps = [float(x) for x in re.findall(r"([\d.]+)\s*MP", rear_segment)]
    front_mps = [float(x) for x in re.findall(r"([\d.]+)\s*MP", front_segment)]

    return pd.Series([
        sum(rear_mps) if rear_mps else None,
        sum(front_mps) if front_mps else None,
    ])

def card_normalize(x):
    """Parse memory card description into (supported, type, capacity)."""
    if pd.isna(x):
        return pd.Series([None, None, None])

    x = x.strip()
    for key, value in TB_GB_MAP.items():
        x = x.replace(key, value)

    if "Not Supported" in x:
        return pd.Series([0, None, None])

    card_supported = 1
    card_type = "Hybrid" if "Hybrid" in x else "Dedicated"
    card_capacity = None
    if "upto" in x:
        card_capacity = x.split("upto ")[1].strip().split(" ")[0]

    return pd.Series([card_supported, card_type, card_capacity])


# column cleaning functions 
def clean_name_and_brand(df):
    df["Name"] = (
        df["Name"].str.replace(r"\s+", " ", regex=True).str.strip()
        .str.split("(").str[0].str.strip()
    )
    df["Brand"] = (
        df["Name"].str.split(" ").str[0].str.strip().str.title()
        .replace(BRAND_MAPPING)
    )
    df["Name"] = df["Name"].astype("string")
    df["Brand"] = df["Brand"].astype("string")
    return df

def clean_price_and_specs(df):
    df["Specs"], df["Price"] = df["Price"], df["Specs"]
    df["Price"] = (
        df["Price"].str.replace(r"\s+", " ", regex=True).str.strip()
        .str[1:].str.strip().str.replace(",", "")
    )
    df["Specs"] = df["Specs"].astype("int")
    df["Price"] = df["Price"].astype("int")
    df["Rating"] = df["Rating"].astype("float")
    return df

def clean_sim(df):
    df["Sim"] = df["Sim"].str.strip()
    replacements = {
        "Dual Sim, 5G, NFC, Wi-Fi": "Dual Sim, 5G, VoLTE, NFC, Wi-Fi",
        "Dual Sim, 5G, Wi-Fi": "Dual Sim, 5G, VoLTE, Wi-Fi",
        "4G, Wi-Fi": "Dual Sim, 4G, VoLTE, Wi-Fi",
        "Dual Sim, 4G, Wi-Fi": "Dual Sim, 4G, VoLTE, Wi-Fi",
        "Dual Sim, 5G, Wi-Fi, IR Blaster": "Dual Sim, 5G, VoLTE, Wi-Fi, IR Blaster",
        "Dual Sim, 4G, Wi-Fi, IR Blaster": "Dual Sim, 4G, VoLTE, Wi-Fi, IR Blaster",
        "Dual Sim, 5G, eSIM, Wi-Fi": "Dual Sim, 5G, VoLTE, Vo5G, eSIM, Wi-Fi",
        "Dual Sim, 5G, NFC, Wi-Fi, IR Blaster": "Dual Sim, 5G, VoLTE, NFC, Wi-Fi, IR Blaster",
    }
    df["Sim"] = df["Sim"].replace(replacements)
    df["Sim"] = df["Sim"].str.replace(r"\s+", " ", regex=True).str.strip()

    df["SIM"] = df["Sim"].str.split(", ").str[0].str.strip()
    df["Network"] = df["Sim"].str.split(", ").str[1].str.strip()

    df['VoLTE'] = df['Sim'].str.strip().str.contains('VoLTE')
    df['VoLTE'] = np.where(df['VoLTE'], 1, np.nan)

    df['Vo5G'] = df['Sim'].str.strip().str.contains('Vo5G')
    df['Vo5G'] = np.where(df['Vo5G'], 1, np.nan)

    df['NFC'] = df['Sim'].str.strip().str.contains('NFC')
    df['NFC'] = np.where(df['NFC'], 1, np.nan)

    df['eSIM'] = df['Sim'].str.strip().str.contains('eSIM')
    df['eSIM'] = np.where(df['eSIM'], 1, np.nan)

    df['Wi-Fi'] = df['Sim'].str.strip().str.contains('Wi-Fi')
    df['Wi-Fi'] = np.where(df['Wi-Fi'], 1, np.nan)

    df['IR_Blaster'] = df['Sim'].str.strip().str.contains('IR Blaster')
    df['IR_Blaster'] = np.where(df['IR_Blaster'], 1, np.nan)
    
    # later detected that two columns had the same name due to which load operation was not able to proceed
    df = df.rename(columns={'Sim':'sim_original'})
    return df

def clean_processor(df):
    df["Processor"] = (
        df["Processor"].str.replace(r"\s+", " ", regex=True).str.strip()
    )
    df["Processor"] = df["Processor"].str.strip()

    df.loc[227, "Processor"] = "MediaTek Helio MT8125, Quad Core, 1.4 GHz"
    df.loc[339, "Processor"] = "Unisoc SC9863A, Octa Core, 1.6 GHz"
    df.loc[371, "Processor"] = "Mediatek, Single Core, 1.7Ghz"
    df.loc[584, "Processor"] = "Cortex-A7, Quad Core, 512 MHz"
    df.loc[771, "Processor"] = "MediaTek Helio, Quad Core, 512 MHz"
    df.loc[[501, 774], "Processor"] = "Helio, Single Core, 1.7 GHz Processor"
    df.loc[764, "Processor"] = "Helio, Single Core, 1.3 GHz Processor"
    df.loc[584, "Processor"] = "Cortex-A7, Quad Core, 0.512 GHz"
    df.loc[771, "Processor"] = "MediaTek Helio, Quad Core, 0.512 GHz"

    value_fixes = {
        "Qualcomm Snapdragon 710 AIE, Octa Core, 2.2 GHz Processor": "Snapdragon 710 AIE, Octa Core, 2.2 GHz Processor",
        "Octa Core, 2 GHz Processor": "MediaTek Helio, Octa Core, 2.0 GHz Processor",
        "Octa Core Processor": "Unisoc T7100, Octa Core, 1.82 GHz",
        "Dual Core, 1.7 GHz Processor": "MTK6763, Dual Core, 1.7 GHz Processor",
        "MediaTek Helio MT8125, Quad Core, 1.4 GHz": "Helio MT8125, Quad Core, 1.4 GHz",
        "Mediatek, Single Core, 1.7Ghz": "MT8125, Single Core, 1.7 Ghz",
        "UNISOC 9863a, Octa Core Processor": "Unisoc 9863a, Octa Core Processor",
        "Dual Core Processor": "Unknkown, Dual Core Processor",
    }
    for old, new in value_fixes.items():
        df.loc[df["Processor"] == old, "Processor"] = new

    df["processor_name"] = df["Processor"].str.split(", ").str[0]
    df["processor_cores"] = (
        df["Processor"].str.split(", ").str[1].str.strip()
        .replace(PROCESSORS_CORES_MAP)
    )
    df["processor_clock_speed(GHz)"] = (
        df["Processor"].str.split(", ").str[2].str.strip()
        .str.strip("Processor").str.strip().str.split(" ").str[0]
    )
    return df

def clean_ram_and_storage(df):
    df["Ram"] = df["Ram"].str.replace(r"\s+", " ", regex=True).str.strip()
    df.loc[df["Ram"] == "128 GB inbuilt", "Ram"] = "8 GB RAM, 128 GB inbuilt"
    df.loc[df["Ram"] == "256 GB inbuilt", "Ram"] = "8 GB RAM, 256 GB inbuilt"
    df.loc[df["Ram"] == "5000 mAh Battery", "Ram"] = "4 GB RAM, 128 GB inbuilt"

    df["ram(GB)"] = df["Ram"].str.split(", ").str[0].str.split(" ").str[0]
    df["storage(GB)"] = df["Ram"].str.split(", ").str[1].str.split(" ").str[0]
    df.loc[df["storage(GB)"] == "1", "storage(GB)"] = "1000"
    df.loc[df["storage(GB)"] == "2", "storage(GB)"] = "2000"
    return df

def clean_battery(df):
    df["Battery"] = df["Battery"].str.replace(r"\s+", " ", regex=True).str.strip()
    df.loc[751, "Battery"] = "Unknown Battery with 20W Fast Charging"

    df["battery(mAh)"] = (
        df["Battery"].str.split("with").str[0].str.strip()
        .str.split(" ").str[0].str.strip()
    )
    df["charging_support(W)"] = (
        df["Battery"].str.split("with").str[1].str.strip()
        .str.split(" ").str[0].str.strip("W").str.strip()
        .replace("Fast", "Unknown")
    )
    return df

def clean_display(df):
    df["Display"] = df["Display"].str.replace(r"\s+", " ", regex=True).str.strip()
    df.loc[
        df["Display"] == "12 MP + 12 MP + 12 MP Triple Rear & 12 MP Front Camera",
        "Display",
    ] = "6.1 inches, 2532 × 1170 px, 60 Hz Display with Notch"

    df["display_size"] = df["Display"].str.split(", ").str[0].str.split(" ").str[0]
    df["display_resolution"] = df["Display"].str.split(", ").str[1].str.split("px").str[0]
    df["refresh_rate(Hz)"] = (
        df["Display"].str.split("px").str[1].str.strip(", ").str.strip()
        .str.split("Hz").str[0]
    )
    df.loc[df["refresh_rate(Hz)"].str.contains("Display", na=False), "refresh_rate(Hz)"] = np.nan
    df["display_design"] = (
        df["Display"].str.split("px").str[1].str.strip().str.split("with").str[1]
    )
    df['isFoldable'] = np.where(df['Camera'].str.lower().str.contains("foldable"), 1, np.nan)
    df['isDualDisplay'] = np.where(df['Camera'].str.contains("Dual Display"), 1, np.nan)
    return df

def clean_camera(df):
    df["Camera"] = df["Camera"].str.strip("\n").str.strip()
    df["Camera"] = df["Camera"].str.replace(r"\s+", " ", regex=True).str.strip()

    foldable_idx = df[
        df["Camera"].isin(["Foldable Display, Dual Display", "Dual Display", "Foldable Display"])
    ].index
    df.loc[foldable_idx, "Camera":"Os"] = df.loc[foldable_idx, "Camera":"Os"].shift(-1, axis=1)

    df.loc[df["Camera"] == "Memory Card Not Supported", "Camera"] = (
        "12 MP + 12 MP + 12 MP Triple Rear & 12 MP Front Camera"
    )
    df.loc[762, "Camera"] = "13 MP Rear & 5 MP Front Camera"

    df["rear_main_camera"] = df["Camera"].str.split(" ").str[0]
    df["rear_camera_count"] = df.apply(assign_numeric_rear_camera_count, axis=1)
    df["front_main_camera"] = (
        df[df["Camera"].str.contains("Front")]["Camera"]
        .str.split("& ").str[1].str.split(" ").str[0]
    )
    df['front_camera_count'] = np.where(df['Camera'].str.contains('Front'), 1, 0)
    mask = df['Camera'].str.contains('Dual Front')
    df.loc[mask, 'front_camera_count'] += 1
    df[["rear_total_mp", "front_total_mp"]] = df["Camera"].apply(calculate_total_mp)
    return df

def clean_card_and_os(df):
    df["Os"] = df["Os"].str.replace(r"\s+", " ", regex=True).str.strip()
    
    mask = df["Card"].str.contains("Android", na=False) | df["Card"].str.contains("iOS v14.0", na=False)
    df.loc[mask, "Card":"Os"] = df.loc[mask, "Card":"Os"].shift(axis=1)
    df.loc[df["Os"] == "No FM Radio", "Os"] = np.nan
    
    df[["card_supported", "card_type", "card_capacity(GB)"]] = df["Card"].apply(card_normalize)
    return df

# MAIN FUNCTION
def transform():
    df = pd.read_csv(DATA_DIR / "raw" / "smartphones.csv", index_col="Unnamed: 0")

    # Row 371 has shifting problems
    df.loc[371, "Battery":] = df.loc[371, "Battery":].shift(1)
    df.loc[371, "Battery"] = "5000 mAh Battery"

    # Apply column-level cleaners
    df = clean_name_and_brand(df)
    df = clean_price_and_specs(df)
    df = clean_sim(df)
    df = clean_processor(df)
    df = clean_ram_and_storage(df)
    df = clean_battery(df)
    df = clean_display(df)
    df = clean_camera(df)
    df = clean_card_and_os(df)
    df = df.rename(columns={'Sim':'sim_original'})
    # Save
    output_path = DATA_DIR / "processed" / "smartphones_cleaned.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)

    print(f"Transformed and saved to {output_path} Successfully")



if __name__ == "__main__":
    transform()