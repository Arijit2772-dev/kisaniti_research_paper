"""Tests for ceda_fetch.py against a local fake CEDA server (no network, no real token)."""
import argparse, json, os, sys, tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ceda_fetch as cf

TOKEN = "TEST-TOKEN-NOT-REAL"
state = {"throttled": False, "prices_calls": 0}


class Fake(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def reply(self, code, obj=None, headers=None):
        body = json.dumps(obj).encode() if obj is not None else b""
        self.send_response(code)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authed(self):
        if self.headers.get("Authorization") != f"Bearer {TOKEN}":
            self.reply(401, {"error": "bad token"}); return False
        return True

    def do_GET(self):
        if not self.authed(): return
        if self.path.endswith("/commodities"):
            self.reply(200, {"commodities": [{"id": 7, "name": "Paddy(Basmati)"}, {"id": 8, "name": "Wheat"}]})
        elif self.path.endswith("/geographies"):
            self.reply(200, {"geographies": [{"state_id": 28, "state_name": "Punjab",
                     "districts": [{"district_id": 1, "district_name": "Patiala"}]}]})
        else:
            self.reply(404)

    def do_POST(self):
        if not self.authed(): return
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.path.endswith("/prices"):
            state["prices_calls"] += 1
            if not state["throttled"]:
                state["throttled"] = True
                self.reply(429, {"error": "slow down"}, {"Retry-After": "1"}); return
            year = int(req["from_date"][:4])
            self.reply(200, {"data": [
                {"date": f"{year}-10-0{d}", "commodity_id": req["commodity_id"], "census_state_id": 3,
                 "census_district_id": 4, "market_id": m, "min_price": 2000.0, "max_price": 2500.0,
                 "modal_price": 2300.0} for d in (1, 2) for m in (11, 12)]})
        elif self.path.endswith("/markets"):
            self.reply(200, {"data": [{"census_state_id": 3, "census_district_id": 4, "market_id": 11, "market_name": "Patiala"}]})
        else:
            self.reply(404)


class CedaFetchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), Fake)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.tmp = tempfile.TemporaryDirectory()
        cf.BASE = f"http://127.0.0.1:{cls.server.server_port}/v1"
        cf.ROOT = Path(cls.tmp.name)
        cf.OUT = cf.ROOT / "data" / "raw" / "ceda"
        os.environ["CEDA_API_TOKEN"] = TOKEN

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.tmp.cleanup()

    def test_1_discover_then_fetch_with_retry_and_checksums(self):
        cf.cmd_discover(argparse.Namespace())
        ref = cf.OUT / "_reference" / "commodities.json"
        self.assertTrue(ref.exists())
        args = argparse.Namespace(commodity_id=7, state_id=28, from_date="2019-06-01", to_date="2020-03-31",
                                  quantities=False, pause=0, force=False)
        cf.cmd_fetch(args)
        files = sorted((cf.OUT / "c7_s28" / "prices").glob("prices_????.json"))
        self.assertEqual([f.name for f in files], ["prices_2019.json", "prices_2020.json"])
        self.assertGreaterEqual(state["prices_calls"], 3)          # 429 once, then success
        m = json.loads(files[0].with_suffix(".json.manifest.json").read_text())
        self.assertEqual(m["sha256"], cf.sha256(files[0].read_bytes()))
        self.assertEqual(m["records"], 4)
        self.assertEqual(m["request"]["from_date"], "2019-06-01")  # year chunk starts at the request start
        self.assertEqual(m["origin"], "REAL")

    def test_2_second_run_does_not_overwrite(self):
        before = (cf.OUT / "c7_s28" / "prices" / "prices_2019.json").stat().st_mtime_ns
        cf.cmd_fetch(argparse.Namespace(commodity_id=7, state_id=28, from_date="2019-06-01",
                                        to_date="2019-12-31", quantities=False, pause=0, force=False))
        self.assertEqual(before, (cf.OUT / "c7_s28" / "prices" / "prices_2019.json").stat().st_mtime_ns)

    def test_3_token_never_written(self):
        for f in cf.OUT.rglob("*"):
            if f.is_file():
                self.assertNotIn(TOKEN, f.read_text())

    def test_4_wrong_token_stops(self):
        os.environ["CEDA_API_TOKEN"] = "wrong"
        try:
            with self.assertRaises(SystemExit):
                cf.request("GET", "/agmarknet/commodities")
        finally:
            os.environ["CEDA_API_TOKEN"] = TOKEN

    def test_5_markets(self):
        cf.cmd_markets(argparse.Namespace(commodity_id=7, state_id=28, indicator="price", force=False))
        self.assertTrue((cf.OUT / "c7_s28" / "markets" / "district_1.json").exists())

    def test_6_ingest_file_idempotent_and_conflict(self):
        src = Path(self.tmp.name) / "portal_download.csv"
        src.write_text("a,b\n1,2\n")
        cf.cmd_ingest_file(argparse.Namespace(paths=[str(src)]))
        cf.cmd_ingest_file(argparse.Namespace(paths=[str(src)]))   # same bytes: no-op
        src.write_text("a,b\n9,9\n")
        with self.assertRaises(SystemExit):
            cf.cmd_ingest_file(argparse.Namespace(paths=[str(src)]))

    def test_7_missing_token(self):
        del os.environ["CEDA_API_TOKEN"]
        try:
            with self.assertRaises(SystemExit):
                cf.request("GET", "/agmarknet/commodities")
        finally:
            os.environ["CEDA_API_TOKEN"] = TOKEN


if __name__ == "__main__":
    unittest.main(verbosity=2)
