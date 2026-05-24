from debate.config import load_config


def test_load_config_topic():
    cfg = load_config()
    assert "Godfather" in cfg.debate.topic or "Shawshank" in cfg.debate.topic
    assert cfg.debate.pings_per_side >= 5
