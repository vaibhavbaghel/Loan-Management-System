# Microservices Loan Management System

## Overview

This is a refactored microservices architecture of the Loan Management System. The original monolithic Django backend has been split into independent, scalable services:

- **User Service** (Django, port 8001) — handles user authentication, roles, and approvals
- **Loan Service** (Django, port 8002) — handles loan lifecycle (create, list, approve, reject, edit)
- **API Gateway** (FastAPI, port 8000) — unified entry point, routes requests to services
- **PostgreSQL databases** (separate for each service)

## Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│           API Gateway (FastAPI)                 │
│     Port 8000 - Unified Entry Point             │
│  Routes /api/user/* → User Service              │
│  Routes /api/loan/* → Loan Service              │
│  • Auth validation                              │
│  • Rate limiting (TODO)                         │
│  • Request/Response transformation              │
└──────┬──────────────────────────────┬───────────┘
       │                              │
       │                              │
┌──────▼─────────────┐      ┌─────────▼──────────┐
│  User Service      │      │  Loan Service      │
│  Django, port 8001 │      │  Django, port 8002 │
│  • Signup          │      │  • Request Loan    │
│  • Login           │      │  • Approve/Reject  │
│  • Profile         │      │  • Edit Loan       │
│  • Approvals       │      │  • List Loans      │
└──────┬─────────────┘      └─────────┬──────────┘
       │                              │
       │                              │
┌──────▼──────────────┐      ┌────────▼──────────┐
│  postgres-user     │      │ postgres-loan      │
│  (user_service_db) │      │ (loan_service_db)  │
└────────────────────┘      └───────────────────┘

Optional: Event Bus (RabbitMQ)
  - Async inter-service communication
  - Events: user.created, loan.approved, etc.
```

## Key Benefits of Microservices

1. **Independent Scaling** — Scale User Service or Loan Service separately based on load
2. **Technology Flexibility** — Each service can use different tech stacks
3. **Separate Databases** — User and Loan data are isolated; easier to scale/backup independently
4. **Fault Isolation** — If Loan Service fails, User Service continues operating
5. **Independent Deployment** — Deploy changes to one service without affecting others
6. **Team Autonomy** — Teams can work on services independently

## Getting Started

### Prerequisites

- Docker & Docker Compose (version 20.10+)
- Python 3.9+ (if running locally without Docker)

### Setup

1. **Clone and navigate to services directory:**
   ```bash
   cd services
   ```

2. **Copy environment configuration:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to change default values (JWT secrets, DB credentials, etc.)

3. **Build and run all services:**
   ```bash
   docker-compose up --build
   ```

   Expected output:
   ```
   api-gateway         | Application startup complete [Uvicorn]
   user-service       | Started server process
   loan-service       | Started server process
   ```

4. **Verify services are running:**
   - API Gateway: http://localhost:8000
   - User Service: http://localhost:8001
   - Loan Service: http://localhost:8002

5. **Create migrations and superuser:**
   ```bash
   # Create admin user in User Service
   docker-compose exec user-service python manage.py createsuperuser
   ```

## API Endpoints

All endpoints are accessed through the API Gateway at `http://localhost:8000/api`.

### User Service Endpoints

- **POST** `/api/user/signup` — Register a new user
- **POST** `/api/user/login` — Authenticate user (returns JWT)
- **GET** `/api/user/profile` — Get authenticated user's profile
- **POST** `/api/user/create-admin` — Create admin (admin-only)
- **GET** `/api/user/list-agents` — List customers
- **GET** `/api/user/list-users` — List all users (admin-only)
- **GET** `/api/user/list-approvals` — List pending agent approvals (admin-only)
- **PUT** `/api/user/approve-delete/{user_id}` — Approve/delete agent (admin-only)
- **DELETE** `/api/user/approve-delete/{user_id}` — Delete agent

### Loan Service Endpoints

- **POST** `/api/loan/customer-loan` — Agent requests a loan for a customer
- **PUT** `/api/loan/approve-reject-loan/{loan_id}` — Admin approves/rejects loan
- **PUT** `/api/loan/edit-loan/{loan_id}` — Agent edits a loan
- **GET** `/api/loan/list-loans-admin-agent` — List all loans (admin/agent)
  - Query param: `?status=NEW|APPROVED|REJECTED`
- **GET** `/api/loan/list-loans-customer` — List customer's loans
  - Query param: `?status=NEW|APPROVED|REJECTED`

## Authentication

1. **Sign up a user:**
   ```bash
   curl -X POST http://localhost:8000/api/user/signup \
     -H "Content-Type: application/json" \
     -d '{
       "email": "customer@example.com",
       "password": "securepass123",
       "first_name": "John",
       "last_name": "Doe",
       "is_customer": true,
       "is_agent": false
     }'
   ```

2. **Login to get JWT token:**
   ```bash
   curl -X POST http://localhost:8000/api/user/login \
     -H "Content-Type: application/json" \
     -d '{
       "email": "customer@example.com",
       "password": "securepass123"
     }'
   ```
   Response includes `token` field.

3. **Use token in subsequent requests:**
   ```bash
   curl -X GET http://localhost:8000/api/user/profile \
     -H "Authorization: Bearer <your_jwt_token>"
   ```

## Service Communication

### Synchronous (HTTP)
- API Gateway calls User/Loan Services via HTTP
- Loan Service can call User Service for validation (TODO)

### Asynchronous (Event Bus - Optional)
- Services publish events to RabbitMQ/Redis
- Subscribers consume events for eventual consistency
- Examples:
  - User Service publishes `agent.approved` → Loan Service updates limits
  - Loan Service publishes `loan.created` → User Service logs activity

To enable RabbitMQ:
1. Uncomment RabbitMQ service in `docker-compose.yml`
2. Set `EVENT_BUS_TYPE=rabbitmq` in `.env`
3. Rebuild: `docker-compose up --build`
4. Access RabbitMQ management: http://localhost:15672 (admin/admin)

## Database Management

### Migrations

Each service manages its own database migrations:

```bash
# User Service migrations
docker-compose exec user-service python manage.py makemigrations user
docker-compose exec user-service python manage.py migrate

# Loan Service migrations
docker-compose exec loan-service python manage.py makemigrations loan
docker-compose exec loan-service python manage.py migrate
```

### Admin Panels

- User Service: http://localhost:8001/admin
- Loan Service: http://localhost:8002/admin

## Testing

### Run tests in User Service
```bash
docker-compose exec user-service python manage.py test user
```

### Run tests in Loan Service
```bash
docker-compose exec loan-service python manage.py test loan
```

### Run all tests
```bash
docker-compose exec user-service python manage.py test && \
docker-compose exec loan-service python manage.py test
```

## Monitoring and Logs

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f user-service
docker-compose logs -f loan-service
docker-compose logs -f api-gateway
```

### Check service health
```bash
curl http://localhost:8000/health
curl http://localhost:8001/admin
curl http://localhost:8002/admin
```

## Deployment

### Local Development

1. **Start all services:**
   ```bash
   docker-compose up
   ```

2. **Apply migrations on first run:**
   ```bash
   docker-compose exec user-service python manage.py migrate
   docker-compose exec loan-service python manage.py migrate
   ```

### Production

1. **Build images:**
   ```bash
   docker-compose build
   ```

2. **Push to registry (e.g., Docker Hub):**
   ```bash
   docker tag loan-management-system-user-service:latest myregistry/user-service:1.0.0
   docker push myregistry/user-service:1.0.0
   ```

3. **Deploy to orchestration platform (Kubernetes, Swarm):**
   - Services can be deployed independently
   - Use Kubernetes deployment files or Docker Swarm stacks
   - See `k8s/` directory (TODO) for Kubernetes examples

4. **Environment variables:**
   - Set `DEBUG=False` in production
   - Use strong JWT secrets (e.g., generated with `openssl rand -hex 32`)
   - Configure CORS properly for your frontend domain

## Shared Utilities (`services/shared/`)

Located in `services/shared/`:
- `jwt_utils.py` — JWT token creation and validation
- `exceptions.py` — Common exceptions for all services
- `event_schemas.py` — Event definitions for inter-service communication
- `event_bus.py` — In-memory and RabbitMQ event bus implementations

These utilities are used by both services to maintain consistency.

## Development Workflow

### Making changes to User Service

1. Edit files in `services/user-service/`
2. Changes are picked up automatically (hot reload in DEBUG mode)
3. Test: `docker-compose exec user-service python manage.py test`
4. Commit and push

### Making changes to Loan Service

1. Edit files in `services/loan-service/`
2. Changes are picked up automatically
3. Test: `docker-compose exec loan-service python manage.py test`
4. Commit and push

### Making changes to API Gateway

1. Edit files in `services/api-gateway/`
2. Changes are picked up automatically
3. No tests (integration tests recommended)
4. Commit and push

## Troubleshooting

### Services won't start
```bash
# Check docker-compose logs
docker-compose logs --tail=50

# Rebuild images
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Database connection errors
```bash
# Ensure postgres services are healthy
docker-compose ps

# Check postgres logs
docker-compose logs postgres-user postgres-loan

# Reset databases
docker-compose down -v  # WARNING: This deletes all data!
docker-compose up
```

### JWT token issues
```bash
# Ensure JWT_SECRET_KEY is set in .env
# Token expiry is 2 hours - re-login to get new token
```

### API Gateway can't reach services
- Ensure services are on same network: `docker network ls | grep microservices`
- Check service URLs in `.env` (use service name, not localhost)
- Verify services are running: `docker-compose ps`

## Next Steps & TODO

1. **Add API Gateway rate limiting**
2. **Implement RabbitMQ event bus for true async communication**
3. **Add Redis caching layer**
4. **Kubernetes deployment files (helm charts)**
5. **Service mesh (Istio) for advanced networking**
6. **Integration tests across services**
7. **API versioning** (e.g., `/api/v1/...`)
8. **Swagger/OpenAPI documentation generation**
9. **Implement circuit breakers** for service resilience
10. **Add distributed tracing** (Jaeger/Zipkin)
11. **Migrate to `djangorestframework-simplejwt`** for better JWT handling
12. **Add request validation middleware** in API Gateway

## Architecture Decision Records (ADRs)

### ADR-1: Separate Databases per Service
- **Decision:** Each microservice has its own PostgreSQL database
- **Rationale:** Supports independent scaling, schema evolution, and technology choices
- **Trade-off:** Requires eventual consistency and distributed transactions

### ADR-2: Synchronous HTTP Communication
- **Decision:** API Gateway communicates with services via HTTP (not gRPC initially)
- **Rationale:** Simpler development, better observability, language-agnostic
- **Trade-off:** Slightly higher latency than gRPC

### ADR-3: API Gateway Pattern
- **Decision:** Single entry point (API Gateway) routes to services
- **Rationale:** Unified authentication, versioning, rate limiting
- **Trade-off:** Gateway becomes potential bottleneck (mitigated by load balancing)

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make changes and test locally
4. Commit with clear messages
5. Push and open a Pull Request

## License

MIT

## Support

For issues, questions, or feature requests, open an issue on GitHub or contact the team.
