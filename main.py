#!/usr/bin/env python3
"""
LaunchDarkly SDK Usage Prometheus Exporter

This exporter fetches SDK usage data from LaunchDarkly's MAU API
and exposes it as Prometheus metrics.
"""

import os
import time
import logging
import requests
import threading
from typing import Dict, List, Optional
from flask import Flask, Response
from prometheus_client import Gauge, Counter, Info, CONTENT_TYPE_LATEST, generate_latest
from prometheus_client.core import CollectorRegistry

from datetime import datetime, timedelta, timezone



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable Flask's default logging for cleaner output
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

class LaunchDarklySDKExporter:
    """
    Prometheus exporter for LaunchDarkly SDK usage metrics
    """

    def __init__(self, api_key: str, base_url: str = "https://app.launchdarkly.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': api_key,
            'Content-Type': 'application/json',
            'LD-API-Version': 'beta'  # Use beta API version
        })

        # Create a custom registry to disable default metrics
        self.registry = CollectorRegistry(auto_describe=False)

        # Prometheus metrics (using custom registry)
        # SDK's by version lang and version
        self.sdk_clients_gauge = Gauge(
            'launchdarkly_sdk_clients_by_type_and_version',
            'Total number of SDK clients by type and version',
            ['sdk_name', 'version', 'timestamp'],
            registry=self.registry
        )


        ### Connection count we're billed on, server side connections
        self.service_connection_gauge = Gauge(
            'launchdarkly_service_connection_count',
            'Total Service Connections count',
            ['timestamp'],
            registry=self.registry
        )

        self.service_client_side_connection_gauge = Gauge(
            'launchdarkly_client_side_connection_count',
            'Total Client side connection counts',
            ['timestamp'],
            registry=self.registry
        )
        self.api_requests_total = Counter(
            'launchdarkly_exporter_api_requests_total',
            'Total API requests made to LaunchDarkly',
            ['endpoint', 'status'],
            registry=self.registry
        )

        self.last_scrape_timestamp = Gauge(
            'launchdarkly_exporter_last_scrape_timestamp_seconds',
            'Unix timestamp of the last successful scrape',
            registry=self.registry
        )

        self.exporter_info = Info(
            'launchdarkly_exporter',
            'Information about the LaunchDarkly SDK exporter',
            registry=self.registry
        )

        # Set exporter info
        self.exporter_info.info({
            'version': '1.0.0',
            'base_url': base_url
        })

    def clean_sdk_version(self, version: str) -> str:
        """
        Clean version string to ensure it's a valid Prometheus label value

        Args:
            version: Raw version string

        Returns:
            Cleaned version string
        """
        # Replace invalid characters with underscores
        cleaned = version.split('+')[0]
        # ''.join(c if c.isalnum() or c in '._-' else '_' for c in version)
        # cleaned = cleaned.split('+')[0]
        return cleaned




    def get_timestamps(self) -> tuple:
        """
        Get the timestamps for the last 24 hours

        Returns:
            Tuple of (from_time, to_time)
        """
        # Calculate time range (last 7 days for better data granularity)
        now = datetime.now()
        seven_days_ago = now - timedelta(days=1)
        # one_hour_ago = now - timedelta(hours=6)
        # Format timestamps as ISO 8601 strings
        from_time = seven_days_ago.isoformat() + 'Z'


        today_utc = datetime.now(timezone.utc).date()


        # Calculate yesterday's date
        yesterday_utc = today_utc - timedelta(days=1)

        # Create a datetime object for yesterday at 11:59 PM UTC
        target_time_utc = datetime(
            yesterday_utc.year,
            yesterday_utc.month,
            yesterday_utc.day,
            23,  # 11 PM
            59,  # 59 minutes
            0,   # 0 seconds
            0,   # 0 microseconds
            tzinfo=timezone.utc
            )
        start_time_utc = datetime(
            yesterday_utc.year,
            yesterday_utc.month,
            yesterday_utc.day,
            00,  #  PM
            1,  # 1 minutes
            0,   # 0 seconds
            0,   # 0 microseconds
            tzinfo=timezone.utc
            )
        return start_time_utc, target_time_utc

    def get_stream_usage_by_sdk(self, source: str = 'server',
                                from_time: Optional[str] = None,
                                to_time: Optional[str] = None,
                                # sdk: Optional[str] = None,
                                # version: Optional[str] = None
                              ) -> Dict:
        """
        Fetch stream usage by SDK version from LaunchDarkly API

        Args:
            source: 'client' or 'server' - source of streaming connections
            from_time: ISO 8601 timestamp string (defaults to 24 hours ago)
            to_time: ISO 8601 timestamp string (defaults to current time)
            sdk: Filter by SDK name (optional)
            version: Filter by SDK version (optional)

        Returns:
            Dict containing stream usage data with metadata and series
        """
        url = f"{self.base_url}/api/v2/usage/streams/{source}/bysdkversion"

        params = {}
        if from_time:
            params['from'] = from_time
        if to_time:
            params['to'] = to_time


        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            self.api_requests_total.labels(
                endpoint='stream_usage/bysdkversion',
                status=response.status_code
            ).inc()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch stream usage by SDK: {e}")
            self.api_requests_total.labels(
                endpoint='stream_usage/bysdkversion',
                status='error'
            ).inc()
            raise

    def get_client_connection_count(self,
                                granularity:  Optional[str] = "daily",
                                ) -> Dict:
        """
        Fetch connections from LaunchDarkly API

        Args:
            granularity: Specifies the data granularity. Defaults to `daily`. `monthly` granularity is only supported with the **month_to_date** aggregation type.<br/>Valid values: `daily`, `hourly`, `monthly`.


        Returns:
            Dict containing stream usage data with metadata and series
        """
        url = f"{self.base_url}/api/v2/usage/service-connections"

        params = {}

        if granularity:
            params['granularity'] = granularity

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            self.api_requests_total.labels(
                endpoint='usage/service-connections',
                status=response.status_code
            ).inc()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch service connection count: {e}")
            self.api_requests_total.labels(
                endpoint='usage/service-connections',
                status='error'
            ).inc()
            raise

    def _process_connection_count_usage_data(self, data: Dict, sdk_type: str):
        """
        Process connection count data and update metrics

        Args:
            data: Response from get_client_connection_count
        """

        series = data.get('series', [])


        # Get the most recent data point (last item in series)
        if series:
            # the latest is always empty becuase their api sucks, so I get first item
            latest_datapoint = series[-1]
            connections = latest_datapoint.get('0', 0)
            timestamp = latest_datapoint.get('time', 'unknown')

            self.service_connection_gauge.labels(
                timestamp=timestamp
            ).set(connections)

            logger.info(f"Processed latest connections: {connections} at {timestamp}")

    def _process_stream_usage_data(self, data: Dict, sdk_type: str):
        """
        Process stream usage data and update metrics

        Args:
            data: Response from get_stream_usage_by_sdk
            sdk_type: 'client' or 'server'
        """
        metadata = data.get('metadata', [])
        series = data.get('series', [])

        if not metadata or not series:
            logger.warning(f"No {sdk_type} SDK usage data available")
            return

        # metadata contains info about each series (SDK name/version combinations)
        # series contains time-series data points

        # Extract unique SDK name/version combinations from metadata
        for idx, meta in enumerate(metadata):
            sdk_name = meta.get('sdk', 'unknown')
            version = meta.get('version', 'unknown')
            # Use the index as the series key (metadata index maps to series data keys)
            series_key = str(idx)

            # Get the most recent data point (last item in series)
            if series:
                # the latest is always empty becuase their api sucks, so I get n-2
                latest_datapoint = series[0]

                connections = latest_datapoint.get(series_key, 0)
                timestamp = latest_datapoint.get('time', 'unknown')

                self.sdk_clients_gauge.labels(
                    sdk_name=sdk_name,
                    version=self.clean_sdk_version(version),
                    timestamp=timestamp
                ).set(connections)

                logger.info(f"Processed {sdk_type} SDK: {sdk_name} {version} - Latest connections: {connections} at {timestamp}")

    def collect_metrics(self):
        """
        Collect and update Prometheus metrics from stream usage API
        """
        logger.info("Starting metrics collection")

        try:


            # from_time,to_time = self.get_timestamps()
            # logger.error(f"from_time: {from_time}, to_time: {to_time}")
            # Collect server SDK stream usage
            logger.info("Fetching server SDK stream usage data")
            server_data = self.get_stream_usage_by_sdk(
                source='server',
                # from_time=from_time,
                # to_time=to_time
            )

            # Clear existing metrics
            self.sdk_clients_gauge.clear()

            # Process server SDK metadata and series
            self._process_stream_usage_data(server_data, 'server')

            # Process client connection count
            connection_count = self.get_client_connection_count()

            # Clear existing metrics
            self.service_connection_gauge.clear()

            # Process connection count data
            self._process_connection_count_usage_data(connection_count, 'server')

            # Update last scrape timestamp
            self.last_scrape_timestamp.set(time.time())

            logger.info("Metrics collection completed successfully")

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            raise

    def run(self, port: int = 8000, scrape_interval: int = 300):
        """
        Start the Prometheus exporter with Flask

        Args:
            port: Port to serve metrics on
            scrape_interval: How often to scrape LaunchDarkly API (seconds)
        """
        logger.info(f"Starting LaunchDarkly SDK exporter on port {port}")
        logger.info(f"Scrape interval: {scrape_interval} seconds")

        # Create Flask app
        app = Flask(__name__)

        @app.route('/metrics')
        def metrics():
            """Metrics endpoint for Prometheus"""
            return Response(generate_latest(self.registry), mimetype=CONTENT_TYPE_LATEST)

        @app.route('/health')
        def health():
            """Health check endpoint"""
            return {'status': 'healthy', 'last_scrape': self.last_scrape_timestamp._value._value}, 200

        @app.route('/')
        def index():
            """Index page with exporter info"""
            return '''
            <html>
                <head><title>LaunchDarkly SDK Exporter</title></head>
                <body>
                    <h1>LaunchDarkly SDK Exporter</h1>
                    <p><a href="/metrics">Metrics</a></p>
                    <p><a href="/health">Health</a></p>
                </body>
            </html>
            '''

        # Start metrics collection in a background thread
        def collect_loop():
            # Initial metrics collection
            try:
                self.collect_metrics()
            except Exception as e:
                logger.error(f"Initial metrics collection failed: {e}")

            # Main loop
            while True:
                try:
                    time.sleep(scrape_interval)
                    self.collect_metrics()
                except Exception as e:
                    logger.error(f"Error in metrics collection loop: {e}")
                    time.sleep(60)  # Wait a minute before retrying

        # Start collection thread
        collector_thread = threading.Thread(target=collect_loop, daemon=True)
        collector_thread.start()

        # Start Flask server
        app.run(host='0.0.0.0', port=port, debug=False)


def main():
    """
    Main entry point
    """
    # Get configuration from environment variables
    api_key = os.getenv('LAUNCHDARKLY_API_KEY')
    if not api_key:
        logger.error("LAUNCHDARKLY_API_KEY environment variable is required")
        return 1

    base_url = os.getenv('LAUNCHDARKLY_BASE_URL', 'https://app.launchdarkly.com')
    port = int(os.getenv('EXPORTER_PORT', '8000'))
    scrape_interval = int(os.getenv('SCRAPE_INTERVAL', '300'))

    # Create and run exporter
    exporter = LaunchDarklySDKExporter(api_key, base_url)

    try:
        exporter.run(port=port, scrape_interval=scrape_interval)
        return 0
    except Exception as e:
        logger.error(f"Exporter failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())