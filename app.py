from flask import Flask, render_template_string
import psutil
import docker

app = Flask(__name__)
client = docker.DockerClient(base_url='unix://var/run/docker.sock')

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>System & Docker Metrics</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f4f4f4;
            padding: 50px;
            text-align: center;
        }
        .container {
            background-color: white;
            padding: 30px;
            margin: auto;
            max-width: 700px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            border-radius: 16px;
        }
        h1 {
            color: #333;
            font-size: 32px;
        }
        .metric, .container-box {
            margin: 20px 0;
            font-size: 20px;
        }
        .docker-box {
            background: #f0f8ff;
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥 System & Docker Metrics</h1>
        <div class="metric">CPU Usage: {{ cpu }}%</div>
        <div class="metric">Memory Usage: {{ memory }}%</div>

        <h2 style="margin-top:40px;">🐳 Docker Containers</h2>
        {% if containers %}
            {% for c in containers %}
                <div class="docker-box">
                    <strong>{{ c.name }}</strong><br>
                    CPU: {{ c.cpu }}%<br>
                    Memory: {{ c.mem }} MB
                </div>
            {% endfor %}
        {% else %}
            <p>No running Docker containers found.</p>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return '<h2>Flask App is Running! Go to <a href="/metrics">/metrics</a> to view system and Docker metrics.</h2>'

@app.route('/metrics')
def metrics():
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    containers = []

    for container in client.containers.list():
        stats = container.stats(stream=False)
        try:
            # CPU %
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = round((cpu_delta / system_delta) * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"]) * 100.0, 2) if system_delta > 0 else 0.0

            # Memory MB
            mem_usage = round(stats["memory_stats"]["usage"] / (1024 * 1024), 2)
        except:
            cpu_percent = 0.0
            mem_usage = 0.0

        containers.append({
            'name': container.name,
            'cpu': cpu_percent,
            'mem': mem_usage
        })

    return render_template_string(TEMPLATE, cpu=cpu, memory=memory, containers=containers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
