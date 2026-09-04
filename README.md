# Fresho

## Project Overview

Fresho is an AI-powered apple supply-chain management system designed to reduce fruit waste and improve distribution efficiency. The system combines computer vision, deep learning, large language models, and route optimization to manage apple batches from harvest through delivery.

Traditional perishable-food supply chains often rely on static inventory and FIFO-based distribution, which does not account for the actual biological condition or remaining shelf life of produce. Fresho addresses this by analyzing every batch through AI models, estimating remaining shelf life, prioritizing batches using FEFO (First Expired, First Out) logic, and recommending the most suitable buyer or destination based on freshness urgency, geographic proximity, and buyer capacity.

The current prototype focuses on apple-only processing. The system is built as a full-stack application with a Python/FastAPI backend, a Next.js frontend, a PostgreSQL database, and integrated machine learning pipelines.

---

## Key Features

- **Multi-image batch upload with YOLO detection** -- Upload multiple apple images per batch. A YOLOv11 object detection model identifies and counts individual apples in each image.
- **Freshness classification** -- An EfficientNet-B0 deep learning model classifies each image as fresh or rotten.
- **Shelf-life range prediction** -- A second EfficientNet-B0 model predicts the remaining shelf life of apples in three ranges: 1-5 days, 5-10 days, and 10-14 days.
- **Digital Birth Certificate** -- An LLM-powered quality assessment is generated for each batch, including a quality status, risk level, AI summary, and recommended logistics action.
- **FEFO Priority Queue** -- Batches are sorted by estimated remaining shelf life, with risk level and quality status as secondary factors, ensuring the most urgent batches are handled first.
- **Buyer and destination recommendations** -- The system scores eligible buyers/destinations using a weighted model based on geographic distance, shelf-life urgency, and buyer capacity.
- **Genetic Algorithm route optimization** -- A genetic algorithm minimizes total travel distance, travel duration, shelf-life risk, and capacity violations when allocating batches to destinations.
- **Batch transfer and tracking** -- Full transfer lifecycle management from assignment through in-transit tracking to delivery confirmation, with automatic status history recording.
- **Batch status state machine** -- Validated status transitions prevent invalid state changes. The system tracks the complete lifecycle: CREATED, DETECTED, SHELF_LIFE_PREDICTED, RECOMMENDED, ASSIGNED_TO_BUYER, DISPATCHED, IN_TRANSIT, DELIVERED, COMPLETED.
- **Multi-user authentication** -- JWT-based authentication with user registration, login, and ownership-scoped batch access.
- **AI report generation** -- On-demand LLM generation of quality assessment reports for individual batches using Groq-hosted models.
- **Interactive batch details** -- Frontend batch detail pages display detection results, image galleries, shelf-life predictions, buyer recommendations, AI reports, and status transition controls.

---

## System Architecture

```
                    +-------------------+
                    |   Next.js (React) |
                    |   Frontend :3000  |
                    +--------+----------+
                             |
                        HTTP / REST
                             |
                    +--------v----------+
                    |  FastAPI Backend   |
                    |   Uvicorn :8000    |
                    +--------+----------+
                             |
          +------------------+------------------+
          |                  |                  |
  +-------v------+   +------v-------+  +-------v--------+
  |  PostgreSQL   |  |  YOLOv11     |  | Groq LLM       |
  |  Database     |  |  Detection   |  | (LangChain)    |
  +---------------+  +--------------+  +----------------+
          |                  |                  |
          |          +-------v-------+  +--------v---------+
          |          | EfficientNet  |  | OpenRouteService|
          |          | Freshness +   |  | Nominatim       |
          |          | Shelf-Life    |  | Geocoding       |
          |          +---------------+  +------------------+
          |
  +-------v-------+
  | Image Storage |
  | (uploads/)    |
  +---------------+
```

