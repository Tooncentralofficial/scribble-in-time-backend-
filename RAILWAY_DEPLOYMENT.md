# Railway Deployment Guide

## Environment Variables

Set these environment variables in your Railway project:

### Required Variables:
- `SECRET_KEY`: A secure Django secret key
- `DEBUG`: Set to `False` for production
- `SITE_URL`: Your Railway app URL (e.g., `https://your-app.railway.app`)
- `OPENROUTER_API_KEY`: Your OpenRouter API key

### Optional Variables:
- `OPENROUTER_MODEL`: AI model to use (default: `meta-llama/llama-3.3-70b-instruct:free`)
- `RAILWAY_STATIC_URL`: Your Railway app URL (Railway may set this automatically)

## Deployment Steps

1. **Connect your GitHub repository to Railway**
2. **Set the environment variables** in Railway dashboard
3. **Deploy** - Railway will automatically:
   - Install dependencies from `requirements.txt`
   - Run migrations
   - Collect static files
   - Start the server using the `Procfile`

## Files Created for Railway:

- `Procfile`: Tells Railway how to start the app
- `railway.json`: Alternative configuration file
- `start.py`: Startup script that handles migrations and static files
- `gunicorn.conf.py`: Gunicorn configuration optimized for Railway

## Troubleshooting

If you see gunicorn errors:
1. Check that `PORT` environment variable is set (Railway sets this automatically)
2. Ensure all required environment variables are configured
3. Check Railway logs for specific error messages

## Local Development

For local development, you can still use:
```bash
python manage.py runserver
```

The settings will automatically detect if you're running locally or on Railway. 