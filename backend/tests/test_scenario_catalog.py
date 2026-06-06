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
    assert "I'd like" in config.useful_expressions
