# ModelMirror

A Python library for automatic configuration management using JSON files. It lets you describe object instances and their dependencies in JSON, then automatically creates and connects those objects for you.

## Key Features

- **Non-Intrusive**: Works with existing classes without modification
- **Simple Registration**: Just create a registry entry linking schema to class
- **JSON Configuration**: Human-readable configuration files
- **Automatic Dependency Injection**: Reference instances with `$name` syntax and types with `$name$` syntax
- **Singleton Management**: Reuse instances across your configuration
- **Type Safety**: Pydantic integration for type checking and validation
- **Dependency Resolution**: Automatic topological sorting of dependencies
- **Thread-Safe**: Automatic per-thread/task Mirror instances with isolated caches
- **Circular Dependency Detection**: Optional detection of circular type dependencies
- **Secret Management**: Automatic resolution of uppercase strings to secret values from files

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

**Note**: Use `$name` for instance references and `$name$` for type references.

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
from typing import Type
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

### Example 1b: Type Reference Configuration

```python
# Example using type references
class ServiceFactory:
    def __init__(self, name: str, service_type: Type[EmailService]):
        self.name = name
        self.service_type = service_type

    def create_service(self, **kwargs):
        return self.service_type(**kwargs)

class ServiceFactoryRegister(ClassRegister):
    reference = ClassReference(id="service_factory", cls=ServiceFactory)

class FactoryConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    factory: ServiceFactory

# Configuration with type reference
config_data = {
    "factory": {
        "$mirror": "service_factory",
        "name": "EmailFactory",
        "service_type": "$email_service$"  # Type reference with $ suffix
    }
}

mirror = Mirror('__main__')
config = mirror.reflect('factory_config.json', FactoryConfig)

# Create instances dynamically
email_service = config.factory.create_service(
    smtp_host="smtp.gmail.com", port=587, username="app@example.com"
)
print(email_service.send_email("user@example.com", "Hello!"))
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

### Example 6: Secret Management

```python
from modelmirror.mirror import Mirror
from modelmirror.parser.default_secret_parser import DefaultSecretParser
from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference
from pydantic import BaseModel, ConfigDict
import json
import tempfile
from pathlib import Path

# Service that uses secrets
class DatabaseService:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def connect(self):
        return f"Connected to {self.host}:{self.port} as {self.username}"

class ApiService:
    def __init__(self, name: str, database: DatabaseService, api_key: str):
        self.name = name
        self.database = database
        self.api_key = api_key

    def authenticate(self):
        return f"API {self.name} authenticated with key: {self.api_key[:8]}..."

# Register services
class DatabaseServiceRegister(ClassRegister):
    reference = ClassReference(id="database", cls=DatabaseService)

class ApiServiceRegister(ClassRegister):
    reference = ClassReference(id="api_service", cls=ApiService)

# Schema
class SecureConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    database: DatabaseService
    api_service: ApiService

# Create secrets directory and files
secrets_dir = Path(tempfile.mkdtemp()) / "secrets"
secrets_dir.mkdir()

# Create secret files (uppercase names are automatically detected)
(secrets_dir / "DB_PASSWORD").write_text("super_secret_db_password")
(secrets_dir / "API_KEY").write_text("sk-1234567890abcdef")
(secrets_dir / "DB_USERNAME").write_text("admin")

# Configuration with secrets (uppercase strings are resolved automatically)
config_data = {
    "database": {
        "$mirror": "database:main_db",
        "host": "localhost",
        "port": 5432,
        "username": "DB_USERNAME",  # Resolved to "admin"
        "password": "DB_PASSWORD"   # Resolved to "super_secret_db_password"
    },
    "api_service": {
        "$mirror": "api_service",
        "name": "UserAPI",
        "database": "$main_db",
        "api_key": "API_KEY"        # Resolved to "sk-1234567890abcdef"
    }
}

with open('secure_config.json', 'w') as f:
    json.dump(config_data, f, indent=2)

# Create custom secret parser pointing to secrets directory
secret_parser = DefaultSecretParser(str(secrets_dir))
mirror = Mirror('__main__', secret_parser=secret_parser)

# Load configuration - secrets are automatically resolved
config = mirror.reflect('secure_config.json', SecureConfig)

print("🔐 Secrets resolved automatically:")
print(config.database.connect())
print(config.api_service.authenticate())
print(f"Database password: {config.database.password}")
print(f"API key: {config.api_service.api_key}")

