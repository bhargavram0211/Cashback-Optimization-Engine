# Cashback Optimization Engine - Frontend

## Phase 3: Streamlit Dashboard

Interactive dashboard for visualizing credit card cashback optimization insights.

---

## 🚀 Quick Start

### Option 1: Docker (Recommended) 🐳

**Run the entire stack (backend + frontend) with one command:**

```bash
# From project root
docker-compose up -d
```

The dashboard will be available at: **http://localhost:8501**

---

### Option 2: Local Development

#### Prerequisites

1. **Backend Running**: Ensure the backend is running at `http://localhost:8000`
   ```bash
   cd ..  # Go to project root
   docker-compose up -d backend db
   ```

2. **Python 3.9+**: Streamlit requires Python 3.9 or higher

#### Installation

1. **Create a Virtual Environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

#### Running the Dashboard

```bash
streamlit run app.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

---

## 📊 Dashboard Features

### 1. **Top-Level Metrics**
- **Total Spent**: Aggregate spending across all transactions
- **Actual Rewards**: Cashback earned with current card usage
- **Lost Savings**: Opportunity cost from suboptimal card choices

### 2. **Category Breakdown**
- Interactive bar chart showing lost savings by spending category
- Detailed table with transaction counts and cashback metrics
- Key insights highlighting the biggest optimization opportunities

### 3. **Card Recommendation**
- Visual card display showing the most recommended card
- Impact analysis with:
  - Number of times recommended
  - Total potential savings
  - Average savings per transaction
  - Coverage percentage

### 4. **Transaction Explorer**
- Detailed table of optimization opportunities
- Shows merchant, amount, category, and recommended card
- Sorted by lost savings (highest first)
- Limited to top 50 opportunities for performance

### 5. **User Selection**
- Sidebar input to switch between different users
- Default user ID pre-populated for testing

---

## 🎨 Technology Stack

- **Streamlit**: Interactive web application framework
- **Plotly**: Interactive data visualizations
- **Pandas**: Data manipulation and analysis
- **Requests**: HTTP client for backend API calls

---

## 🔧 Configuration

### Backend URL

The backend URL is automatically configured based on the environment:

**Docker (default):**
```bash
BACKEND_URL=http://backend:8000  # Uses Docker service name
```

**Local Development:**
```python
BACKEND_URL = "http://localhost:8000"  # Default if env var not set
```

To override, set the `BACKEND_URL` environment variable:
```bash
export BACKEND_URL=http://custom-host:8000
streamlit run app.py
```

---

## 📝 API Endpoints Used

The dashboard consumes the following backend endpoints:

1. **Consolidated Report**:
   - `GET /reports/savings/{user_id}`
   - Returns summary, category breakdown, and top recommendation

2. **Transaction Opportunities** (optional):
   - `GET /analytics/opportunities/{user_id}`
   - Returns individual transactions with optimization potential

---

## 🐛 Troubleshooting

### Dashboard won't start

**Error**: `ModuleNotFoundError: No module named 'streamlit'`

**Solution**: Make sure you've installed the dependencies:
```bash
pip install -r requirements.txt
```

---

### Can't connect to backend

**Error**: `Failed to fetch data from backend: Connection refused`

**Solution**: 
1. Check that the backend is running:
   ```bash
   curl http://localhost:8000/
   ```
2. If not running, start it:
   ```bash
   cd ..  # Go to project root
   docker-compose up -d
   ```

---

### No data showing

**Error**: `Unable to load data. Please check: User ID is valid`

**Solution**:
1. Verify the user exists in the database:
   ```bash
   docker exec -it cashback_postgres psql -U cashback_user -d cashback_db -c "SELECT id, email FROM users;"
   ```
2. Use a valid user ID in the sidebar

---

## 🎯 Next Steps

- Add time-series charts (spending trends over time)
- Implement merchant-level insights
- Add card portfolio optimization recommendations
- Export reports as PDF

---

## 📄 License

Part of the Cashback Optimization Engine project.

