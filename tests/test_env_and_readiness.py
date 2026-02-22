from pathlib import Path

from omega_quant.config.alpaca_config import get_alpaca_config
from omega_quant.ops.env_loader import load_dotenv_if_present
from omega_quant.ui_service import run_action


def test_dotenv_loader_reads_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('.env').write_text('ALPACA_API_KEY=abc\nALPACA_API_SECRET=def\n', encoding='utf-8')
    assert load_dotenv_if_present()
    cfg = get_alpaca_config()
    assert cfg['api_key'] == 'abc'
    assert cfg['api_secret'] == 'def'


def test_alpaca_config_defaults(monkeypatch):
    monkeypatch.delenv('ALPACA_DATA_BASE_URL', raising=False)
    monkeypatch.delenv('ALPACA_WS_URL', raising=False)
    cfg = get_alpaca_config()
    assert cfg['data_base_url'].startswith('https://')
    assert cfg['ws_url'].startswith('wss://')


def test_live_readiness_contains_next_actions(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = run_action('live_readiness')
    assert 'readiness' in out
    for item in out['readiness'].values():
        assert 'next_action' in item
        assert str(item['next_action']).strip() != ''


def test_ui_refresh_related_actions_do_not_crash(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert 'status' in run_action('paper_account')
    assert 'status' in run_action('live_readiness')
    assert 'status' in run_action('alpaca_setup')
