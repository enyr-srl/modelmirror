# ModelMirror

A Python library for automatic configuration management using JSON files. It lets you describe object instances and their dependencies in JSON, then automatically creates and connects those objects for you.

## Key Features

- **Non-Intrusive**: Works with existing classes without modification
- **Simple Registration**: Just create a registry entry linking schema to class
- **JSON Configuration**: Human-readable configuration files
- **Automatic Dependency Injection**: Reference instances with `$name` syntax
- **Singleton Management**: Reuse instances across your configuration
- **Type Safety**: Pydantic integration for type checking and validation
- **Dependency Resolution**: Automatic topological sorting of dependencies

## Quick Start - Complete Working Example

Here's a complete example you can copy and run:

### Step 1: Define Your Classes

```python
# app/services.py
class DatabaseService:
    def __init__(self, host: str, port: int, database_name: str):
        self.host = host
        self.port = port
        self.database_name = database_name

    def connect(self):
        return f"Connected to {self.database_name} at {self.host}:{self.port}"

class UserService:
    def __init__(self, database: DatabaseService, cache_enabled: bool):
        self.database = database
        self.cache_enabled = cache_enabled

    def get_user(self, user_id: int):
        connection = self.database.connect()
        return f"User {user_id} from {connection} (cache: {self.cache_enabled})"
```

### Step 2: Register Your Classes

```python
# app/registers.py
from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference
from .services import DatabaseService, UserService

class DatabaseServiceRegister(ClassRegister):
    reference = ClassReference(id="database", cls=DatabaseService)

class UserServiceRegister(ClassRegister):
    reference = ClassReference(id="user_service", cls=UserService)
```

### Step 3: Create Pydantic Schema

```python
# app/config.py
from pydantic import BaseModel, ConfigDict
from .services import DatabaseService, UserService

class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    database: DatabaseService
    user_service: UserService
```

### Step 4: Create JSON Configuration

```json
{
    "database": {
        "$mirror": "database:main_db",
        "host": "localhost",
        "port": 5432,
        "database_name": "myapp"
    },
    "user_service": {
        "$mirror": "user_service",
        "database": "$main_db",
        "cache_enabled": true
    }
}
```

### Step 5: Load and Use

```python
# app/main.py
from modelmirror.mirror import Mirror
from .config import AppConfig

# Load configuration
mirror = Mirror('app')
config = mirror.reflect('config.json', AppConfig)

# Use your configured services
print(config.user_service.get_user(123))
# Output: User 123 from Connected to myapp at localhost:5432 (cache: True)
```

## Runnable Examples

### Example 1: Basic Service Configuration

```python
# Complete runnable example
from modelmirror.mirror import Mirror
from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference
from pydantic import BaseModel, ConfigDict
import json

# 1. Define your service
class EmailService:
    def __init__(self, smtp_host: str, port: int, username: str):
        self.smtp_host = smtp_host
        self.port = port
        self.username = username

    def send_email(self, to: str, subject: str):
        return f"Sending '{subject}' to {to} via {self.smtp_host}:{self.port}"

# 2. Register the service
class EmailServiceRegister(ClassRegister):
    reference = ClassReference(id="email_service", cls=EmailService)

# 3. Create schema
class EmailConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    email_service: EmailService

# 4. Create configuration
config_data = {
    "email_service": {
        "$mirror": "email_service",
        "smtp_host": "smtp.gmail.com",
        "port": 587,
        "username": "myapp@gmail.com"
    }
}

# Save config to file
with open('email_config.json', 'w') as f:
    json.dump(config_data, f, indent=2)

# 5. Load and use
mirror = Mirror('__main__')  # Use current module
config = mirror.reflect('email_config.json', EmailConfig)
print(config.email_service.send_email("user@example.com", "Welcome!"))
```

### Example 2: Dependency Injection with Singletons

