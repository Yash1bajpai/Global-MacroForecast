"""Compatibility entry point: shared causal candidate pipeline, not deployment."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.train_candidate import train_country

if __name__ == '__main__':
    train_country('india', 'candidate_artifacts')
