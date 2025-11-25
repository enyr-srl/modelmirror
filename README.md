# ModelMirror

A Python library for automatic configuration management using JSON files. It lets you describe object instances and their dependencies in JSON, then automatically creates and connects those objects for you.

## Key Features

- **Non-Intrusive**: Works with existing classes without modification
- **Simple Registration**: Just create a registry entry linking schema to class
- **JSON Configuration**: Human-readable configuration files
- **Automatic Dependency Injection**: Reference instances with `$name` syntax
- **Singleton Management**: Reuse instances across your configuration
- **Type Safety**: Optional Pydantic integration for type checking
- **Dependency Resolution**: Automatic topological sorting of dependencies

## Tutorial 1: Quick Start - Your First Working Example

Let's create a simple example with two classes: a `DatabaseService` and a `UserService` that depends on it.

### Step 1: Define Your Classes

```python
# Your existing classes - no modifications required
class DatabaseService:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def connect(self):
        return f"Connected to {self.host}:{self.port}"

class UserService:
    def __init__(self, db: DatabaseService, cache_enabled: bool):
        self.db = db
        self.cache_enabled = cache_enabled

    def get_user(self, user_id: int):
        connection = self.db.connect()
        return f"User {user_id} from {connection} (cache: {self.cache_enabled})"
```

### Step 2: Register Your Classes

Create registry entries that link your classes to schema identifiers:

```python
from modelmirror.class_provider.class_register import ClassRegister
from modelmirror.class_provider.class_reference import ClassReference

# Register DatabaseService with schema "database" and version "1.0.0"
class DatabaseServiceRegister(ClassRegister,
    reference=ClassReference(schema="database", version="1.0.0", cls=DatabaseService)):
    pass

# Register UserService with schema "user_service" and version "1.0.0"
class UserServiceRegister(ClassRegister,
    reference=ClassReference(schema="user_service", version="1.0.0", cls=UserService)):
    pass
```

### Step 3: Create JSON Configuration

Create a `config.json` file that defines your instances:

```json
{
    "my_database": {
        "$reference": {
            "registry": {"schema": "database", "version": "1.0.0"},
            "instance": "db_singleton"
        },
        "host": "localhost",
        "port": 5432
    },
    "my_user_service": {
        "$reference": {
            "registry": {"schema": "user_service", "version": "1.0.0"}
        },
        "db": "$db_singleton",
        "cache_enabled": true
    }
}
```

### Step 4: Load and Use

```python
from modelmirror.mirror import Mirror

# Load configuration
mirror = Mirror('myapp')  # 'myapp' is the package where your registers are defined
instances = mirror.reflect_raw('config.json')

# Get your configured instances
user_service = instances.get(UserService)
print(user_service.get_user(123))  # Output: User 123 from Connected to localhost:5432 (cache: True)
```

**That's it!** Your classes are now configured via JSON with automatic dependency injection.

## Tutorial 2: Type-Safe Configuration with Pydantic

For production applications, add type safety with Pydantic schemas. Just add your schema definition:

```python
from pydantic import BaseModel, ConfigDict

class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    my_database: DatabaseService
    my_user_service: UserService

# Load with full type checking and IDE support
config = mirror.reflect_typed('config.json', AppConfig)
print(config.my_database.host)  # Full autocomplete!
```

## Tutorial 3: Understanding References - The Heart of ModelMirror

ModelMirror's power comes from its reference system. Let's explore how it works with practical examples.

### Basic Reference Structure

Every object in your JSON you want to mirror needs a `$reference` block:

```json
{
    "my_service": {
        "$reference": {
            "registry": {"schema": "service", "version": "1.0.0"}
        },
        "name": "My Service"
    }
}
```

This tells ModelMirror:
1. Create an instance using the class registered with schema "service" v1.0.0
2. Pass `"name": "My Service"` as a constructor parameter

### Singleton References - Reuse Instances Anywhere

Add an `instance` field to create a reusable singleton:

```json
{
    "database": {
        "$reference": {
            "registry": {"schema": "database", "version": "1.0.0"},
            "instance": "main_db"
        },
        "host": "localhost",
        "port": 5432
    },
    "user_service": {
        "$reference": {
            "registry": {"schema": "user_service", "version": "1.0.0"}
        },
        "database": "$main_db"
    },
    "admin_service": {
        "$reference": {
            "registry": {"schema": "admin_service", "version": "1.0.0"}
        },
        "database": "$main_db"
    }
}
```

Both services get the **same** database instance! Use `$main_db` anywhere you need it.

### Pydantic Schema for Type Safety

```python
from pydantic import BaseModel, ConfigDict

class ServiceConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    database: DatabaseService
    user_service: UserService
    admin_service: AdminService

config = mirror.reflect_typed('config.json', ServiceConfig)
# Full IDE support and validation!
```

## Tutorial 4: Working with Collections

ModelMirror handles lists and dictionaries seamlessly.

### Lists of Services

```json
{
    "primary_db": {
        "$reference": {
            "registry": {"schema": "database", "version": "1.0.0"},
            "instance": "primary"
        },
        "host": "primary.db.com",
        "port": 5432
    },
    "services": [
        {
            "$reference": {
                "registry": {"schema": "service", "version": "1.0.0"}
            },
            "name": "Service 1",
            "database": "$primary"
        },
        {
            "$reference": {
                "registry": {"schema": "service", "version": "1.0.0"}
            },
            "name": "Service 2",
            "database": "$primary"
        }
    ]
}
```

