# LaunchDarkly SDK Prometheus Exporter

A Prometheus exporter that collects LaunchDarkly SDK usage metrics and service connection data, providing visibility into SDK versions in use and billable connection counts.

## Features

- 📊 **SDK Version Tracking** - Monitor SDK versions and connection counts by language and version
- 💰 **Service Connection Monitoring** - Track billable server-side and client-side connections
- 📈 **Prometheus Format** - Standard Prometheus metrics endpoint for easy integration
- 🐳 **Docker Support** - Containerized deployment with Docker Compose
- 🚀 **Flask Web Server** - Built-in endpoints: `/metrics`, `/health`, `/`
- 🔐 **Secure API Access** - LaunchDarkly API authentication with beta API support
- ⚙️ **Configurable** - Customizable scrape intervals and time ranges
- 📉 **Clean Metrics** - No default Python metrics, only LaunchDarkly data
- 🔍 **Timestamp Labels** - Track when metrics were collected

## How It Works

The exporter uses LaunchDarkly's usage APIs to collect metrics:

1. **Stream Usage by SDK Version API** - Fetches SDK version distribution and connection counts
2. **Service Connections API** - Retrieves billable server-side connection counts
3. **Data Processing** - Extracts the most recent data point with timestamp
4. **Metric Exposition** - Exposes data via Prometheus-compatible `/metrics` endpoint
5. **Automated Collection** - Updates metrics on a configurable interval (default: 5 minutes)

## API Headers

The exporter uses proper LaunchDarkly REST API headers:

- **Authorization**: API access token from `LAUNCHDARKLY_API_KEY`
- **Content-Type**: `application/json`
- **LD-API-Version**: `beta` (beta API version)

## Endpoints

The exporter exposes the following HTTP endpoints:

- **`/metrics`** - Prometheus metrics endpoint (scraped by Prometheus)
- **`/health`** - Health check endpoint with last scrape timestamp
- **`/`** - Simple HTML index page with links to other endpoints

## Metrics

The exporter provides the following Prometheus metrics:

### SDK Usage Metrics

- **`launchdarkly_sdk_clients_by_type_and_version`** - SDK connections by language and version
  - Labels: `sdk_name`, `version`
  - Type: Gauge
  - Description: Number of connections for each SDK version at the time of collection

### Connection Count Metrics

- **`launchdarkly_service_connection_minutes`** - Server-side service connection minutes (billable)
  - Labels: `sdk_name`, `sdk_version`, `sdk_app_id`
  - Type: Gauge
  - Description: Month-to-date (cumulative, resets monthly) connection minutes, grouped by SDK, SDK version and application ID. Use `increase()` for per-period values.

### Exporter Metrics

- **`launchdarkly_exporter_api_requests_total`** - API request counter
  - Labels: `endpoint`, `status`
  - Type: Counter
  - Description: Total API requests made to LaunchDarkly

- **`launchdarkly_exporter_last_scrape_timestamp_seconds`** - Last scrape time
  - Type: Gauge
  - Description: Unix timestamp of the last successful metrics collection

- **`launchdarkly_exporter_info`** - Exporter information
  - Labels: `version`, `base_url`
  - Type: Info
  - Description: Version and configuration details

## Requirements

- Python 3.11+
- LaunchDarkly API key with appropriate permissions
- Network access to LaunchDarkly API

## Configuration

The exporter is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LAUNCHDARKLY_API_KEY` | LaunchDarkly API key (required) | - |
| `LAUNCHDARKLY_BASE_URL` | LaunchDarkly API base URL | `https://app.launchdarkly.com` |
| `EXPORTER_PORT` | Port to serve metrics on | `8000` |
| `SCRAPE_INTERVAL` | How often to scrape LaunchDarkly API (seconds) | `300` |

## Installation & Usage

### Local Development

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set your LaunchDarkly API key:

   ```bash
   export LAUNCHDARKLY_API_KEY="your-api-key-here"
   ```

3. Run the exporter:

   ```bash
   python main.py
   ```

