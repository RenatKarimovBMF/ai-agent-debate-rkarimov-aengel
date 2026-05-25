from debate.config import load_config, with_custom_debate


def test_custom_debate_override():
    cfg = load_config()
    custom = with_custom_debate(
        cfg,
        pro_side="Alpha",
        con_side="Beta",
        topic="Which is better?",
    )
    assert custom.debate.pro_side == "Alpha"
    assert custom.debate.con_side == "Beta"
    assert custom.debate.topic == "Which is better?"
