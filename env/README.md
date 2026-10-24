# Research environment (R0)

- Python 3.13 (v2 used 3.13.1). Direct pins: `requirements.in`; full lock: `requirements.lock` (`uv pip compile`).
- Create: `env/setup.sh` (needs [uv](https://docs.astral.sh/uv/)). It installs the lock, then the shared algorithm package with `pip install -e ../kisaniti_implementation/core` (CHAT-28).
- Run any script with `env/run <script.py>`. It adds `core/src` to `PYTHONPATH`, because on macOS the files inside `.venv` can carry the "hidden" flag and Python 3.13 skips hidden `.pth` files, so the editable install may not load otherwise.
- NumPy is 2.2.6 instead of the v2 run's 1.26.4 (no Python 3.13 wheel for 1.26.4). The v2 results still reproduce exactly (`results/R0_v2_reproduction/report.md`).
