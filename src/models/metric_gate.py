"""Operational check only. Never copies candidate artifacts into production."""
import argparse
import json
from pathlib import Path
from src.models.validation import quality_gate

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate', required=True)
    parser.add_argument('--incumbent')
    args = parser.parse_args()
    quality_gate(json.loads(Path(args.candidate).read_text()),
                 json.loads(Path(args.incumbent).read_text()) if args.incumbent else None)
    print('Gate passed; manual review still required. Nothing promoted.')
