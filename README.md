# LaunchDarkly SDK Prometheus Exporter

This Prometheus exporter collects SDK usage metrics from LaunchDarkly's MAU (Monthly Active Users) API and exposes them as Prometheus metrics.

## Features

## Features

- 📊 Collects **stream usage metrics by SDK version** from LaunchDarkly
- 🔄 Tracks both **client and server SDK** usage with actual connection counts
- 📈 Exposes metrics in **Prometheus format** for monitoring and alerting
- 🐳 **Docker support** with health checks and multi-container setup
- 🚀 **Flask-based web server** with /metrics, /health, and / endpoints
- 🔐 Secure API authentication with beta API version support
- ⚙️ Configurable scrape intervals and time ranges
- 📉 No default Python metrics (clean metrics output)

## How It Works

The exporter uses LaunchDarkly's **Stream usage by SDK version API** to collect real-time connection data:

1. **Fetches stream usage data** for both client and server SDKs
2. **Extracts SDK name, version, and connection counts** from the time-series data
3. **Calculates maximum connections** for each SDK/version combination
4. **Exposes metrics** via Prometheus-compatible endpoint
5. **Updates metrics** on a configurable interval (default: 5 minutes)

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

The exporter provides the following Prometheus metrics (only custom metrics, no default internal metrics):

- `launchdarkly_sdk_clients_total` - Maximum streaming connections by SDK type and version
  - Labels: `sdk_name`, `sdk_type`, `version`
  - Value: Peak number of concurrent connections in the time period
- `launchdarkly_mau_total` - Total Monthly Active Users across all SDKs
  - Labels: `time_period`
- `launchdarkly_exporter_api_requests_total` - Total API requests made to LaunchDarkly
  - Labels: `endpoint`, `status`
- `launchdarkly_exporter_last_scrape_timestamp_seconds` - Unix timestamp of the last successful scrape
- `launchdarkly_exporter_info` - Information about the exporter (version, base URL)

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
count by (sdk_name, version) (launchdarkly_sdk_clients_total)
```

### Client vs Server SDK Usage
```promql
sum by (sdk_type) (launchdarkly_sdk_clients_total)
```

### Top 10 Most Used SDKs
```promql
topk(10, sum by (sdk_name) (launchdarkly_sdk_clients_total))
```

### MAU Trends
```promql
launchdarkly_mau_total{time_period="30d"}
```

### Exporter Health
```promql
time() - launchdarkly_exporter_last_scrape_timestamp_seconds < 600
```

## Grafana Dashboard

Create visualizations in Grafana using the exported metrics:

1. **SDK Version Heatmap**: Show SDK versions over time
2. **MAU Trends**: Line chart of monthly active users
3. **SDK Type Distribution**: Pie chart of client vs server SDKs
4. **API Health**: Status of LaunchDarkly API calls
5. **Top SDKs**: Bar chart of most popular SDK versions

## API Limitations

**Important Notes:**

- The Stream usage by SDK version API provides actual connection counts
- Metrics show the maximum concurrent connections for each SDK/version
- Data granularity depends on age: minutely (< 2 hours), hourly (< 2 days), daily (older)
- The API is in beta and subject to changes
- Rate limiting may apply to API requests
- Default time range is last 7 days for optimal data coverage

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