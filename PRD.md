##command
ketika menambahkan project tambahkan informasi misal didropdown kan ada select framework seperti laravel, nah dibawah formnya tambahkan informasinya bahwa format lognya harus seperti ini tapi tampilkan secara human readable:
```python
self.laravel_pattern = re.compile(
    r'\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s+'
    r'(?P<environment>\w+)\.(?P<level>\w+):\s+'
    r'(?P<message>.*?)(?=\s*\{)'
    r'\s(?P<context>\{.*\})?$',
    re.DOTALL
)

# django_flask log pattern (Django/Flask)
self.django_flask = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}[,.]?\d*)\s+'
    r'(?P<level>\w+)\s+'
    r'(?P<message>.*?)(?:\s+\[(?P<file>.*?):(?P<line>\d+)\])?'
)

# Node.js log pattern
self.nodejs_pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z)\s+'
    r'(?P<level>\w+):\s+'
    r'(?P<message>.*?)(?:\s+at\s+(?P<controller>.*?)\s+\((?P<file>.*?):(?P<line>\d+):\d+\))?'
)

self.python_pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[.,]?\d*)\s*-\s*'
    r'(?P<level>\w+)\s*-\s*'
    r'(?P<message>.+)'
)

# FastAPI log pattern
self.fastapi_pattern = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s*-\s*'
    r'(?P<module>[\w.]+)\s*-\s*'
    r'(?P<level>\w+)\s*-\s*'
    r'(?P<file>\w+\.py):(?P<line>\d+)\s*-\s*'
    r'(?P<message>.+)'
)

```