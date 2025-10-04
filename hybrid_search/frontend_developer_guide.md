# Frontend Developer Guide: Fixing 422 Errors

## Problem
Your frontend application is sending malformed requests to the `/search` endpoint, causing 422 "Unprocessable Entity" errors.

## Required Request Format

### 1. Authentication
All requests to `/search` require authentication. Include the Bearer token in the Authorization header:

```javascript
const headers = {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
};
```

### 2. Request Body Schema
The `/search` endpoint expects this exact JSON structure:

```json
{
  "query": "your search query here",
  "index_name": "passage_index",
  "search_method": "multi_stage",  // optional
  "num_results": 5                 // optional, 1-100
}
```

### 3. Required Fields
- `query` (string, required): The search query
- `index_name` (string, required): Must be "passage_index"

### 4. Optional Fields
- `search_method` (string, optional): "multi_stage", "semantic", "keyword"
- `num_results` (integer, optional): Number of results (1-100, default: 5)

## Example Working Request

```javascript
// 1. First login to get token
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'your_username',
    password: 'your_password'
  })
});

const { access_token } = await loginResponse.json();

// 2. Make search request with token
const searchResponse = await fetch('http://localhost:8000/search', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: "What is machine learning?",
    index_name: "passage_index",
    search_method: "multi_stage",
    num_results: 5
  })
});
```

## Common Mistakes to Avoid

### ❌ Wrong: Missing required fields
```json
{
  "query": "test"
  // Missing index_name
}
```

### ❌ Wrong: Wrong data types
```json
{
  "query": "test",
  "index_name": "passage_index",
  "num_results": "5"  // Should be number, not string
}
```

### ❌ Wrong: Invalid values
```json
{
  "query": "test",
  "index_name": "passage_index",
  "num_results": 0    // Must be >= 1
}
```

### ❌ Wrong: Missing Content-Type header
```javascript
// Don't do this
fetch('/search', {
  method: 'POST',
  body: JSON.stringify(data)  // Missing Content-Type header
});
```

### ❌ Wrong: No authentication
```javascript
// Don't do this
fetch('/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(data)  // Missing Authorization header
});
```

## Response Format

Successful requests return:

```json
{
  "query": "What is machine learning?",
  "answer": "Mock response for: What is machine learning? (User: username)",
  "method": "mock",
  "num_results": 0,
  "search_results": [],
  "content_analysis": {},
  "similarity_analysis": {},
  "validation_results": {},
  "step_times": {},
  "total_processing_time": 0.0,
  "input_tokens": 0,
  "output_tokens": 0,
  "total_tokens": 0,
  "cost_estimate": 0.0,
  "workflow_messages": ["Running in mock mode - workflow components not available"],
  "quality_score": 0.0,
  "error": "Workflow components not available",
  "timestamp": "2025-08-03T00:38:09.896782"
}
```

## Error Responses

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "index_name"],
      "msg": "Field required",
      "input": {"query": "test"},
      "url": "https://errors.pydantic.dev/2.5/v/missing"
    }
  ]
}
```

### 403 Forbidden
```json
{
  "detail": "Not authenticated"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid authentication credentials"
}
```

## Testing Your Fix

Use this curl command to test:

```bash
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser2", "password": "testpassword123"}'

# 2. Use the token in search request
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "index_name": "passage_index"}'
```

## Backend Code Reference

The backend expects this exact Pydantic model:

```python
class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query", min_length=1)
    index_name: str = Field(..., description="Name of the search index to use")
    search_method: Optional[str] = Field(None, description="Search method to use")
    num_results: Optional[int] = Field(None, description="Number of results to return", ge=1, le=100)
```

## Quick Checklist

- [ ] Include `Authorization: Bearer <token>` header
- [ ] Include `Content-Type: application/json` header
- [ ] Include `query` field (string, non-empty)
- [ ] Include `index_name` field (string, value: "passage_index")
- [ ] Ensure `num_results` is a number between 1-100 (if provided)
- [ ] Ensure `search_method` is a string (if provided)
- [ ] Send valid JSON in request body

## Need Help?

If you're still getting 422 errors after following this guide, please share:
1. The exact request body you're sending
2. The complete headers you're including
3. The full error response you're receiving 