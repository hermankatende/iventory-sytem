# Module Dependencies

## Dependency Rule
- Dependencies always point inward to domain and abstractions.

## Allowed Dependencies
- presentation -> application
- application -> domain
- application -> interfaces
- infrastructure -> application interfaces and domain contracts
- persistence models -> django ORM

## Forbidden Dependencies
- domain -> django/rest/framework imports
- application -> django ORM direct imports
- presentation -> persistence direct imports except composition root wiring

## Runtime Flow
1. Presentation accepts request.
2. Service class executes use case.
3. Repository interface called.
4. Infrastructure repository interacts with ORM/MySQL.
5. Domain event triggers audit and notification side effects.