**Frontend** communicates with the **Backend** over HTTP REST endpoints at `/api/v1/*`. The backend orchestrates all AI/ML inference, database operations, and external API calls. Uploaded images are stored on disk and served as static files. The system uses PostgreSQL for persistent data storage and connects to external services for geocoding (Nominatim), road distance calculation (OpenRouteService), and LLM inference (Groq).

---

## End-to-End Workflow

The following describes the complete journey of an apple batch through the system:

1. **User Registration and Login** -- A farmer, supplier, or logistics operator registers an account with location information (address, pincode). The system resolves coordinates via Nominatim geocoding.

2. **Batch Creation with Image Upload** -- The user creates a new batch by providing a batch identifier, origin address, and one or more apple images (JPEG, PNG, or WEBP). Images are saved to disk under `uploads/batches/{batch_id}/original/`.

3. **YOLO Apple Detection** -- Each uploaded image is processed by the YOLOv11 detection model. The model identifies individual apples, producing bounding boxes and confidence scores. The total apple count across all images is aggregated and stored on the batch record.

4. **Freshness Prediction** -- Each image is passed through the freshness classification model (EfficientNet-B0), which classifies the image as fresh or rotten. Predictions across multiple images are aggregated using majority voting.

5. **Shelf-Life Prediction** -- Each image is also passed through the shelf-life prediction model (EfficientNet-B0), which predicts one of three remaining shelf-life ranges. The batch-level shelf-life prediction is determined by majority voting across all images.

6. **Batch Status Recorded** -- After detection and prediction, the batch status is set to DETECTED. All results (apple count, freshness prediction, shelf-life prediction, confidence scores) are persisted to PostgreSQL.

7. **Shelf-Life Analysis** -- The user triggers shelf-life prediction, which applies rule-based adjustments using the ML model output and freshness status to estimate remaining days, urgency level, predicted expiry date, and recommended sale deadline.

8. **Buyer and Destination Recommendations** -- The system retrieves all active destinations that accept apples and have available capacity. For each eligible destination, it calculates the geographic distance from the batch origin (using OpenRouteService for road distance or Haversine formula as fallback) and scores the destination using weighted criteria: distance (40%), shelf-life urgency (30%), capacity (20%), and urgency bonus (10%).

9. **AI Quality Report Generation** -- On demand, the system generates a structured quality assessment using a Groq-hosted LLM via LangChain. The LLM receives the verified model predictions (which it is instructed never to alter) and produces a quality status, risk level, summary, and recommended action. This report is persisted on the batch record.

10. **FEFO Prioritization** -- The FEFO queue sorts all active batches by estimated remaining shelf life (shortest first), with risk level and quality status as tiebreakers. Each batch receives a priority score and a recommended action: DISPATCH_NOW (critical), DISPATCH_NEXT (moderate), or NORMAL.

11. **Buyer Assignment** -- The user selects a recommended buyer destination. The batch status transitions to ASSIGNED_TO_BUYER and the assignment is recorded.

12. **Transfer and Tracking** -- The user initiates a transfer to the assigned destination. The system creates a transfer record with a unique transfer ID. The transfer progresses through statuses: TRANSFERRED, IN_TRANSIT, DELIVERED. When delivery is confirmed, the batch automatically transitions to COMPLETED.

13. **Dispatch (Alternative Path)** -- Alternatively, batches can be dispatched through the dispatch workflow, which records origin, destination, estimated delivery time, and manages dispatch status updates.

14. **Status History** -- Every status transition is recorded in the batch status history table with the previous status, new status, action description, actor, and timestamp. This provides a complete audit trail for every batch.

---

## Technology Stack

### Frontend
- **Framework**: Next.js 16.3 with React 19
- **Language**: TypeScript 5.7
- **Styling**: Tailwind CSS 4.3 with custom CSS
- **UI Components**: shadcn/ui, Lucide React icons
- **Package Manager**: pnpm
- **Analytics**: Vercel Analytics

