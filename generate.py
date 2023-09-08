import argparse
import logging
import os
import random
import string
import sys
from collections import defaultdict

import yaml
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("aiven-terraform-generator")
logging.basicConfig()

default_service_plans = {
    "kafka_connect": "startup-4",
    "flink": "business-4",
    "influxdb": "startup-4",
    "opensearch": "startup-4",
    "grafana": "startup-1",
}

default_versions = {"flink": "1.16", "kafka": "3.5", "pg": "14", "m3db": "1.5"}


def is_valid_file(path):
    if not os.path.exists(path):
        logger.fatal(f"{path} does not exist")
        sys.exit(1)
    if not os.path.isfile(path):
        logger.fatal(f"{path} is not a valid file")
        sys.exit(1)
    return path


def is_valid_directory(path):
    if os.path.isfile(path):
        logger.fatal(f"{path} is not a valid directory")
        sys.exit(1)
    os.makedirs(path, exist_ok=True)
    return path


def validate(context):
    if not "environment" in context:
        logger.fatal("No environment specified")
        sys.exit(1)
    environment = context["environment"]
    if not "project" in environment:
        logger.fatal("No environment specified")
        sys.exit(1)
    if not "services" in environment or not isinstance(environment["services"], dict):
        logger.fatal("No services specified")
        sys.exit(1)
    if not "integrations" in environment:
        logger.warning("No integrations specified")
    if "networking" in environment and environment["networking"] not in [
        "public",
        "vpc",
        "privatelink",
    ]:
        logger.warning(
            "Ignoring invalid for 'networking' - must be one of 'public', 'vpc', 'privatelink'"
        )
    return True


def fill_in_gaps(context):

    logger.debug("Original context: %s", context)

    environment = defaultdict(dict, context["environment"])
    services = defaultdict(str, environment["services"])
    integrations = defaultdict(list, environment["integrations"])
    integration_endpoints = set(environment["integration_endpoints"])

    # If we've asked for Kafka Connect service but there's no Connect integration for Kafka, add one
    if "kafka_connect" in services:
        if not "kafka_connect" in integrations["kafka"]:
            integrations["kafka"].append("kafka_connect")

    # If we've asked for Kafka Connect integration but there's no Kafka Connect service, add one
    if "kafka_connect" in integrations["kafka"] and not "kafka_connect" in services:
        services["kafka_connect"] = default_service_plans["kafka_connect"]

    # If a service asks for Flink integration but there's no Flink service, add one
    for flink_candidate_service in {"kafka", "pg", "opensearch"}.intersection(
        services.keys()
    ):
        if "flink" in integrations[flink_candidate_service] and not "flink" in services:
            services["flink"] = default_service_plans["flink"]
            break

    # If we've asked for Flink service (or just added it), add all eligible integrations
    if "flink" in services:
        for flink_candidate_service in ["kafka", "pg", "opensearch"]:
            if (
                flink_candidate_service in integrations
                and not "flink" in integrations[flink_candidate_service]
            ):
                integrations[flink_candidate_service].append("flink")

    # If any service asks for metrics integration but there's no InfluxDB or M3DB service, add an InfluxDB
    metrics_integration_requested = False
    for service in services:
        if service in integrations and "metrics" in integrations[service]:
            metrics_integration_requested = True
            break

    if "influxdb" in services:
        context["metrics_database"] = "influxdb"
    elif "m3db" in services:
        context["metrics_database"] = "m3db"

    if metrics_integration_requested:
        if "metrics_database" not in context:
            services["influxdb"] = default_service_plans["influxdb"]
            context["metrics_database"] = "influxdb"
        if not "grafana" in services:
            services["grafana"] = default_service_plans["grafana"]
            integrations["grafana"] = ["dashboard"]

    # If any service asks for logs integration but there's no OpenSearch service, add an OpenSearch
    for service in services:
        if service in integrations and "logs" in integrations[service]:
            if not "opensearch" in services:
                services["opensearch"] = default_service_plans["opensearch"]
                break

    # If any service asks for Prometheus or Jolokia integration but there's no endpoint, add that
    for service in services:
        if (
            "prometheus" in integrations[service]
            and not "prometheus" in integration_endpoints
        ):
            integration_endpoints.add("prometheus")
        if (
            "jolokia" in integrations[service]
            and not "jolokia" in integration_endpoints
        ):
            integration_endpoints.add("jolokia")

    # Save the updated context back
    context["environment"]["services"] = dict(services)
    context["environment"]["integrations"] = dict(integrations)
    context["environment"]["integration_endpoints"] = list(integration_endpoints)
    logger.debug("Enriched context: %s", context)

    return context


def generate_random_string(length=8):
    allowed_chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(allowed_chars) for _ in range(length))


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        "--input",
        type=is_valid_file,
        default="definition.yml",
        help="Path to the input YML file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=is_valid_directory,
        default="output",
        help="Path to the output directory",
    )
    parser.add_argument(
        "-p",
        "--prefix",
        type=str,
        default="tf-gen",
        help="Prefix for generated resource names",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level",
    )
    args = parser.parse_args()

    logger.setLevel(args.log_level)

    # Initialize the Jinja2 environment with the path to the templates folder
    env = Environment(
        loader=FileSystemLoader("templates"), trim_blocks=True, lstrip_blocks=True
    )
    env.globals["generate_random_string"] = generate_random_string

    # Load the YAML file to get the context data
    logger.info("Loading context from %s", args.input)
    with open(args.input, "r") as f:
        context = yaml.safe_load(f)
        context["prefix"] = args.prefix
        context["version_numbers"] = default_versions

    # Validate and enrich the context with missing services/integrations if needed
    validate(context)
    context = fill_in_gaps(context)

    # Load the main template and render
    template = env.get_template("main.tf.j2")
    output = template.render(context)

    # Write the generated Terraform code to main.tf in the output directory
    output_path = os.path.join(args.output, "main.tf")
    with open(output_path, "w") as f:
        f.write(output)

    logger.info("Terraform code successfully written to %s", output_path)


if __name__ == "__main__":
    main()
