# Memoir Form API Documentation

This document describes the API endpoints for the memoir form functionality in the Scribble in Time application.

## Base URL
All endpoints are prefixed with `/api/`

## Endpoints

### 1. Submit Memoir Form
**POST** `/api/memoir/submit/`

Submit a new memoir form with personal and memoir details.

#### Request Body
```json
{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "gender": "male",
    "theme": "Overcoming adversity",
    "subject": "My journey through cancer",
    "main_themes": "Resilience, family support, medical journey",
    "key_life_events": "Diagnosis, treatment, recovery, new perspective",
    "audience": "family_friends"
}
```

#### Field Descriptions
- `first_name` (string, required): First name of the person
- `last_name` (string, required): Last name of the person
- `email` (string, required): Valid email address
- `phone_number` (string, required): Phone number (minimum 10 characters)
- `gender` (string, required): One of: "male", "female", "other", "prefer_not_to_say"
- `theme` (string, required): Overall theme of the memoir
- `subject` (string, required): Subject of the memoir
- `main_themes` (string, required): Main themes to cover in the memoir
- `key_life_events` (string, required): Key life events to include
- `audience` (string, required): One of: "family_friends", "public", "specific_group"

#### Response (Success - 201)
```json
{
    "success": true,
    "message": "Memoir form submitted successfully! We will review your submission and get back to you soon.",
    "data": {
        "id": 1,
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone_number": "+1234567890",
        "gender": "male",
        "theme": "Overcoming adversity",
        "subject": "My journey through cancer",
        "main_themes": "Resilience, family support, medical journey",
        "key_life_events": "Diagnosis, treatment, recovery, new perspective",
        "audience": "family_friends",
        "submitted_at": "2024-01-15T10:30:00Z",
        "is_processed": false
    },
    "submission_id": 1
}
```

#### Response (Validation Error - 400)
```json
{
    "success": false,
    "message": "Validation failed",
    "errors": {
        "email": ["Please provide a valid email address."],
        "first_name": ["This field is required."]
    }
}
```

### 2. Get Memoir Form Submissions (Admin)
**GET** `/api/memoir/submissions/`

Retrieve all memoir form submissions with filtering and pagination. This endpoint is designed for admin use.

#### Query Parameters
- `page` (integer, optional): Page number for pagination (default: 1)
- `page_size` (integer, optional): Number of items per page (default: 20, max: 100)
- `search` (string, optional): Search term for filtering by name, email, or theme
- `audience` (string, optional): Filter by audience type
- `is_processed` (string, optional): Filter by processing status ("true" or "false")
- `date_from` (string, optional): Filter submissions from this date (YYYY-MM-DD format)
- `date_to` (string, optional): Filter submissions until this date (YYYY-MM-DD format)

#### Example Requests
```
GET /api/memoir/submissions/
GET /api/memoir/submissions/?page=2&page_size=10
GET /api/memoir/submissions/?search=john&audience=family_friends
GET /api/memoir/submissions/?is_processed=false&date_from=2024-01-01
```

#### Response (Success - 200)
```json
{
    "success": true,
    "data": [
        {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone_number": "+1234567890",
            "gender": "male",
            "theme": "Overcoming adversity",
            "subject": "My journey through cancer",
            "main_themes": "Resilience, family support, medical journey",
            "key_life_events": "Diagnosis, treatment, recovery, new perspective",
            "audience": "family_friends",
            "submitted_at": "2024-01-15T10:30:00Z",
            "is_processed": false
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_count": 100,
        "has_next": true,
        "has_previous": false,
        "page_size": 20
    },
    "filters": {
        "search": "john",
        "audience": "family_friends",
        "is_processed": "false",
        "date_from": "2024-01-01",
        "date_to": ""
    }
}
```

### 3. Get Memoir Form Options
**GET** `/api/memoir/options/`

Get available options for the memoir form (gender choices, audience choices, etc.).

#### Response (Success - 200)
```json
{
    "success": true,
    "data": {
        "gender_choices": [
            {"value": "male", "label": "Male"},
            {"value": "female", "label": "Female"},
            {"value": "other", "label": "Other"},
            {"value": "prefer_not_to_say", "label": "Prefer not to say"}
        ],
        "audience_choices": [
            {"value": "family_friends", "label": "Family and Friends"},
            {"value": "public", "label": "Public"},
            {"value": "specific_group", "label": "Specific Group"}
        ],
        "form_fields": {
            "personal_info": [
                "first_name", "last_name", "email", "phone_number", "gender"
            ],
            "memoir_details": [
                "theme", "subject", "main_themes", "key_life_events", "audience"
            ]
        }
    }
}
```

## Error Responses

All endpoints may return the following error responses:

### 500 Internal Server Error
```json
{
    "success": false,
    "message": "An error occurred while processing your request.",
    "error": "Detailed error message"
}
```

## Usage Examples

### Frontend Integration Example (JavaScript)

```javascript
// Submit a memoir form
async function submitMemoirForm(formData) {
    try {
        const response = await fetch('/api/memoir/submit/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('Form submitted successfully:', result.data);
            return result;
        } else {
            console.error('Validation errors:', result.errors);
            return result;
        }
    } catch (error) {
        console.error('Error submitting form:', error);
        throw error;
    }
}

// Get form submissions (admin)
async function getMemoirSubmissions(filters = {}) {
    try {
        const queryParams = new URLSearchParams(filters);
        const response = await fetch(`/api/memoir/submissions/?${queryParams}`);
        const result = await response.json();
        
        if (result.success) {
            return result;
        } else {
            console.error('Error fetching submissions:', result.message);
            return result;
        }
    } catch (error) {
        console.error('Error fetching submissions:', error);
        throw error;
    }
}

// Get form options
async function getMemoirFormOptions() {
    try {
        const response = await fetch('/api/memoir/options/');
        const result = await response.json();
        
        if (result.success) {
            return result.data;
        } else {
            console.error('Error fetching options:', result.message);
            return null;
        }
    } catch (error) {
        console.error('Error fetching options:', error);
        throw error;
    }
}
```

### cURL Examples

```bash
# Submit a memoir form
curl -X POST http://localhost:8000/api/memoir/submit/ \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "gender": "male",
    "theme": "Overcoming adversity",
    "subject": "My journey through cancer",
    "main_themes": "Resilience, family support, medical journey",
    "key_life_events": "Diagnosis, treatment, recovery, new perspective",
    "audience": "family_friends"
  }'

# Get memoir submissions with filters
curl "http://localhost:8000/api/memoir/submissions/?page=1&page_size=10&search=john&is_processed=false"

# Get form options
curl http://localhost:8000/api/memoir/options/
```

## Admin Interface

The memoir form submissions are also available in the Django admin interface at `/admin/scribble/memoirformsubmission/` where administrators can:

- View all submissions
- Filter by various criteria
- Mark submissions as processed/unprocessed
- Add processing notes
- Export data

## Database Schema

The `MemoirFormSubmission` model includes the following fields:

- `id`: Primary key
- `first_name`, `last_name`: Personal names
- `email`: Contact email
- `phone_number`: Contact phone
- `gender`: Gender selection
- `theme`, `subject`: Memoir details
- `main_themes`, `key_life_events`: Text fields for memoir content
- `audience`: Target audience
- `submitted_at`: Timestamp of submission
- `is_processed`: Processing status flag
- `processing_notes`: Admin notes for processing 