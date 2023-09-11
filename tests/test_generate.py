from generate import default_service_plans, fill_in_gaps


def test_adding_kafka_connect_service():
    context = {
        "environment": {
            "services": {"kafka": "business-4"},
            "integrations": {"kafka": ["kafka_connect"]},
        }
    }
    context = fill_in_gaps(context)
    assert (
        context["environment"]["services"]["kafka_connect"]
        == default_service_plans["kafka_connect"]
    )


def test_adding_kafka_connect_integration():
    context = {
        "environment": {
            "services": {"kafka": "business-4", "kafka_connect": "startup-4"},
            "integrations": {},
        }
    }
    context = fill_in_gaps(context)
    assert "kafka_connect" in context["environment"]["integrations"]["kafka"]


def test_adding_flink_service():
    context = {
        "environment": {
            "services": {"kafka": "business-4"},
            "integrations": {"kafka": ["flink"]},
        }
    }
    context = fill_in_gaps(context)
    assert context["environment"]["services"]["flink"] == default_service_plans["flink"]


def test_adding_flink_integration_single():
    context = {
        "environment": {
            "services": {"kafka": "business-4", "flink": "business-4"},
            "integrations": {},
        }
    }
    context = fill_in_gaps(context)
    assert "flink" in context["environment"]["integrations"]["kafka"]


def test_adding_flink_integration_multi():
    context = {
        "environment": {
            "services": {
                "kafka": "business-4",
                "flink": "business-4",
                "pg": "business-4",
                "opensearch": "business-4",
            },
            "integrations": {},
        }
    }
    context = fill_in_gaps(context)
    for service in ["kafka", "pg", "opensearch"]:
        assert "flink" in context["environment"]["integrations"][service]


def test_adding_metrics_database_1():
    context = {
        "environment": {
            "services": {"kafka": "business-4"},
            "integrations": {"kafka": ["metrics"]},
        }
    }
    context = fill_in_gaps(context)
    assert context["metrics_database"] == "influxdb"
    assert (
        context["environment"]["services"]["influxdb"]
        == default_service_plans["influxdb"]
    )


def test_adding_metrics_database_2():
    context = {
        "environment": {
            "services": {"kafka": "business-4", "influxdb": "xxx"},
            "integrations": {"kafka": ["metrics"]},
        }
    }
    context = fill_in_gaps(context)
    assert context["metrics_database"] == "influxdb"
    assert context["environment"]["services"]["influxdb"] == "xxx"


def test_adding_metrics_database_3():
    context = {
        "environment": {
            "services": {"kafka": "business-4", "m3db": "xxx"},
            "integrations": {"kafka": ["metrics"]},
        }
    }
    context = fill_in_gaps(context)
    assert context["metrics_database"] == "m3db"
    assert "influxdb" not in context["environment"]["services"]


def test_adding_metrics_database_4():
    context = {
        "environment": {
            "services": {"kafka": "business-4", "influxdb": "xxx", "m3db": "xxx"},
            "integrations": {"kafka": ["metrics"]},
        }
    }
    context = fill_in_gaps(context)
    assert context["metrics_database"] == "influxdb"


def test_adding_opensearch_service_for_logs():
    context = {
        "environment": {
            "services": {"kafka": "business-4"},
            "integrations": {"kafka": ["logs"]},
        }
    }
    context = fill_in_gaps(context)
    assert (
        context["environment"]["services"]["opensearch"]
        == default_service_plans["opensearch"]
    )


def test_adding_prometheus_endpoint():
    context = {
        "environment": {
            "services": {"kafka": "business-4"},
            "integrations": {"kafka": ["prometheus"]},
        }
    }
    context = fill_in_gaps(context)
    assert "prometheus" in context["environment"]["integration_endpoints"]


def test_adding_jolokia_endpoint():
    context = {
        "environment": {
            "services": {"kafka": "business-4"},
            "integrations": {"kafka": ["jolokia"]},
        }
    }
    context = fill_in_gaps(context)
    assert "jolokia" in context["environment"]["integration_endpoints"]