```python
from modelmirror.mirror import Mirror
from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference
from pydantic import BaseModel, ConfigDict
import json

# Services with dependencies
class Logger:
    def __init__(self, level: str, output: str):
        self.level = level
        self.output = output

    def log(self, message: str):
        return f"[{self.level}] {message} -> {self.output}"

class DatabaseService:
    def __init__(self, host: str, logger: Logger):
        self.host = host
        self.logger = logger

    def query(self, sql: str):
        self.logger.log(f"Executing: {sql}")
        return f"Results from {self.host}"

class ApiService:
    def __init__(self, name: str, database: DatabaseService, logger: Logger):
        self.name = name
        self.database = database
        self.logger = logger

    def handle_request(self, endpoint: str):
        self.logger.log(f"Handling {endpoint}")
        return self.database.query(f"SELECT * FROM {endpoint}")

# Register services
class LoggerRegister(ClassRegister):
    reference = ClassReference(id="logger", cls=Logger)

class DatabaseRegister(ClassRegister):
    reference = ClassReference(id="database", cls=DatabaseService)

class ApiRegister(ClassRegister):
    reference = ClassReference(id="api", cls=ApiService)

# Schema
class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    logger: Logger
    database: DatabaseService
    api_service: ApiService

# Configuration with shared logger singleton
config_data = {
    "logger": {
        "$mirror": "logger:shared_logger",
        "level": "INFO",
        "output": "console"
    },
    "database": {
        "$mirror": "database",
        "host": "db.example.com",
        "logger": "$shared_logger"
    },
    "api_service": {
        "$mirror": "api",
        "name": "UserAPI",
        "database": "$database",
        "logger": "$shared_logger"
    }
}

with open('app_config.json', 'w') as f:
    json.dump(config_data, f, indent=2)

mirror = Mirror('__main__')
config = mirror.reflect('app_config.json', AppConfig)

# Both services share the same logger instance
print(config.api_service.handle_request("users"))
print(f"Same logger instance: {config.database.logger is config.api_service.logger}")
```

### Example 3: Collections and Complex Structures

```python
from modelmirror.mirror import Mirror
from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference
from pydantic import BaseModel, ConfigDict
from typing import List, Dict
import json

# Microservice classes
class ServiceConfig:
    def __init__(self, name: str, port: int, health_check_path: str):
        self.name = name
        self.port = port
        self.health_check_path = health_check_path

class LoadBalancer:
    def __init__(self, services: List[ServiceConfig], algorithm: str):
        self.services = services
        self.algorithm = algorithm

    def route_request(self):
        return f"Routing via {self.algorithm} to {len(self.services)} services"

# Registers
class ServiceConfigRegister(ClassRegister):
    reference = ClassReference(id="service_config", cls=ServiceConfig)

class LoadBalancerRegister(ClassRegister):
    reference = ClassReference(id="load_balancer", cls=LoadBalancer)

# Schema
class MicroservicesConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    services: List[ServiceConfig]
    load_balancer: LoadBalancer

# Configuration with arrays
config_data = {
    "services": [
        {
            "$mirror": "service_config",
            "name": "auth-service",
            "port": 8001,
            "health_check_path": "/health"
        },
        {
            "$mirror": "service_config",
            "name": "user-service",
            "port": 8002,
            "health_check_path": "/health"
        },
        {
            "$mirror": "service_config",
            "name": "order-service",
            "port": 8003,
            "health_check_path": "/status"
        }
    ],
    "load_balancer": {
        "$mirror": "load_balancer",
        "services": "$services",
        "algorithm": "round_robin"
    }
}

with open('microservices_config.json', 'w') as f:
    json.dump(config_data, f, indent=2)

mirror = Mirror('__main__')
config = mirror.reflect('microservices_config.json', MicroservicesConfig)

print(f"Configured {len(config.services)} services")
print(config.load_balancer.route_request())
```

### Example 4: Environment-Specific Configuration

