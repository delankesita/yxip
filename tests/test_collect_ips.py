import os
import sys
from pathlib import Path
from textwrap import dedent
from types import SimpleNamespace

import pytest

# ensure project root on path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import collect_ips as ci


HTML_SAMPLE = dedent(
    """
    <html>
      <body>
        <table>
          <tr><td>104.26.4.90</td></tr>
          <tr><td>162.159.140.116</td></tr>
        </table>
        <ul>
          <li>duplicate 104.26.4.90</li>
          <li>other 172.64.52.127</li>
        </ul>
      </body>
    </html>
    """
)


def test_parse_ips_from_html_extracts_unique_ips():
    ips = ci.parse_ips_from_html(HTML_SAMPLE)
    assert ips == [
        "104.26.4.90",
        "162.159.140.116",
        "172.64.52.127",
    ]


def test_collect_ips_dedup_and_merge(monkeypatch):
    def fake_get(url, timeout=0):  # noqa: ARG001
        return SimpleNamespace(text=HTML_SAMPLE, raise_for_status=lambda: None)

    monkeypatch.setenv("CF_AUDIT_LOG", "")  # disable file logging path creation issues
    monkeypatch.setattr("requests.get", fake_get)

    urls = ["https://a.example", "https://b.example"]
    ips = ci.collect_ips(urls)

    # HTML_SAMPLE contains 3 unique, but fetched twice should still be 3 due to dedup
    assert sorted(ips) == sorted([
        "104.26.4.90",
        "162.159.140.116",
        "172.64.52.127",
    ])


def test_write_ips_file_overwrites_atomically(tmp_path, monkeypatch):
    out = tmp_path / "ip.txt"

    # initial write
    ci.write_ips_file(str(out), ["1.1.1.1", "2.2.2.2"])
    assert out.read_text().strip().splitlines() == ["1.1.1.1", "2.2.2.2"]

    # overwrite with different content
    ci.write_ips_file(str(out), ["9.9.9.9"]) 
    assert out.read_text().strip().splitlines() == ["9.9.9.9"]


def test_e2e_run_main_creates_outputs(tmp_path, monkeypatch):
    # point audit log to temp
    monkeypatch.setenv("CF_AUDIT_LOG", str(tmp_path / "audit.log"))

    # mock network
    def fake_get(url, timeout=0):  # noqa: ARG001
        return SimpleNamespace(text=HTML_SAMPLE, raise_for_status=lambda: None)

    monkeypatch.setattr("requests.get", fake_get)

    # run main in temp cwd so ip.txt is created there
    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        ci.main()
    finally:
        os.chdir(cwd)

    ip_file = tmp_path / "ip.txt"
    log_file = tmp_path / "audit.log"

    assert ip_file.exists(), "ip.txt should be created"
    content = ip_file.read_text().strip().splitlines()
    assert set(content) == {"104.26.4.90", "162.159.140.116", "172.64.52.127"}

    # audit log should contain key events
    log_content = log_file.read_text()
    assert "start collection" in log_content
    assert "wrote" in log_content
