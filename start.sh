#!/bin/sh
set -e

echo "Starting HWDC 2025 MCP League on Cloud Run..."

# Wait for services to be ready
echo "Starting supervisor to manage all services..."
exec supervisord -c /etc/supervisord.conf