### Backend
- **Framework**: FastAPI with Uvicorn
- **Language**: Python
- **ORM**: SQLAlchemy with psycopg2-binary
- **Authentication**: python-jose (JWT), passlib with bcrypt
- **Data Validation**: Pydantic v2 with email validation
- **Image Processing**: Pillow (PIL)
- **LLM Integration**: LangChain with LangChain-Groq

### Database
- **PostgreSQL** -- Primary data store for batches, users, destinations, route recommendations, dispatches, batch images, transfer records, and status history.

### AI and Machine Learning
- **Object Detection**: YOLOv11 (Ultralytics) -- Apple detection and counting
- **Freshness Classification**: EfficientNet-B0 (PyTorch) -- Binary classification (fresh/rotten)
- **Shelf-Life Prediction**: EfficientNet-B0 (PyTorch) -- Three-class classification (1-5 days, 5-10 days, 10-14 days)
- **LLM Reports**: Groq-hosted LLM via LangChain (structured output with Pydantic schema)

### External Services
- **Groq** -- LLM inference for quality assessment report generation
- **OpenRouteService** -- Road distance and travel duration calculation (matrix API)
- **Nominatim (OpenStreetMap)** -- Free geocoding for address-to-coordinate resolution

---

## Project Structure

```
fresho/
  api/
    main.py                  # FastAPI application entry point
    requirements.txt         # Python dependencies
    auth/
      dependencies.py        # JWT authentication dependency injection
    database/
      database.py            # SQLAlchemy engine, session, and base
      models.py              # All database models (Batch, User, Destination, etc.)
    models/
      yolo11/                # YOLOv11 model weights directory
    routes/
      auth.py                # /api/v1/auth -- register, login, profile
      user.py                # /api/v1/users -- profile management
      batch.py               # /api/v1/batches -- batch CRUD, AI report, FEFO queue
      batch_upload.py        # /api/v1/batch-upload -- multi-image upload with YOLO
      batch_status.py        # /api/v1/batch-status -- status transitions
      batch_transfer.py      # /api/v1/batches/{id}/transfer -- transfer lifecycle
      prediction.py          # /api/v1/predict -- single-image prediction
      shelf_life.py          # /api/v1/shelf-life -- shelf-life analysis
      buyer_recommendation.py # /api/v1/recommendations -- buyer scoring
      destination.py         # /api/v1/destinations -- destination management
      dispatch.py            # /api/v1/dispatch -- dispatch management
      routing.py             # /api/v1/routing -- route recommendations
      optimization.py        # /api/v1/optimization -- genetic algorithm
      certificate.py         # /api/v1/certificate -- digital birth certificate
      dashboard.py           # /api/v1/dashboard -- user dashboard data
    schemas/
      batch.py, user.py, certificate.py, destination.py,
      dispatch.py, optimization.py, prediction.py,
      routing.py, transfer.py
    services/
      auth_service.py        # JWT creation/verification, password hashing
      user_service.py        # User registration, authentication, profile updates
      batch_service.py       # Batch creation and retrieval
      yolo_services.py       # YOLOv11 detection service
      prediction_service.py  # EfficientNet-B0 inference for freshness and shelf life
      shelf_life_service.py  # Rule-based shelf-life estimation
      llm_service.py         # Groq LLM initialization and invocation
      certificate_service.py # Digital Birth Certificate generation
      fefo_service.py        # FEFO queue sorting and prioritization
      buyer_recommendation_service.py  # Destination scoring and recommendation
      routing_service.py     # Route recommendation with multi-factor scoring
      dispatch_service.py    # Dispatch creation and status management
      transfer_service.py    # Transfer lifecycle management
      status_service.py      # Status transition validation and state machine
      location_service.py    # Nominatim geocoding
      maps_service.py        # OpenRouteService matrix API integration
      genetic_optimizer.py   # Genetic Algorithm for batch-to-destination allocation
      genetic_algorithm_service.py  # GA service wrapper
  frontend/
    app/
      layout.tsx             # Root layout with AppLayout wrapper
      page.tsx               # Root redirect to /dashboard
      dashboard/page.tsx     # Main dashboard with FEFO queue
      batches/
        page.tsx             # Batch listing with FEFO sort
        create/page.tsx      # Batch creation with multi-image upload
        [batchId]/page.tsx   # Batch detail with detection, AI report, actions
      detection/page.tsx     # Standalone image detection tool
      shelf-life/page.tsx    # Shelf-life prediction display
      buyers/page.tsx        # Buyer/destination listing
      recommendations/page.tsx # Recommendation results
      login/page.tsx         # User login
      register/page.tsx      # User registration
      profile/page.tsx       # User profile management
    components/
      layout/AppLayout.tsx   # Sidebar navigation and page wrapper
      common/                # Reusable components (Metric, PageIntro, Status, Sparkline)
      ui/                    # Base UI primitives
    config/api.config.ts     # API endpoint configuration
    lib/
      apiClient.ts           # HTTP client with JWT auth headers
      utils.ts               # Utility functions (safeNumber, getImageUrl)
    services/
      authService.ts         # Auth API calls and session management
      batchService.ts        # Batch service (client-side)
      detectionService.ts    # Detection result helpers
      buyerService.ts        # Buyer-related API calls
      recommendationService.ts  # Recommendation API calls
      shelfLifeService.ts    # Shelf-life API calls
  model/
    models/
      apple_efficientnet_b0_best.pth               # Freshness model weights
      apple_shelf_life_efficientnet_b0_best.pth    # Shelf-life model weights
    yolo11/
      runs/apple_detection_gpu/weights/best.pt     # YOLOv11 detection weights
  uploads/
    batches/{batch_id}/original/                   # Uploaded original images
    batches/{batch_id}/annotated/                  # YOLO-annotated images (reserved)
  .env                      # Environment variables (not committed)
  .gitignore
```