```python
from modelmirror.mirror import Mirror
from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference
from pydantic import BaseModel, ConfigDict
import json
import os

class DatabaseConfig:
    def __init__(self, host: str, port: int, ssl_enabled: bool, pool_size: int):
        self.host = host
        self.port = port
        self.ssl_enabled = ssl_enabled
        self.pool_size = pool_size

class CacheConfig:
    def __init__(self, redis_url: str, ttl_seconds: int):
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds

class AppService:
    def __init__(self, database: DatabaseConfig, cache: CacheConfig, debug_mode: bool):
        self.database = database
        self.cache = cache
        self.debug_mode = debug_mode

    def get_info(self):
        return {
            "database": f"{self.database.host}:{self.database.port}",
            "cache_ttl": self.cache.ttl_seconds,
            "debug": self.debug_mode
        }

# Registers
class DatabaseConfigRegister(ClassRegister):
    reference = ClassReference(id="database_config", cls=DatabaseConfig)

class CacheConfigRegister(ClassRegister):
    reference = ClassReference(id="cache_config", cls=CacheConfig)

class AppServiceRegister(ClassRegister):
    reference = ClassReference(id="app_service", cls=AppService)

# Schema
class EnvironmentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database: DatabaseConfig
    cache: CacheConfig
    app: AppService

# Development configuration
dev_config = {
    "database": {
        "$mirror": "database_config:main_db",
        "host": "localhost",
        "port": 5432,
        "ssl_enabled": False,
        "pool_size": 5
    },
    "cache": {
        "$mirror": "cache_config:main_cache",
        "redis_url": "redis://localhost:6379",
        "ttl_seconds": 300
    },
    "app": {
        "$mirror": "app_service",
        "database": "$main_db",
        "cache": "$main_cache",
        "debug_mode": True
    }
}

# Production configuration
prod_config = {
    "database": {
        "$mirror": "database_config:main_db",
        "host": "prod-db.company.com",
        "port": 5432,
        "ssl_enabled": True,
        "pool_size": 20
    },
    "cache": {
        "$mirror": "cache_config:main_cache",
        "redis_url": "redis://prod-cache.company.com:6379",
        "ttl_seconds": 3600
    },
    "app": {
        "$mirror": "app_service",
        "database": "$main_db",
        "cache": "$main_cache",
        "debug_mode": False
    }
}

# Save environment-specific configs
with open('config_dev.json', 'w') as f:
    json.dump(dev_config, f, indent=2)

with open('config_prod.json', 'w') as f:
    json.dump(prod_config, f, indent=2)

# Load based on environment
env = os.getenv('ENV', 'dev')
mirror = Mirror('__main__')
config = mirror.reflect(f'config_{env}.json', EnvironmentConfig)

print(f"Environment: {env}")
print(f"App info: {config.app.get_info()}")
```

### Example 5: Validation and Error Handling

```python
from modelmirror.mirror import Mirror
from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference
from pydantic import BaseModel, ConfigDict, Field, validator
from typing import List
import json

class DatabaseConnection:
    def __init__(self, host: str, port: int, max_connections: int):
        self.host = host
        self.port = port
        self.max_connections = max_connections

class ApiServer:
    def __init__(self, name: str, database: DatabaseConnection, allowed_origins: List[str]):
        self.name = name
        self.database = database
        self.allowed_origins = allowed_origins

# Registers
class DatabaseConnectionRegister(ClassRegister):
    reference = ClassReference(id="database", cls=DatabaseConnection)

class ApiServerRegister(ClassRegister):
    reference = ClassReference(id="api_server", cls=ApiServer)

# Schema with validation
class ValidatedConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')

    database: DatabaseConnection
    api_server: ApiServer

    # Custom validation
    @validator('database')
    def validate_database(cls, v):
        if v.port < 1 or v.port > 65535:
            raise ValueError('Database port must be between 1 and 65535')
        if v.max_connections < 1:
            raise ValueError('Max connections must be at least 1')
        return v

# Valid configuration
valid_config = {
    "database": {
        "$mirror": "database:main_db",
        "host": "localhost",
        "port": 5432,
        "max_connections": 10
    },
    "api_server": {
        "$mirror": "api_server",
        "name": "MyAPI",
        "database": "$main_db",
        "allowed_origins": ["http://localhost:3000", "https://myapp.com"]
    }
}

with open('valid_config.json', 'w') as f:
    json.dump(valid_config, f, indent=2)

mirror = Mirror('__main__')

try:
    config = mirror.reflect('valid_config.json', ValidatedConfig)
    print("✅ Configuration loaded successfully!")
    print(f"API: {config.api_server.name}")
    print(f"Database: {config.database.host}:{config.database.port}")
except Exception as e:
    print(f"❌ Configuration error: {e}")

# Invalid configuration (will fail validation)
invalid_config = {
    "database": {
        "$mirror": "database:main_db",
        "host": "localhost",
        "port": 99999,  # Invalid port
        "max_connections": 10
    },
    "api_server": {
        "$mirror": "api_server",
        "name": "MyAPI",
        "database": "$main_db",
        "allowed_origins": ["http://localhost:3000"]
    }
}

with open('invalid_config.json', 'w') as f:
    json.dump(invalid_config, f, indent=2)

try:
    config = mirror.reflect('invalid_config.json', ValidatedConfig)
    print("Configuration loaded")
except Exception as e:
    print(f"❌ Expected validation error: {e}")
```

