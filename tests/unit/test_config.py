from debate.config import load_config


def test_load_config_topic():
    cfg = load_config()
    assert "Godfather" in cfg.debate.topic or "Shawshank" in cfg.debate.topic
    assert cfg.debate.pings_per_side == 10
    assert cfg.gatekeeper.max_total_requests == 200


def test_load_demo_config():
    from debate.config.loader import project_root

    root = project_root()
    cfg = load_config(root / "config" / "demo_setup.json")
    assert cfg.debate.pings_per_side == 5
    assert cfg.gatekeeper.max_total_requests == 80
