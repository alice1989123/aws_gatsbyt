import json
import psycopg2
import os
from datetime import datetime

# 🔁 In-memory cache (persists while Lambda is warm)
metric_catalog_cache = {}
metric_data_cache = {}

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def lambda_handler(event, context):
    params = event.get("queryStringParameters", {}) or {}
    metric_name = params.get("metric")

    if not metric_name:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing metric name'}),
            'headers': {'Access-Control-Allow-Origin': '*'}
        }

    # Check cache for metric_id
    if metric_name in metric_catalog_cache:
        metric_id = metric_catalog_cache[metric_name]
    else:
        try:
            conn = psycopg2.connect(
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                host=os.environ["DB_HOST"],
                port="5432"
            )
            cur = conn.cursor()
            cur.execute("SELECT id FROM onchain_metric_catalog WHERE name = %s", (metric_name,))
            result = cur.fetchone()
            if not result:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': f'Metric \"{metric_name}\" not found'}),
                    'headers': {'Access-Control-Allow-Origin': '*'}
                }
            metric_id = result[0]
            metric_catalog_cache[metric_name] = metric_id
            cur.close()
            conn.close()
        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'DB error: {str(e)}'}),
                'headers': {'Access-Control-Allow-Origin': '*'}
            }

    # Check cache for metric data
    if metric_id in metric_data_cache:
        data = metric_data_cache[metric_id]
    else:
        try:
            conn = psycopg2.connect(
                dbname=os.environ["DB_NAME"],
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                host=os.environ["DB_HOST"],
                port="5432"
            )
            cur = conn.cursor()
            cur.execute("""
                SELECT timestamp, value
                FROM onchain_metrics_1d
                WHERE metric_id = %s
                ORDER BY timestamp ASC;
            """, (metric_id,))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            data = [{"timestamp": row[0], "value": row[1]} for row in rows]
            metric_data_cache[metric_id] = data  # cache result

        except Exception as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'DB error: {str(e)}'}),
                'headers': {'Access-Control-Allow-Origin': '*'}
            }

    return {
        'statusCode': 200,
        'body': json.dumps(data, cls=EnhancedJSONEncoder),
        'headers': {'Access-Control-Allow-Origin': '*'}
    }