## Technical Details

### Mirror Singleton Behavior

Mirror instances are singletons based on their configuration parameters:

```python
# These are the same instance
mirror1 = Mirror('myapp')
mirror2 = Mirror('myapp')
assert mirror1 is mirror2  # True

# Different parameters create different instances
mirror3 = Mirror('myapp', placeholder='$ref')
assert mirror1 is not mirror3  # True
```

### Automatic Caching

By default, Mirror caches all reflections for performance:

```python
mirror = Mirror('myapp')

# First call - processes configuration
config1 = mirror.reflect('config.json', AppConfig)

# Second call - returns cached result instantly
config2 = mirror.reflect('config.json', AppConfig)
assert config1 is config2  # True - same object

# Force fresh processing
config3 = mirror.reflect('config.json', AppConfig, cached=False)
assert config1 is not config3  # True - different object
```

### Reference Resolution

ModelMirror automatically resolves dependencies using topological sorting:

```json
{
    "user_service": {
        "$mirror": "user_service",
        "database": "$main_db",
        "cache": "$redis"
    },
    "database": {
        "$mirror": "database:main_db"
    },
    "cache": {
        "$mirror": "cache:redis"
    }
}
```

**Resolution order**: `database` → `cache` → `user_service`

### Singleton References

Use `:instance_name` to create reusable singletons:

- `"service:name"` creates a singleton named "name"
- `"$name"` references inject the singleton instance
- All references to `"$name"` get the exact same object

## Advanced Configuration

### Custom Reference Parsers

Create custom parsers for specialized reference formats:

```python
from modelmirror.parser.key_parser import KeyParser, ParsedKey, FormatValidation

class VersionedKeyParser(KeyParser):
    """Supports format: service@v1.0:instance_name"""

    def __init__(self, placeholder: str = "$mirror"):
        super().__init__(placeholder)

    def _validate(self, reference: str) -> FormatValidation:
        if '@' not in reference:
            return FormatValidation(False, "Missing version: use format 'id@version' or 'id@version:instance'")
        return FormatValidation(True)

    def _parse(self, reference: str) -> ParsedKey:
        if ':' in reference:
            id_version, instance = reference.split(':', 1)
        else:
            id_version, instance = reference, None

        id_part, version = id_version.split('@', 1)
        return ParsedKey(id=id_part, instance=instance)

# Use custom parser
custom_parser = VersionedKeyParser()
mirror = Mirror('myapp', parser=custom_parser)
```

### Custom Placeholders

Change the placeholder field from `$mirror` to anything you prefer:

```python
from modelmirror.parser.default_key_parser import DefaultKeyParser

# Use $ref instead of $mirror
custom_parser = DefaultKeyParser(placeholder='$ref')
mirror = Mirror('myapp', parser=custom_parser)
```

**JSON with custom placeholder:**
```json
{
    "my_service": {
        "$ref": "service:shared",
        "name": "Custom Placeholder Example"
    }
}
```

### Flexible Instance Retrieval

```python
# Multiple ways to get your instances
instances = mirror.reflect_raw('config.json')

user_service = instances.get(UserService)                    # First instance of type
specific_db = instances.get(DatabaseService, '$primary_db') # By singleton name
all_services = instances.get(list[UserService])             # All instances as list
service_map = instances.get(dict[str, UserService])         # All instances as dict
```

## Installation

```bash
pip install modelmirror
```

## Requirements

- Python >= 3.10
- Pydantic >= 2.0.0

## License

MIT License - see LICENSE file for details.