# Cleanup
import shutil
shutil.rmtree(secrets_dir.parent)
```

**Output:**
```
🔐 Secrets resolved automatically:
Connected to localhost:5432 as admin
API UserAPI authenticated with key: sk-12345...
Database password: super_secret_db_password
API key: sk-1234567890abcdef
```

**Secret Management Features:**
- **Automatic Detection**: Only `UPPERCASE` strings are treated as secrets
- **File-Based**: Secrets are read from individual files in a directory
- **Secure**: Secrets are resolved at runtime, not stored in configuration files
- **Flexible**: Works with nested objects, arrays, and `$mirror` parameters
- **Configurable**: Custom secret parsers can implement different resolution strategies

**Secret Directory Structure:**
```
secrets/
├── DB_PASSWORD      # Contains: super_secret_db_password
├── API_KEY          # Contains: sk-1234567890abcdef
└── DB_USERNAME      # Contains: admin
```

## Technical Details

### Mirror Instance Management

Mirror instances are automatically managed per thread/task context:

```python
# Same parameters in same thread = same instance
mirror1 = Mirror('myapp')
mirror2 = Mirror('myapp')
assert mirror1 is mirror2  # True - same singleton

# Different parameters = different instances
mirror3 = Mirror('myapp', check_circular_types=False)
assert mirror1 is not mirror3  # True - different instance

# Different threads automatically get separate instances
import threading

def worker():
    mirror = Mirror('myapp')  # Separate instance per thread
    return id(mirror)

thread1 = threading.Thread(target=worker)
thread2 = threading.Thread(target=worker)
# Each thread gets its own Mirror instance
```

### Instance-Level Caching

Each Mirror instance has its own isolated cache:

```python
mirror = Mirror('myapp')

# First call - processes configuration
config1 = mirror.reflect('config.json', AppConfig)

# Second call - returns cached result from this instance
config2 = mirror.reflect('config.json', AppConfig)
assert config1 is config2  # True - same object from cache

# Different Mirror instance has separate cache
mirror2 = Mirror('myapp', check_circular_types=False)
config3 = mirror2.reflect('config.json', AppConfig)
assert config1 is not config3  # True - different cache

# Force fresh processing (bypass cache)
config4 = mirror.reflect('config.json', AppConfig, cached=False)
assert config1 is not config4  # True - bypassed cache
```

### Type References

Reference class types (not instances) using `$class_name$` syntax:

```python
# Configuration with type references
config_data = {
    "factory": {
        "$mirror": "service_factory",
        "name": "MyFactory",
        "creates_type": "$user_service$"  # Type reference
    },
    "user_instance": {
        "$mirror": "user_service",
        "name": "John"
    }
}

# The factory gets the UserService class, not an instance
config = mirror.reflect('config.json', AppConfig)
user_class = config.factory.creates_type  # This is the UserService class
user_instance = user_class(name="Jane")   # Create new instance
```

### Circular Dependency Detection

Optional detection of circular type dependencies:

```python
# Enable circular dependency detection (default: True)
mirror = Mirror('myapp', check_circular_types=True)

# This will raise ValueError if circular type dependencies exist
try:
    config = mirror.reflect('config.json', AppConfig)
except ValueError as e:
    print(f"Circular dependency detected: {e}")

# Disable detection to allow circular type references
mirror_permissive = Mirror('myapp', check_circular_types=False)
config = mirror_permissive.reflect('config.json', AppConfig)  # Works
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
from modelmirror.parser.code_link_parser import CodeLinkParser, ParsedKey, FormatValidation

class VersionedCodeLinkParser(CodeLinkParser):
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
custom_parser = VersionedCodeLinkParser()
mirror = Mirror('myapp', parser=custom_parser)
```

### Custom Placeholders

Change the placeholder field from `$mirror` to anything you prefer:

```python
from modelmirror.parser.default_code_link_parser import DefaultCodeLinkParser
from modelmirror.parser.default_model_link_parser import DefaultModelLinkParser

# Use $ref instead of $mirror
custom_code_parser = DefaultCodeLinkParser(placeholder='$ref')
# Use @type@ instead of $type$ for type references
custom_model_parser = DefaultModelLinkParser(type_suffix='@')
mirror = Mirror('myapp', code_link_parser=custom_code_parser, model_link_parser=custom_model_parser)
```

**JSON with custom placeholders:**
```json
{
    "my_service": {
        "$ref": "service:shared",
        "name": "Custom Placeholder Example",
        "service_type": "@other_service@"
    }
}
```

### Thread and Async Safety

Mirror instances are automatically isolated per thread and async task:

```python
import threading
import asyncio
from modelmirror.mirror import Mirror

def worker_thread():
    # Each thread gets its own Mirror instance and cache
    mirror = Mirror('myapp')
    config = mirror.reflect('config.json', AppConfig)
    return id(mirror), id(config)

