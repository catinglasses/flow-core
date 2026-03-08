# Flow-core: a generic workflow automation engine written in Python.

## About the project

Pet-project focused on orchestrating workflows via python. Potential use cases: scenario automatization (for SOAR, SGRC systems, CRON-like routines).

## Project Structure

### Directory Tree
    flow-core/
    ├── src/
    │   ├── domain/                             # Core: business logic, bl entities, interfaces (ports)
    │   │   ├── interfaces/
    │   │   │   ├── action.py                   # Action (ABC)
    │   │   │   ├── rule.py                     # Rule (ABC)
    │   │   │   └── ...
    │   │   ├── entities/                       # Business objects with identity, not database models
    │   │   │   └── workflow_event.py           # WorkflowEvent (dataclass / Pydantic)
    │   │   └── engine.py                       # WorkflowEngine (relies on interfaces)
    │   │
    │   ├── application/                        # Use cases
    │   │   ├── workflows/
    │   │   │   └── process_event.py            # ProcessEventUseCase
    │   │   └── interfaces/                     # Use Case interfaces
    │   │
    │   ├── presentation/                       # Data serialization for outer world
    │   │   ├── cli/                            # For CLI
    │   │   │   ├── commands/
    │   │   │   │   └── run_workflow.py         # CLI command (call use case via presenter)
    │   │   │   └── presenters/
    │   │   │       └── workflow_presenter.py   # Format output for CLI
    │   │   ├── web/                            # Web-interface
    │   │   │   ├── controllers/
    │   │   │   │   └── workflow_controller.py
    │   │   │   ├── serializers/
    │   │   │   │   └── workflow_serializer.py  # Request/Response models
    │   │   │   └── presenters/
    │   │   │       └── workflow_presenter.py   # Format output for HTTP
    │   │   └── dto/                            # Data Transfer Objects (common for all presentation layers)
    │   │       ├── requests/
    │   │       │   └── process_event_request.py
    │   │       └── responses/
    │   │           └── process_event_response.py
    │   │
    │   ├── infrastructure/                     # Interface implementations (outer systems)
    │   │   ├── http/
    │   │   │   ├── base.py                     # BaseHTTPClient (utility)
    │   │   │   └── ...
    │   │   ├── storage/                        # DB repositories
    │   │   ├── messaging/                      # Message brokers
    │   │   └── config/                         # Config (read envs, etc)
    │   │
    │   ├── common/                             # Common utils, do NOT depend on other layers
    │   │   └── ...
    │   │
    │   └── main.py                             # Composition (compose all dependencies)
    └──── tests/

### Layers and their responsibilities
|Layer|Responsibility|Depends on|
|-|-|-|
|`Domain`|<ul><li>Business logic rules</li><li>Entities</li><li>Interfaces (ports)</li></ul>|Nothing external<br>(only pydantic models are allowed)|
|`Application`|<ul><li>Use cases</li><li>Domain-object orchestration</li><li>No business logic</li></ul>|Domain|
|`Presentation`|<ul><li>Outer world communication (CLI, web)</li><li>DTO <-> use case objects serialization</li><li>Use case invocations</li></ul>|Application, DTOs|
|`Infrastructure`|<ul><li>Interface implementations (HTTP-clients, DB, brokers)</li><li>Configuration</li></ul>|Domain, Application (sometimes)|
|`Composition` (`main.py`)|<ul><li>All objects composition</li><li>Dependency Injection</li><li>Runtime</li></ul>|All layers as it's an entry point of the project|

### Schematic flow description
    [Outer world]
    |
    [CLI command / Web route] --> [Request DTO] --> [Presentation.presenter]
    |
    [Application] --> [Use case]
    |
    [Domain] --> [Engine] --> [Interfaces] --> [Infrastructure (interface implementations)]
    |
    [Result] --> [Presentation.presenter] --> [Response DTO] --> [CLI / web interface]
    |
    [Outer world]


### Architectural reasoning
- **Complete layer isolation**: `infrastructure` changes (such as HTTP-library swap, etc) should NOT impact `domain` and `application` layers
- **Ease of testing**: use cases should be testable via mock-implementations of interfaces
- **Adaptability**: new interfaces should be added with ease - just add a new presenter & a controller, no need to change core implementation
- **Clean code** and clear separation of concerns