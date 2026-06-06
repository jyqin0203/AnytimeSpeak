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
    assert "busy cafe" in config.story_intro.lower()
    assert "I'd like" in config.useful_expressions


def test_catalog_scenarios_include_story_intro_and_opening_message():
    for config in list_scenario_prompt_configs():
        assert config.scenario_id
        assert config.title_en
        assert config.title_zh
        assert config.ai_role
        assert config.user_role
        assert config.goal
        assert len(config.story_intro) > 40
        assert config.opening_message
        assert config.conversation_style
        assert config.feedback_focus
        assert config.useful_expressions