4. View metrics at `http://localhost:8000/metrics`

### Testing the Exporter

After starting the exporter, you can test all endpoints:

```bash
# Test all endpoints
python test_exporter.py

# Or manually test each endpoint
curl http://localhost:8000/              # Index page
curl http://localhost:8000/health        # Health check
curl http://localhost:8000/metrics       # Prometheus metrics
```

### Docker

1. Build the image:
   ```bash
   docker build -t ld-sdk-exporter .
   ```

2. Run the container:
   ```bash
   docker run -d \
     --name ld-sdk-exporter \
     -p 8000:8000 \
     -e LAUNCHDARKLY_API_KEY="your-api-key-here" \
     ld-sdk-exporter
   ```

### Docker Compose

```yaml
version: '3.8'
services:
  ld-sdk-exporter:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LAUNCHDARKLY_API_KEY=your-api-key-here
      - SCRAPE_INTERVAL=300
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped
```

## Prometheus Configuration

Add the exporter to your `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'launchdarkly-sdk-exporter'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 60s
    metrics_path: /metrics
```

## Example Queries

Here are some useful Prometheus queries for the exported metrics:

### SDK Version Distribution

```promql
launchdarkly_sdk_clients_by_type_and_version
```

### Total Connections by SDK

```promql
sum by (sdk_name) (launchdarkly_sdk_clients_by_type_and_version)
```

### Top 10 Most Used SDK Versions

```promql
topk(10, launchdarkly_sdk_clients_by_type_and_version)
```

### Service Connection Count (Billable)

```promql
launchdarkly_service_connection_minutes
```

### Connection Trends Over Time

```promql
sum by (sdk_app_id) (increase(launchdarkly_service_connection_minutes[1d]))
```

### Exporter Health Check

```promql
time() - launchdarkly_exporter_last_scrape_timestamp_seconds < 600
```

### API Error Rate

```promql
rate(launchdarkly_exporter_api_requests_total{status="error"}[5m])
```

## Grafana Dashboard

Create visualizations in Grafana using the exported metrics:

1. **SDK Version Heatmap**: Show SDK versions over time
2. **MAU Trends**: Line chart of monthly active users
3. **SDK Type Distribution**: Pie chart of client vs server SDKs
4. **API Health**: Status of LaunchDarkly API calls
5. **Top SDKs**: Bar chart of most popular SDK versions

## API Details & Limitations

### APIs Used

1. **Stream Usage by SDK Version API** (`/api/v2/usage/streams/{source}/bysdkversion`)
   - Provides SDK version distribution and connection counts
   - Returns time-series data with metadata mapping

2. **Service Connections API** (`/api/v2/usage/service-connections`)
   - Provides billable connection counts
   - Supports daily, hourly, or monthly granularity

### Important Notes

- **Beta API**: The stream usage API is in beta and subject to changes
- **Timestamp Handling**: The exporter uses the most recent non-empty data point (API sometimes returns empty latest values)
- **Version Cleaning**: SDK versions with git commit hashes (e.g., `8.7.0+60328b1f`) are cleaned to remove the hash portion
- **Index Mapping**: Metadata array indices map to series data keys (e.g., index 0 → key "0")
- **Rate Limiting**: API rate limits may apply; adjust scrape intervals accordingly
- **Data Lag**: Most recent data may have a slight delay due to API processing

## Development

### Adding New Metrics

1. Define the metric in the `__init__` method of `LaunchDarklySDKExporter`
2. Implement collection logic in the `collect_metrics` method
3. Update documentation

### Testing

Run the exporter locally and verify metrics:

```bash
curl http://localhost:8000/metrics
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**: Check your API key
2. **No metrics appearing**: Verify API key permissions and network connectivity
3. **High memory usage**: Consider reducing scrape frequency for large organizations
4. **Rate limiting**: Increase scrape interval if hitting API limits

### Logging

The exporter logs to stdout. Set the log level with:

```bash
export LOG_LEVEL=DEBUG
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request
