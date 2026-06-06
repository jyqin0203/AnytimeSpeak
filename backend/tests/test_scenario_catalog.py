from app.scenario_catalog import get_scenario_prompt_config, list_scenario_prompt_configs


def test_catalog_contains_required_prompt_scenarios():
    scenario_ids = {scenario.scenario_id for scenario in list_scenario_prompt_configs()}

    assert {
        "interview",
        "ordering_food",
        "meeting",
        "travel",
        "daily_conversation",
    }.issubset(scenario_ids)


def test_restaurant_alias_preserves_existing_backend_scenario_id():
    config = get_scenario_prompt_config("restaurant")

    assert config.scenario_id == "ordering_food"
    assert config.title_zh == "点餐"
    assert config.ai_role == "Restaurant server"
    assert "cafe" in config.default_story_seed.story_intro_en.lower()
    assert "I'd like" in config.useful_expressions


def test_catalog_scenarios_provide_at_least_three_story_seeds():
    for config in list_scenario_prompt_configs():
        assert config.scenario_id
        assert config.title_en
        assert config.title_zh
        assert config.ai_role
        assert config.user_role
        assert config.goal
        assert len(config.story_seeds) >= 3
        seed_ids = {seed.seed_id for seed in config.story_seeds}
        assert len(seed_ids) == len(config.story_seeds)
        for seed in config.story_seeds:
            assert seed.seed_id
            assert len(seed.story_intro_zh) > 20
            assert len(seed.story_intro_en) > 40
            assert seed.opening_message
        assert config.default_story_seed in config.story_seeds
        assert config.conversation_style
        assert config.feedback_focus
        assert config.useful_expressions