---

## AI and Machine Learning

### Apple Detection with YOLOv11

The system uses a YOLOv11 model trained for apple detection. The model weights are located at `model/yolo11/runs/apple_detection_gpu/weights/best.pt`. The `YOLOService` class loads the model at startup using the Ultralytics library and provides methods for detecting apples in images.

Detection is performed during batch upload. Each uploaded image is processed with a confidence threshold of 0.25. The service returns bounding box coordinates, confidence scores, and class labels for each detected apple. Only detections with class name "apple" are retained.

### Apple Counting

Apples are counted per image and aggregated across all images in a batch. The total count and per-image counts are stored in the database. The average confidence across all detected apples in a batch is also recorded.

### Freshness Prediction

An EfficientNet-B0 model fine-tuned for binary classification predicts whether the apples in an image are fresh or rotten. The model weights are stored at `model/models/apple_efficientnet_b0_best.pth`. The model accepts 224x224 RGB images and outputs softmax probabilities over two classes: fresh and rotten.

During batch processing, each image is classified independently. The batch-level freshness prediction is determined by majority voting across all images. The average confidence across all images is stored as the batch freshness confidence.

### Shelf-Life Prediction

A second EfficientNet-B0 model predicts the remaining shelf-life range of apples in an image. The model weights are stored at `model/models/apple_shelf_life_efficientnet_b0_best.pth`. The model classifies images into three classes: "1-5 days", "5-10 days", and "10-14 days".

Like freshness prediction, shelf-life predictions are aggregated across all batch images using majority voting. The batch-level shelf-life prediction and average confidence are stored.

The `ShelfLifeService` further processes the ML model output using rule-based adjustments. It maps shelf-life labels to estimated day ranges, adjusts based on the freshness prediction (fresh = full shelf life, rotten = 20% of shelf life), applies confidence-based adjustments, and calculates estimated expiry dates and recommended sale deadlines.