async def worker_task():
    # Each async task gets its own Mirror instance and cache
    mirror = Mirror('myapp')
    config = mirror.reflect('config.json', AppConfig)
    return id(mirror), id(config)

# Different threads get different Mirror instances
thread1 = threading.Thread(target=worker_thread)
thread2 = threading.Thread(target=worker_thread)

# Different async tasks get different Mirror instances
async def main():
    task1 = asyncio.create_task(worker_task())
    task2 = asyncio.create_task(worker_task())
    results = await asyncio.gather(task1, task2)
    # Each task has different Mirror and config instances
```

### Secret Management

ModelMirror provides built-in secret management for secure configuration:

```python
from modelmirror.parser.default_secret_parser import DefaultSecretParser
from modelmirror.mirror import Mirror

# Default secret parser reads from /run/secrets (Docker secrets)
mirror = Mirror('myapp')  # Uses DefaultSecretParser("/run/secrets")

# Custom secrets directory
secret_parser = DefaultSecretParser("/path/to/secrets")
mirror = Mirror('myapp', secret_parser=secret_parser)

# Configuration with secrets
config_data = {
    "database": {
        "$mirror": "database",
        "host": "localhost",
        "password": "DB_PASSWORD",  # Uppercase = secret
        "username": "db_user"       # Lowercase = literal value
    }
}
```

**Secret Resolution Rules:**
- Only `UPPERCASE` strings are treated as secrets
- Secrets are read from individual files in the secrets directory
- File name matches the secret name (e.g., `DB_PASSWORD` file contains the password)
- Works in nested objects, arrays, and `$mirror` parameters
- Non-uppercase strings are used as literal values

**Custom Secret Parser:**
```python
from modelmirror.parser.secret_parser import SecretParser
from modelmirror.parser.miirror_secret import MirrorSecret

class EnvironmentSecretParser(SecretParser):
    """Resolve secrets from environment variables."""

    def parse(self, name: str) -> MirrorSecret | None:
        if name.startswith("ENV_"):
            import os
            value = os.getenv(name)
            if value:
                return MirrorSecret(value)
        return None

# Use custom parser
custom_parser = EnvironmentSecretParser()
mirror = Mirror('myapp', secret_parser=custom_parser)
```

### Environment Variables

ModelMirror resolves `ENV_`-prefixed strings to environment values through the
`env_parser` slot. Two implementations are provided; the prefix is stripped to form
the lookup name (`"ENV_DB_URL"` looks up `DB_URL`):

- `DefaultEnvParser` (the default) reads from `os.environ`, i.e. `os.getenv("DB_URL")`.
- `FileEnvParser` reads from mounted files — e.g. Docker Swarm `configs`, which expose
  each value as a file rather than an environment variable. `"ENV_DB_URL"` resolves to
  the contents of `<envs_dir>/DB_URL` (default directory `/run/envs`).

```python
from modelmirror.mirror import Mirror
from modelmirror.parser.default_env_parser import DefaultEnvParser
from modelmirror.parser.file_env_parser import FileEnvParser

# Default: read ENV_ values from os.environ
mirror = Mirror('myapp')  # uses DefaultEnvParser()

# Docker Swarm: read ENV_ values from files mounted under /run/envs
mirror = Mirror('myapp', env_parser=FileEnvParser('/run/envs'))

# Configuration with environment references
config_data = {
    "database_url": "ENV_DB_URL",   # ENV_ prefix = environment value
    "service_name": "my-service"    # no prefix = literal value
}
```

**Environment Resolution Rules:**
- Only strings prefixed with `ENV_` are treated as environment references.
- A missing variable / file raises `ValueError` (unlike secrets, which fall through to
  the literal string).
- A present-but-empty value resolves to an empty string.
- `DefaultEnvParser` and `FileEnvParser` both implement `EnvParser` and occupy the same
  `env_parser` slot — pick one per `Mirror` (in a Swarm deployment you read files
  *instead of* os variables).

### Validation Is Delegated to Your Objects

Secrets and environment values do **not** have any dedicated Pydantic validation logic
of their own. ModelMirror resolves them to plain strings and substitutes them into the
configuration as-is; all validation, type coercion, and rules are delegated to the
Pydantic models / objects that consume them. For example, `"ENV_PORT"` is substituted as
a string and then validated and coerced by the consuming field's type:

```python
class ServerConfig(BaseModel):
    port: int          # "ENV_PORT" -> "8080" (string) -> validated/coerced to int 8080
    api_key: str       # "API_KEY"  -> secret string, validated as str by this field
```

This keeps the parsers single-purpose (locate and read a value) and lets your existing
schemas own correctness.

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
