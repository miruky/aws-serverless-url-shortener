# aws-serverless-url-shortener

Production-grade serverless URL shortener built on AWS Lambda, API Gateway, and DynamoDB.

## Architecture

```text
Client
  │
  ▼
API Gateway (REST)
  ├── POST   /urls          → CreateUrl Lambda
  ├── GET    /urls          → ListUrls Lambda
  ├── GET    /urls/{id}     → GetUrlStats Lambda
  ├── DELETE /urls/{id}     → DeleteUrl Lambda
  └── GET    /{id}          → RedirectUrl Lambda (301)
                                    │
                                    ▼
                              DynamoDB (urls)
```

## Tech Stack

| Category | Technology |
|:--|:--|
| Language | Python 3.12 |
| Compute | AWS Lambda |
| API | Amazon API Gateway (REST) |
| Database | Amazon DynamoDB (on-demand) |
| IaC | AWS CloudFormation |
| CI | GitHub Actions (lint + test) |
| CD | AWS CodePipeline + CodeBuild + CodeDeploy |
| Testing | pytest + moto (AWS mock) |
| Linting | ruff |

## Project Structure

```
.
├── .github/workflows/ci.yml       # GitHub Actions CI pipeline
├── infrastructure/
│   ├── template.yaml               # Core infrastructure (API GW, Lambda, DynamoDB)
│   └── pipeline.yaml               # CodePipeline + CodeBuild + CodeDeploy
├── src/
│   ├── handlers/                    # Lambda function handlers
│   │   ├── create_url.py
│   │   ├── redirect_url.py
│   │   ├── get_url_stats.py
│   │   ├── delete_url.py
│   │   └── list_urls.py
│   ├── models/
│   │   └── url.py                   # Domain model (frozen dataclass)
│   ├── repositories/
│   │   └── url_repository.py        # DynamoDB data access layer
│   └── utils/
│       ├── response.py              # API Gateway response builders
│       ├── validators.py            # Input validation
│       └── short_id.py              # Short ID generation (SHA-256 based)
├── tests/                           # Comprehensive pytest suite
├── buildspec.yml                    # CodeBuild build specification
├── pyproject.toml                   # Project metadata & tool config
└── Makefile                         # Developer shortcuts
```

## API Reference

### POST /urls

Create a shortened URL.

```json
// Request
{ "url": "https://example.com/very/long/path" }

// Response (201)
{
  "short_id": "aB3kZ9x",
  "original_url": "https://example.com/very/long/path",
  "created_at": 1711612800,
  "click_count": 0,
  "is_active": true
}
```

### GET /{short_id}

Redirect to the original URL (301).

### GET /urls/{short_id}

Retrieve click statistics.

### GET /urls?limit=20

List active URLs.

### DELETE /urls/{short_id}

Soft-delete a URL (sets `is_active` to `false`).

## Local Development

```bash
# Install dependencies
make install

# Run tests
make test

# Run linter
make lint
```

## Deployment

### 1. Deploy the CI/CD pipeline

```bash
aws cloudformation deploy \
  --template-file infrastructure/pipeline.yaml \
  --stack-name url-shortener-pipeline \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
      CodeStarConnectionArn=arn:aws:codestar-connections:... \
      Environment=dev
```

### 2. The pipeline automatically

1. **Source** — Pulls code from GitHub on push to `main`
2. **Build** — Runs lint + tests via CodeBuild, packages Lambda zip
3. **Deploy** — Creates/updates CloudFormation stack with Lambda functions

## Design Decisions

- **Frozen dataclass** for `UrlItem` — immutability prevents accidental mutation
- **Repository pattern** — decouples business logic from DynamoDB SDK calls
- **Dependency injection** in `UrlRepository` — enables moto-based testing without monkeypatching
- **Soft delete** — preserves audit trail; `is_active=false` items are filtered from listings
- **SHA-256 + timestamp** for ID generation — collision-resistant without external state

## License

MIT