### AI-Generated Batch Reports

The `CertificateService` and `LLMService` generate structured quality assessment reports using a Groq-hosted LLM accessed through LangChain. The LLM receives verified model predictions (freshness, shelf life, confidence scores, batch metadata) and is explicitly instructed not to alter any model predictions.

The LLM produces four structured fields:
- **quality_status**: GOOD, WARNING, or CRITICAL
- **risk_level**: LOW, MEDIUM, or HIGH
- **summary**: A short explanation of the batch assessment
- **recommended_action**: Practical logistics recommendation

The LLM output is validated against a Pydantic schema (`CertificateAssessment`) using structured output with JSON schema enforcement. Reports can be generated on demand from the batch detail page.

---

## FEFO Prioritization

FEFO (First Expired, First Out) is a distribution strategy that prioritizes items with the shortest remaining shelf life. This approach differs from FIFO (First In, First Out) by accounting for the actual biological condition of produce rather than simply processing in order of arrival.

Fresho implements FEFO through the `FEFOService`, which sorts active batches using three factors:

1. **Shelf-life priority** (primary): Batches with shorter remaining shelf life receive higher priority. "1-5 days" = priority 1, "5-10 days" = priority 2, "10-14 days" = priority 3.
2. **Risk level** (secondary): HIGH risk = priority 1, MEDIUM = 2, LOW = 3.
3. **Quality status** (tertiary): CRITICAL = priority 1, WARNING = 2, GOOD = 3.

A composite priority score is calculated as: `(shelf_priority * 50) + (risk_priority * 30) + (quality_priority * 20)`. Lower scores indicate higher urgency.

Based on the priority, each batch receives a recommended action:
- **DISPATCH_NOW**: Critical shelf life (1-5 days) or high risk or critical quality
- **DISPATCH_NEXT**: Moderate shelf life (5-10 days)
- **NORMAL**: Batch can remain in storage

The FEFO queue is displayed on the frontend dashboard and batch listing page, with visual indicators for urgency levels (URGENT, HIGH, MEDIUM, NORMAL).

---

## Location and Destination Recommendations

The buyer recommendation system scores each eligible destination for a given batch using four weighted criteria:

1. **Distance** (40% weight): Closer destinations receive higher scores. Distance is calculated using the Haversine formula for straight-line distance, adjusted by a 1.3x road-distance factor. When available, actual road distance and duration from OpenRouteService are used instead.

2. **Shelf-life urgency** (30% weight): Batches with shorter remaining shelf life receive higher urgency scores, driving them toward closer destinations.

3. **Capacity** (20% weight): Destinations with more available capacity receive higher scores. Capacity is normalized against a 10,000 kg reference.

4. **Urgency bonus** (10% weight): An additional bonus for CRITICAL urgency batches (100 points), MODERATE (50 points), or LOW (20 points).

**Destination eligibility** is filtered by:
- Destination status must be ACTIVE
- Accepted fruit type must match the batch fruit (currently "apple")
- Available capacity must be greater than zero

**Distance calculation fallback chain**:
1. Existing RouteRecommendation data from a previous routing run
2. OpenRouteService matrix API for actual road distance (requires API key)
3. Haversine formula using batch origin and destination coordinates (requires geocoded coordinates)
4. Default fallback values (50.0 km distance, 120.0 minutes duration)

---

## Batch Transfer and Tracking

The transfer system manages the lifecycle of batch movements from assignment to delivery. The `TransferService` implements the following:

**Transfer Creation**: When a batch is transferred to a destination, the system:
- Validates the batch is in an eligible status (CREATED, DETECTED, ANALYZED, SHELF_LIFE_PREDICTED, RECOMMENDED, ASSIGNED_TO_BUYER, READY_FOR_TRANSFER, AVAILABLE, FEFO_SELECTED, or ROUTE_RECOMMENDED)
- Checks for no existing active transfers (TRANSFERRED or IN_TRANSIT)
- Generates a unique transfer ID (format: TRF-YYYYMMDD-XXXXXXXX)
- Creates a transfer record and updates batch status to TRANSFERRED

