"""The old pooled model was unvalidated and is not used by production.
Use the shared country candidate pipeline until panel evaluation exists.
"""
if __name__ == '__main__':
    raise SystemExit('Pooled training retired: use python -m src.models.train_candidate')