### Pydantic Schema for Lists

```python
from typing import List
from pydantic import BaseModel, ConfigDict

class MultiServiceConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    primary_db: DatabaseService
    services: List[UserService]

config = mirror.reflect_typed('config.json', MultiServiceConfig)
print(f"Loaded {len(config.services)} services")
```

### Dictionaries of Services

```json
{
    "databases": {
        "primary": {
            "$reference": {
                "registry": {"schema": "database", "version": "1.0.0"},
                "instance": "primary_db"
            },
            "host": "primary.db.com",
            "port": 5432
        },
        "secondary": {
            "$reference": {
                "registry": {"schema": "database", "version": "1.0.0"},
                "instance": "secondary_db"
            },
            "host": "secondary.db.com",
            "port": 5432
        }
    },
    "load_balancer": {
        "$reference": {
            "registry": {"schema": "load_balancer", "version": "1.0.0"}
        },
        "primary_db": "$primary_db",
        "secondary_db": "$secondary_db"
    }
}
```

### Pydantic Schema for Dictionaries

```python
from typing import Dict
from pydantic import BaseModel, ConfigDict

class DatabaseClusterConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    databases: Dict[str, DatabaseService]
    load_balancer: LoadBalancerService

config = mirror.reflect_typed('config.json', DatabaseClusterConfig)
print(f"Primary DB: {config.databases['primary'].host}")
```

## Tutorial 5: Nested Structures and Complex Dependencies

ModelMirror handles deeply nested configurations effortlessly.

### Multi-Level Dependencies

```json
{
    "cache": {
        "$reference": {
            "registry": {"schema": "cache", "version": "1.0.0"},
            "instance": "redis_cache"
        },
        "host": "redis.internal",
        "port": 6379
    },
    "database": {
        "$reference": {
            "registry": {"schema": "database", "version": "1.0.0"},
            "instance": "postgres_db"
        },
        "host": "postgres.internal",
        "port": 5432
    },
    "user_service": {
        "$reference": {
            "registry": {"schema": "user_service", "version": "1.0.0"},
            "instance": "user_svc"
        },
        "database": "$postgres_db",
        "cache": "$redis_cache"
    },
    "notification_service": {
        "$reference": {
            "registry": {"schema": "notification_service", "version": "1.0.0"}
        },
        "user_service": "$user_svc",
        "templates": {
            "email": "Welcome {{name}}!",
            "sms": "Hi {{name}}, welcome!"
        }
    }
}
```

### Pydantic Schema for Complex Apps

```python
from typing import Dict
from pydantic import BaseModel, ConfigDict

class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    cache: CacheService
    database: DatabaseService
    user_service: UserService
    notification_service: NotificationService

config = mirror.reflect_typed('config.json', AppConfig)
# ModelMirror automatically resolves all dependencies in correct order!
```

### Nested Objects and Arrays

```json
{
    "microservices": {
        "auth": {
            "$reference": {
                "registry": {"schema": "auth_service", "version": "1.0.0"},
                "instance": "auth"
            },
            "jwt_secret": "secret123",
            "token_expiry": 3600
        },
        "api_gateway": {
            "$reference": {
                "registry": {"schema": "gateway", "version": "1.0.0"}
            },
            "auth_service": "$auth",
            "routes": [
                {
                    "path": "/users",
                    "service": "$user_svc",
                    "methods": ["GET", "POST"]
                },
                {
                    "path": "/notifications",
                    "service": "$notification_svc",
                    "methods": ["POST"]
                }
            ]
        }
    }
}
```

## Tutorial 6: Validation and Error Handling

Use Pydantic's powerful validation to catch configuration errors early.

### Strict Validation

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class DatabaseConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')

    host: str = Field(min_length=1, description="Database hostname")
    port: int = Field(ge=1, le=65535, description="Database port")
    max_connections: int = Field(ge=1, le=1000, default=10)
    ssl_enabled: bool = Field(default=True)

class ServiceConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(min_length=1, max_length=50)
    timeout: int = Field(ge=1, le=300, default=30)
    retries: int = Field(ge=0, le=10, default=3)

class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    database: DatabaseService
    services: List[ServiceConfig]
    debug_mode: bool = Field(default=False)

# This will validate all constraints when loading
config = mirror.reflect_typed('config.json', AppConfig)
```

### Optional Fields and Defaults

```python
from typing import Optional
from pydantic import BaseModel, ConfigDict

class FlexibleConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    required_service: DatabaseService
    optional_cache: Optional[CacheService] = None
    debug_enabled: bool = False
    max_retries: int = 3

# JSON can omit optional fields
config = mirror.reflect_typed('minimal_config.json', FlexibleConfig)
```

## Pro Tips

### 1. Use Meaningful Singleton Names
```json
{
    "instance": "user_db"     // Good: descriptive
    "instance": "cache_1"    // Good: clear purpose
    "instance": "x"          // Bad: unclear
}
```

### 2. Organize Large Configs
```python
# Split large configs into logical sections
class DatabaseConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    primary: DatabaseService
    replica: DatabaseService

class ServiceConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    user_service: UserService
    auth_service: AuthService

class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    databases: DatabaseConfig
    services: ServiceConfig
```

### 3. Environment-Specific Configs
```python
# Load different configs per environment
env = os.getenv('ENV', 'dev')
config = mirror.reflect_typed(f'config_{env}.json', AppConfig)
```

### 4. Retrieve Instances Flexibly
```python
# Multiple ways to get your instances
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