**Transfer Status Updates**: Transfers progress through a defined state machine:
- TRANSFERRED -> IN_TRANSIT
- TRANSFERRED -> DELIVERED
- IN_TRANSIT -> DELIVERED

**Automatic Completion**: When a transfer reaches DELIVERED status, the batch is automatically transitioned to COMPLETED.

**Transfer History**: The system maintains a complete history of all transfers for a batch, including transfer records, status timestamps, and the full batch status history.

**Dispatch Workflow**: An alternative dispatch path exists through the `DispatchService`, which creates dispatch records with origin/destination details, estimated delivery times, and supports status updates through DISPATCHED, IN_TRANSIT, DELIVERED, RISK_INCREASED, REROUTING_REQUIRED, and REROUTED states. Delivery confirmation also triggers automatic completion.

---

## API Overview

All endpoints are prefixed with `/api/v1` unless otherwise noted. Authentication is required for most endpoints via a JWT Bearer token in the Authorization header.

### Authentication
- `POST /api/v1/auth/register` -- Register a new user account
- `POST /api/v1/auth/login` -- Login and receive a JWT token
- `GET /api/v1/auth/me` -- Get current user profile

### User Management
- `GET /api/v1/users/me` -- Get own profile
- `PATCH /api/v1/users/me` -- Update profile information
- `PATCH /api/v1/users/me/password` -- Change password

### Batch Management
- `POST /api/v1/batch-upload` -- Upload images and create batch with YOLO detection
- `GET /api/v1/batches` -- List all batches
- `GET /api/v1/batches/{batch_id}` -- Get batch details with images
- `DELETE /api/v1/batches/{batch_id}` -- Delete a batch (only early lifecycle stages)
- `GET /api/v1/batches/fefo/queue` -- Get FEFO-prioritized queue

### Batch Status
- `PATCH /api/v1/batch-status/{batch_id}` -- Update batch status (validated transitions)
- `GET /api/v1/batch-status/{batch_id}/history` -- Get status change history
- `GET /api/v1/batch-status/{batch_id}/valid-transitions` -- Get valid next statuses

### Batch Transfer
- `POST /api/v1/batches/{batch_id}/transfer` -- Initiate transfer to a destination
- `GET /api/v1/batches/{batch_id}/transfer-history` -- Get transfer history
- `PATCH /api/v1/batches/{batch_id}/transfer-status/{transfer_id}` -- Update transfer status

### Predictions
- `POST /api/v1/predict/apple` -- Predict freshness and shelf life for a single image
- `GET /api/v1/shelf-life/predict/{batch_id}` -- Run shelf-life analysis for a batch

### Recommendations
- `GET /api/v1/recommendations/buyer/{batch_id}` -- Get buyer recommendations
- `POST /api/v1/recommendations/assign/{batch_id}` -- Assign batch to a buyer

### AI Reports
- `POST /api/v1/batches/{batch_id}/ai-report` -- Generate AI quality assessment report

### Destinations
- `POST /api/v1/destinations` -- Create a destination
- `GET /api/v1/destinations` -- List all destinations
- `GET /api/v1/destinations/{destination_id}` -- Get destination details

### Dispatch
- `POST /api/v1/dispatch` -- Create a dispatch
- `GET /api/v1/dispatch` -- List all dispatches
- `GET /api/v1/dispatch/{dispatch_id}` -- Get dispatch details
- `PATCH /api/v1/dispatch/{dispatch_id}/status` -- Update dispatch status

### Route Optimization
- `POST /api/v1/routing/recommend` -- Get route recommendations for a batch
- `POST /api/v1/optimization/run` -- Run genetic algorithm optimization

