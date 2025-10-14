#!/bin/bash

# LaunchDarkly SDK Exporter Setup Script

set -e

echo "🚀 Setting up LaunchDarkly SDK Exporter..."

# Check if API key is provided
if [ -z "$LAUNCHDARKLY_API_KEY" ]; then
    echo "❌ Error: LAUNCHDARKLY_API_KEY environment variable is required"
    echo "   Please set it with: export LAUNCHDARKLY_API_KEY='your-api-key'"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    sed -i.bak "s/your-api-key-here/$LAUNCHDARKLY_API_KEY/" .env
    rm .env.bak
    echo "   ✅ .env file created"
fi

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are running
echo "🔍 Checking service health..."

# Check exporter
if curl -s http://localhost:8000/health > /dev/null; then
    echo "   ✅ LaunchDarkly SDK Exporter is running on http://localhost:8000"
    echo "      Endpoints: / (index), /metrics (prometheus), /health (healthcheck)"
else
    echo "   ❌ LaunchDarkly SDK Exporter is not responding"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/ready > /dev/null; then
    echo "   ✅ Prometheus is running on http://localhost:9090"
else
    echo "   ❌ Prometheus is not responding"
fi

# Check Grafana
if curl -s http://localhost:3000/api/health > /dev/null; then
    echo "   ✅ Grafana is running on http://localhost:3000"
    echo "      Default login: admin/admin"
else
    echo "   ❌ Grafana is not responding"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📊 Access your monitoring stack:"
echo "   - Exporter Index: http://localhost:8000/"
echo "   - Metrics: http://localhost:8000/metrics"
echo "   - Health Check: http://localhost:8000/health"
echo "   - Prometheus: http://localhost:9090"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "📈 Example Prometheus queries:"
echo "   - SDK clients by type: sum by (sdk_type) (launchdarkly_sdk_clients_total)"
echo "   - Top SDKs: topk(10, sum by (sdk_name) (launchdarkly_sdk_clients_total))"
echo ""
echo "🔧 To stop services: docker-compose down"
echo "📜 To view logs: docker-compose logs -f"