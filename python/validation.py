import argparse
import logging
import sys
from pathlib import Path

from data_parsing.config import PROJECT_DATA
from data_parsing.pipeline import load_warband_data, validate_warband_data


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(name)s - %(message)s'
    )

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data",
        type=Path,
        default=PROJECT_DATA,
        help="path to project data folder"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as errors"
    )
    args = parser.parse_args()

    try:
        # Load data
        data = load_warband_data(src=args.data)

        # Validate using CompositeValidator
        result = validate_warband_data(data, strict=args.strict)

        # Print detailed report
        print("\n" + "="*60)
        print(result.detailed_report())
        print("="*60)

        logging.info('Validation PASSED')
        sys.exit(0)

    except Exception as e:
        logging.error(f'Validation FAILED: {e}')
        if hasattr(e, 'validation_result') and e.validation_result:
            print("\n" + e.validation_result.detailed_report())
        sys.exit(1)