### Dashboard
- `GET /api/v1/dashboard/summary` -- Get dashboard summary statistics
- `GET /api/v1/dashboard/batches` -- Get all batches for the logged-in user
- `GET /api/v1/dashboard/batches/{batch_id}` -- Get detailed batch info for the dashboard

### System
- `GET /` -- Service status
- `GET /health` -- Health check

### Static Files
- `GET /uploads/batches/{batch_id}/original/{filename}` -- Access uploaded batch images

---

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- Node.js 18 or later with pnpm
- PostgreSQL 12 or later
- (Optional) NVIDIA GPU with CUDA for accelerated YOLO and EfficientNet inference

### Backend Setup

1. Navigate to the project root directory.

2. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
# or
venv\Scripts\activate           # Windows
```

3. Install Python dependencies:
```bash
pip install -r api/requirements.txt
```

4. Create the `.env` file in the project root with the required environment variables (see Environment Variables section below).

5. Create the PostgreSQL database:
```bash
psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE self_life;"
```

6. Database tables are created automatically on server startup via SQLAlchemy's `create_all()`.

7. Start the FastAPI server:
```bash
uvicorn api.main:app --reload
```

The backend will be available at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
pnpm install
```

3. Start the development server:
```bash
pnpm run dev
```

The frontend will be available at `http://localhost:3000`.

### Running the Complete Application

1. Ensure PostgreSQL is running on `localhost:5432`.

2. Start the backend server from the project root:
```bash
uvicorn api.main:app --reload
```

3. In a separate terminal, start the frontend:
```bash
cd frontend
pnpm run dev
```

4. Open `http://localhost:3000` in a web browser. You will be redirected to the dashboard. Register a new account or log in to begin using the system.

---

## Environment Variables

Create a `.env` file in the project root directory with the following variables:

```env
# Database connection string
DATABASE_URL=postgresql://username:password@localhost:5432/self_life

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-here
JWT_EXPIRE_MINUTES=60

# Groq LLM API (required for AI report generation)
GROQ_API=your-groq-api-key-here

# OpenRouteService API (optional, for road distance calculation)
OPENROUTESERVICE_API_KEY=your-openrouteservice-api-key-here

# Routing provider (default: openrouteservice)
ROUTING_PROVIDER=openrouteservice
```

**Required variables:**
- `DATABASE_URL` -- PostgreSQL connection string
- `JWT_SECRET_KEY` -- Secret key for JWT token signing
- `GROQ_API` -- API key for Groq LLM service (required for AI report generation)

**Optional variables:**
- `JWT_EXPIRE_minutes` -- JWT token expiry in minutes (default: 60)
- `OPENROUTESERVICE_API_KEY` -- API key for road distance calculation. When not provided, the system falls back to Haversine distance estimation.
- `ROUTING_PROVIDER` -- Currently only "openrouteservice" is supported.

**Frontend environment variable:**
- `NEXT_PUBLIC_API_BASE_URL` -- Backend API URL (defaults to `http://localhost:8000/api/v1`). Set this in the frontend directory if the backend runs on a different host or port.

---

## Image Storage

Uploaded batch images are stored on the local filesystem under the `uploads/` directory at the project root. The directory structure is:

```
uploads/
  batches/
    {batch_id}/
      original/        # Original uploaded images
      annotated/       # YOLO-annotated images (reserved for future use)
```

The FastAPI backend mounts the `uploads/` directory as a static file directory, making images accessible at `/uploads/batches/{batch_id}/original/{filename}`. The frontend resolves image URLs by prepending the backend base URL (without the `/api/v1` prefix).

---

## API Documentation

FastAPI automatically generates interactive API documentation. After starting the backend server, access the documentation at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

The documentation includes all endpoint details, request/response schemas, and allows interactive testing of API endpoints.

---

## Error Handling and Fallbacks

The system implements several graceful fallback mechanisms:

