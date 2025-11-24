# ModelMirror

A Python library automatic configuration management using JSON files. ModelMirror allows you to define object instances and their dependencies in JSON configuration files, then automatically instantiate and wire them together.

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

### Step 1: Define Your Classes (No Changes Needed!)

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

## Understanding the Key Concepts

### The `$reference` Object

Every instance in your JSON config needs a `$reference` object with two main parts:

#### 1. `registry` - Links to Your Python Class
```json
"registry": {"schema": "database", "version": "1.0.0"}
```
- **Purpose**: Tells ModelMirror which Python class to instantiate
- **Must match**: The `schema` and `version` in your `ClassReference` registration
- **Required**: Always needed to identify the class

#### 2. `instance` - Creates a Singleton Reference (Optional)
```json
"instance": "db_singleton"
```
- **Purpose**: Creates a named singleton that can be referenced elsewhere
- **Usage**: Reference it with `"$db_singleton"` in other instances
- **Optional**: Only needed if you want to reuse this instance

### Dependency Injection with `$` References

Use `$instance_name` to inject dependencies:

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
        "db": "$main_db",
        "cache_enabled": true
    },
    "admin_service": {
        "$reference": {
            "registry": {"schema": "admin_service", "version": "1.0.0"}
        },
        "db": "$main_db",
        "timeout": 30
    }
}
```

In this example:
- `database` creates a singleton named `main_db`
- Both `user_service` and `admin_service` inject the same `main_db` instance
- ModelMirror automatically resolves dependencies in the correct order

## Tutorial 2: Type-Safe Configuration with Pydantic Schema

For production applications, you want compile-time type checking and IDE support. ModelMirror integrates with Pydantic to provide a type-safe configuration schema.

### Step 1: Define Your Classes (Same as Tutorial 1)

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

### Step 2: Register Your Classes (Same as Tutorial 1)

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

### Step 3: Create JSON Configuration (Same as Tutorial 1)

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

### Step 4: Define Your Pydantic Schema

Create a Pydantic model that describes your configuration structure:

```python
from pydantic import BaseModel, ConfigDict

class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    my_database: DatabaseService
    my_user_service: UserService
```

### Step 5: Load with Type Validation

```python
from modelmirror.mirror import Mirror

# Load configuration with full type checking
mirror = Mirror('myapp')
config = mirror.reflect_typed('config.json', AppConfig)

# Now you have full IDE support and type safety
print(config.my_database.host)  # IDE autocomplete works!
print(config.my_user_service.get_user(456))  # Type-safe method calls
```

**That's it!** Your classes are now configured via JSON with automatic dependency injection AND full type safety.

### Benefits of Using a Schema

- **IDE Support**: Full autocomplete and IntelliSense
- **Type Checking**: Catch configuration errors at load time
- **Documentation**: Schema serves as living documentation
- **Validation**: Pydantic validates all field types automatically
- **Refactoring Safety**: IDE can track usage across your codebase

### Example with Validation

```python
from pydantic import BaseModel, Field
from typing import List

class DatabaseConfig(BaseModel):
    host: str = Field(..., min_length=1)
    port: int = Field(..., ge=1, le=65535)
    max_connections: int = Field(default=10, ge=1)

class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    databases: List[DatabaseService]
    user_service: UserService
    debug_mode: bool = False

# This will validate all constraints when loading
config = mirror.reflect_typed('config.json', AppConfig)
```

## Advanced Usage

### Working with Lists

```json
{
    "services": [
        {
            "$reference": {
                "registry": {"schema": "service", "version": "1.0.0"},
                "instance": "service_1"
            },
            "name": "Primary Service"
        },
        "$service_1",
        {
            "$reference": {
                "registry": {"schema": "service", "version": "1.0.0"}
            },
            "name": "Secondary Service"
        }
    ]
}
```

### Retrieving Instances

```python
# Get single instance by type
user_service = instances.get(UserService)

# Get instance by singleton name
database = instances.get(DatabaseService, '$main_db')

# Get all instances of a type as list
all_services = instances.get(list[ServiceClass])

# Get all instances as dictionary
service_dict = instances.get(dict[str, ServiceClass])
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