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

# Register DatabaseService with id "database"
class DatabaseServiceRegister(ClassRegister,
    reference=ClassReference(id="database", cls=DatabaseService)):
    pass

# Register UserService with id "user_service"
class UserServiceRegister(ClassRegister,
    reference=ClassReference(id="user_service", cls=UserService)):
    pass
```

### Step 3: Create JSON Configuration

Create a `config.json` file that defines your instances:

```json
{
    "my_database": {
        "$mirror": "database:db_singleton",
        "host": "localhost",
        "port": 5432
    },
    "my_user_service": {
        "$mirror": "user_service",
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
config = mirror.reflect('config.json', AppConfig)
print(config.my_database.host)  # Full autocomplete!
```

## Tutorial 3: Understanding References - The Heart of ModelMirror

ModelMirror's power comes from its reference system. The `$mirror` field is what transforms JSON objects into live instances.

### How `$mirror` Works

The `$mirror` field uses a simple string format that ModelMirror parses to understand:
1. **Which class to instantiate** (the registered ID)
2. **Whether to create a singleton** (optional instance name)

**Format**: `"class_id"` or `"class_id:instance_name"`

### Basic Reference Structure

Every object you want to mirror needs a `$mirror` field:

```json
{
    "my_service": {
        "$mirror": "service",
        "name": "My Service"
    }
}
```

**What happens:**
1. ModelMirror finds the class registered with ID "service"
2. Creates a new instance: `ServiceClass(name="My Service")`
3. Returns the configured object

### Singleton References - Reuse Instances Anywhere

Add `:instance_name` to create a reusable singleton:

```json
{
    "database": {
        "$mirror": "database:main_db",
        "host": "localhost",
        "port": 5432
    },
    "user_service": {
        "$mirror": "user_service",
        "database": "$main_db"
    },
    "admin_service": {
        "$mirror": "admin_service",
        "database": "$main_db"
    }
}
```

**What happens:**
1. `"database:main_db"` creates a singleton named "main_db"
2. `"$main_db"` references inject the same database instance
3. Both services share the **exact same** database object

### Reference Parser Architecture

ModelMirror uses a pluggable parser system to handle `$mirror` strings:

```python
from modelmirror.parser.reference_parser import ReferenceParser
from modelmirror.parser.default_reference_parser import DefaultReferenceParser

# Default parser handles: "id" and "id:instance"
default_parser = DefaultReferenceParser()

# You can create custom parsers for different formats
class CustomReferenceParser(ReferenceParser):
    def _parse(self, reference: str):
        # Your custom parsing logic
        pass

# Use custom parser
mirror = Mirror('myapp', reference_parser=CustomReferenceParser())
```

**Built-in Parser Features:**
- **Simple format**: `"service"` → creates new instance
- **Singleton format**: `"service:name"` → creates/reuses singleton
- **Validation**: Ensures reference strings are valid
- **Extensible**: Easy to add new reference formats

### Reference Resolution Process

ModelMirror processes references in a specific order:

1. **Parse**: `DefaultReferenceParser` converts `"database:main_db"` to `ParsedReference(id="database", instance="main_db")`
2. **Lookup**: Find the class registered with ID "database"
3. **Dependency Analysis**: Scan for `$singleton_name` references in parameters
4. **Topological Sort**: Order instances to resolve dependencies first
5. **Instantiate**: Create objects with resolved dependencies
6. **Singleton Management**: Store named instances for reuse

### Pydantic Schema for Type Safety

```python
from pydantic import BaseModel, ConfigDict

class ServiceConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    database: DatabaseService
    user_service: UserService
    admin_service: AdminService

config = mirror.reflect('config.json', ServiceConfig)
# Full IDE support and validation!
```

## Tutorial 4: Working with Collections

ModelMirror handles lists and dictionaries seamlessly.

### Lists of Services

```json
{
    "primary_db": {
        "$mirror": "database:primary",
        "host": "primary.db.com",
        "port": 5432
    },
    "services": [
        {
            "$mirror": "service",
            "name": "Service 1",
            "database": "$primary"
        },
        {
            "$mirror": "service",
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

config = mirror.reflect('config.json', MultiServiceConfig)
print(f"Loaded {len(config.services)} services")
```

### Dictionaries of Services

```json
{
    "databases": {
        "primary": {
            "$mirror": "database:primary_db",
            "host": "primary.db.com",
            "port": 5432
        },
        "secondary": {
            "$mirror": "database:secondary_db",
            "host": "secondary.db.com",
            "port": 5432
        }
    },
    "load_balancer": {
        "$mirror": "load_balancer",
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

config = mirror.reflect('config.json', DatabaseClusterConfig)
print(f"Primary DB: {config.databases['primary'].host}")
```

## Tutorial 5: Nested Structures and Complex Dependencies

ModelMirror handles deeply nested configurations effortlessly.

### Multi-Level Dependencies

```json
{
    "cache": {
        "$mirror": "cache:redis_cache",
        "host": "redis.internal",
        "port": 6379
    },
    "database": {
        "$mirror": "database:postgres_db",
        "host": "postgres.internal",
        "port": 5432
    },
    "user_service": {
        "$mirror": "user_service:user_svc",
        "database": "$postgres_db",
        "cache": "$redis_cache"
    },
    "notification_service": {
        "$mirror": "notification_service",
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

config = mirror.reflect('config.json', AppConfig)
# ModelMirror automatically resolves all dependencies in correct order!
```

### Nested Objects and Arrays

```json
{
    "microservices": {
        "auth": {
            "$mirror": "auth_service:auth",
            "jwt_secret": "secret123",
            "token_expiry": 3600
        },
        "api_gateway": {
            "$mirror": "gateway",
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
config = mirror.reflect('config.json', AppConfig)
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
config = mirror.reflect('minimal_config.json', FlexibleConfig)
```

## Advanced: Mirror Customization

### Custom Reference Parsers

Create custom parsers for specialized reference formats:

```python
from modelmirror.parser.reference_parser import ReferenceParser, ParsedReference, FormatValidation

class VersionedReferenceParser(ReferenceParser):
    """Supports format: service@v1.0:instance_name"""

    def _validate(self, reference: str) -> FormatValidation:
        if '@' not in reference:
            return FormatValidation(False, "Missing version: use format 'id@version' or 'id@version:instance'")
        return FormatValidation(True)

    def _parse(self, reference: str) -> ParsedReference:
        if ':' in reference:
            id_version, instance = reference.split(':', 1)
        else:
            id_version, instance = reference, None

        id_part, version = id_version.split('@', 1)
        # You could use version for class selection logic
        return ParsedReference(id=id_part, instance=instance)

# Use your custom parser
mirror = Mirror('myapp', parser=VersionedReferenceParser())
```

### Custom Placeholders

Change the placeholder field from `$mirror` to anything you prefer:

```python
# Use $ref instead of $mirror
mirror = Mirror('myapp', placeholder='$ref')

# Use $create for a more descriptive name
mirror = Mirror('myapp', placeholder='$create')

# Use $service for domain-specific naming
mirror = Mirror('myapp', placeholder='$service')
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

### Combining Custom Parser and Placeholder

```python
class AtSymbolParser(ReferenceParser):
    """Uses @ for instances: service@instance"""

    def _validate(self, reference: str) -> FormatValidation:
        return FormatValidation(True)

    def _parse(self, reference: str) -> ParsedReference:
        if '@' in reference:
            id_part, instance = reference.split('@', 1)
            return ParsedReference(id=id_part, instance=instance)
        return ParsedReference(id=reference, instance=None)

# Combine custom parser with custom placeholder
mirror = Mirror(
    'myapp',
    parser=AtSymbolParser(),
    placeholder='$build'
)
```

**JSON with both customizations:**
```json
{
    "database": {
        "$build": "database@shared_db",
        "host": "localhost",
        "port": 5432
    },
    "service": {
        "$build": "service",
        "database": "$shared_db"
    }
}
```

### Mirror Constructor Options

```python
mirror = Mirror(
    package_name='myapp',           # Package to scan for registers
    parser=DefaultReferenceParser(), # Reference parser (default: DefaultReferenceParser)
    placeholder='$mirror'           # JSON field name (default: '$mirror')
)
```

## Pro Tips

### 1. Use Meaningful Singleton Names
```json
{
    "$mirror": "database:user_db"     // Good: descriptive
    "$mirror": "cache:cache_1"       // Good: clear purpose
    "$mirror": "service:x"           // Bad: unclear
}
```

### 2. Reference Format Best Practices
```json
{
    // Simple instance - no reuse needed
    "logger": {
        "$mirror": "logger",
        "level": "INFO"
    },

    // Singleton - will be reused
    "database": {
        "$mirror": "database:main_db",
        "host": "localhost"
    },

    // Reference the singleton
    "user_service": {
        "$mirror": "user_service",
        "database": "$main_db"  // Inject the singleton
    }
}
```

### 3. Understanding Reference Resolution Order

ModelMirror automatically resolves dependencies using topological sorting:

```json
{
    "user_service": {
        "$mirror": "user_service",
        "database": "$main_db",     // Depends on main_db
        "cache": "$redis"           // Depends on redis
    },
    "database": {
        "$mirror": "database:main_db"  // Created first
    },
    "cache": {
        "$mirror": "cache:redis"       // Created second
    }
    // user_service created last (after dependencies)
}
```

**Resolution order**: `database` → `cache` → `user_service`

### 4. Organize Large Configs
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

### 5. Environment-Specific Configs
```python
# Load different configs per environment
env = os.getenv('ENV', 'dev')
config = mirror.reflect(f'config_{env}.json', AppConfig)
```

### 6. Retrieve Instances Flexibly
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