- **Prediction failures**: If the freshness or shelf-life model fails to process an image during batch upload, the error is logged and processing continues with remaining images. The batch still receives predictions from any successfully processed images.

- **Missing shelf-life values**: The FEFO service handles missing or "N/A" shelf-life predictions by assigning a default priority of 999, placing these batches at the end of the queue. The dashboard and batch listing pages display "Awaiting prediction" for batches without shelf-life data.

- **Geographic distance fallback**: The buyer recommendation service uses a multi-tier fallback chain for distance calculation: existing route data, OpenRouteService API, Haversine formula, and finally a hardcoded default (50 km / 120 minutes). This ensures recommendations are always generated even when external services are unavailable.

- **Missing OpenRouteService API key**: When the `OPENROUTESERVICE_API_KEY` environment variable is not set, the `MapsService` raises an exception that is caught by callers, which then fall back to Haversine-based distance estimation using geocoded coordinates.

- **Missing Groq API key**: The `LLMService` raises a `RuntimeError` at startup if the `GROQ_API` environment variable is not configured. AI report generation and Digital Birth Certificate features will not be available without this key.

- **Batch deletion safeguards**: Batches in DISPATCHED, IN_TRANSIT, DELIVERED, COMPLETED, or TRANSFERRED status cannot be deleted, preventing data loss for active logistics operations.

- **Status transition validation**: The `StatusService` enforces a defined state machine for batch status transitions. Invalid transitions are rejected with descriptive error messages listing the valid options.

---

## Current Limitations

- **Apple-only processing**: The current prototype is designed exclusively for apple batches. The fruit type field exists in the data model, but all ML models and detection logic are trained and configured for apples only.

- **No real-time tracking**: The transfer and dispatch tracking relies on manual status updates. There is no GPS-based real-time location tracking of in-transit batches.

- **Static genetic algorithm input**: The genetic algorithm optimization endpoint initializes batch-to-destination distances to 0.0, meaning the optimization currently runs without actual distance data. Integration with the routing service to provide real distance inputs is pending.

- **No automated re-analysis**: Once freshness and shelf-life predictions are generated, there is no mechanism to periodically re-analyze batches as conditions change over time.

- **No multi-fruit buyer compatibility scoring**: While destinations have an `accepted_fruit` field, the buyer recommendation scoring does not weight fruit compatibility beyond simple filtering.

- **Image annotation storage**: The system creates directories for YOLO-annotated images but does not currently save annotated output images to disk.

- **LLM API key dependency**: AI report generation and Digital Birth Certificate features are unavailable without a valid Groq API key. There is no offline fallback for these features.

- **No role-based access control**: All authenticated users have the same permissions. The user model includes a `role` field but it is not enforced for access control.

---

## Future Improvements

- **Multi-fruit support**: Extend the detection, freshness, and shelf-life models to support additional fruit types such as bananas, oranges, and mangoes.

- **Real-time GPS tracking**: Integrate GPS tracking for in-transit batches to provide live location updates on the dashboard.

- **Automated re-analysis**: Implement periodic re-analysis of batches based on elapsed time and storage conditions to update shelf-life predictions.

- **Advanced ML recommendation model**: Replace the rule-based buyer recommendation system with a trained ML model that can learn from historical allocation data.

- **Mobile application**: Build a companion mobile application for field workers to capture images and update batch status on-site.

- **Notification system**: Add email or SMS notifications for critical shelf-life events, dispatch confirmations, and delivery completions.

- **Batch quantity management**: Add weight or quantity tracking per batch to improve dispatch planning and destination capacity management.

- **Role-based access control**: Implement admin, supplier, and logistics operator roles with differentiated permissions.

- **Batch re-analysis and shelf-life re-estimation**: Allow shelf-life predictions to be updated as batches age, using sensor data or updated imagery.

- **Historical analytics dashboard**: Build analytics views showing waste reduction metrics, delivery performance, and shelf-life prediction accuracy over time.
