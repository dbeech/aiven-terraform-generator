# Aiven Terraform Generator

This script takes a simple environment file defined in yaml and converts it to Terraform code to create Aiven services and integrations.

**Features and benefits**:

* One-line configuration of public vs private networking
* Much easier to define logging and monitoring integrations; reducing boilerplate and need for copy/paste. The script will automatically add services for OpenSearch, InfluxDB and Grafana if needed where an integration of type `logs` or `metrics` is specified.
* Where a Flink service is requested, integrations for all other eligible services will be automatically added (e.g. Kafka, PostgreSQL, OpenSearch)

**Instructions to run:**

```
usage: generate.py [-h] [-i INPUT] [-o OUTPUT] [-p PREFIX] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        Path to the input YML file
  -o OUTPUT, --output OUTPUT
                        Path to the output directory
  -p PREFIX, --prefix PREFIX
                        Prefix for generated resource names
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Set the logging level
```

**Example definition file:**

```yaml
environment:
  project: dbeech-demo
  cloud: aws-eu-central-1
  networking: vpc
  services:
    kafka: business-8
    pg: business-8
  integrations:
    kafka:
      - logs
      - metrics
      - kafka_connect
      - flink
  configs:
    kafka:
      auto_create_topics_enable: false
```
