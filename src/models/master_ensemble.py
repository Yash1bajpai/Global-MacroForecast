"""Train/evaluate research candidates only. Production remains unchanged."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.train_candidate import run

if __name__ == '__main__':
    run('candidate_artifacts')
