#!/usr/bin/env python3
"""NEXUS-LUNAR: Chandrayaan-2 (OHRC, TMC-2, IIRS) ISSDC Ingestion CLI.

Ingests downloaded Chandrayaan-2 ZIP/TAR archives or folders from ISSDC PRADAN,
extracts PDS4 metadata, generates normalized previews, and indexes them into the catalog.

Usage:
  python scripts/ingest_issdc.py --input /path/to/downloaded_ch2_bundle.zip
  python scripts/ingest_issdc.py --input /path/to/ch2_raw_folder/
"""

import sys
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from packages.data_pipeline import (
    ISSDCClient,
    LunarDataCatalog,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nexus.cli.ingest_issdc")


def main():
    parser = argparse.ArgumentParser(description="Chandrayaan-2 ISSDC PRADAN Ingestion Utility")
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to downloaded ZIP/TAR archive or directory containing PDS4 XML labels",
    )
    parser.add_argument("--raw-dir", type=str, default="data/raw", help="Target raw data directory")
    parser.add_argument("--catalog-file", type=str, default="data/catalog.json", help="Path to catalog index")

    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        sys.exit(1)

    client = ISSDCClient(raw_dir=args.raw_dir)
    catalog = LunarDataCatalog(catalog_file=args.catalog_file)

    if input_path.is_file() and input_path.suffix.lower() in (".zip", ".tar", ".gz", ".tgz"):
        logger.info(f"Ingesting ISSDC archive: {input_path}")
        observations = client.ingest_archive(input_path)
    elif input_path.is_dir():
        logger.info(f"Ingesting ISSDC directory: {input_path}")
        observations = client.ingest_directory(input_path)
    elif input_path.is_file() and input_path.suffix.lower() == ".xml":
        logger.info(f"Ingesting single PDS4 XML: {input_path}")
        obs = client.parse_pds4_xml(input_path)
        if obs.primary_image_path and Path(obs.primary_image_path).exists():
            target_dir = client.raw_dir / obs.sensor.value.lower() / obs.product_id
            target_dir.mkdir(parents=True, exist_ok=True)
            preview_file = target_dir / f"{obs.product_id}_preview.png"
            if not preview_file.exists():
                client._generate_preview_from_raster(obs.primary_image_path, preview_file)
            if preview_file.exists():
                obs.preview_image_path = str(preview_file.resolve())
            elif not obs.preview_image_path:
                obs.preview_image_path = obs.primary_image_path
        observations = [obs]
    else:
        logger.error(f"Unsupported input file type: {input_path}")
        sys.exit(1)

    if not observations:
        logger.warning("No valid Chandrayaan-2 observations found to ingest.")
        return

    catalog.add_observations(observations)
    print("\n=== Ingestion Summary ===")
    for obs in observations:
        print(f"✓ Ingested [{obs.sensor.value}] {obs.product_id}")
        print(f"  Bounds: Lat [{obs.bbox.min_lat:.2f}, {obs.bbox.max_lat:.2f}], Lon [{obs.bbox.min_lon:.2f}, {obs.bbox.max_lon:.2f}]")
        print(f"  Resolution: {obs.spatial_resolution_m}m | Solar Zenith: {obs.geometry.solar_zenith_deg}°")
        print(f"  Primary Image: {obs.primary_image_path or 'Pending/Raw'}")

    print(f"\nTotal {len(observations)} observations indexed into {args.catalog_file}!")


if __name__ == "__main__":
    main()
