# Production Deployment Guide

## Railway.com + Neon PostgreSQL Setup

This guide will walk you through deploying your LeetCode Amigos application to Railway.com with a Neon PostgreSQL database.

### Prerequisites

- Railway.com account
- Neon PostgreSQL account
- Git repository pushed to GitHub/GitLab

### Step 1: Setup Neon PostgreSQL Database

1. Go to [console.neon.tech](https://console.neon.tech)
2. Create a new project
3. Note down your connection string (it should look like):
   ```
   postgresql://username:password@host:5432/database_name
   ```

### Step 2: Deploy to Railway.com

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your repository
5. Railway will automatically detect the `railway.toml` configuration

### Step 3: Configure Environment Variables

In your Railway dashboard, go to your project settings and add these environment variables:

#### Required Environment Variables:
```bash
# Database
DATABASE_URL=postgresql://your_neon_connection_string_here

# Security (Generate a strong secret key)
SECRET_KEY=your-super-secret-key-here-minimum-32-characters
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin User (Optional - defaults provided)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password
```

#### How to generate a secure SECRET_KEY:
```bash
# Python method
python -c "import secrets; print(secrets.token_urlsafe(32))"

# OpenSSL method
openssl rand -base64 32
```

### Step 4: Deploy

1. Railway will automatically deploy your application
2. The database tables will be created automatically on first run
3. An admin user will be created with the credentials you specified

### Step 5: Access Your Application

1. Railway will provide you with a URL like: `https://your-app-name.railway.app`
2. Navigate to this URL to access your application
3. Login with your admin credentials

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./leet_amigos.db` | Yes (for production) |
| `SECRET_KEY` | JWT secret key | `your-secret-key-here-change-in-production` | Yes |
| `ALGORITHM` | JWT algorithm | `HS256` | No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | `30` | No |
| `ADMIN_USERNAME` | Admin username | `admin` | No |
| `ADMIN_PASSWORD` | Admin password | `admin123` | No |
| `PORT` | Server port | `8000` | No (Railway sets this) |

### Local Development

For local development, you can still use SQLite:

1. Copy `.env.example` to `.env`
2. Keep `DATABASE_URL` commented out for SQLite
3. Set your preferred admin credentials
4. Run: `python main.py`

### Database Migration

The application will automatically create database tables on startup. No manual migration is needed.

### Troubleshooting

#### Common Issues:

1. **Database Connection Error**: Verify your Neon PostgreSQL connection string
2. **Secret Key Error**: Ensure SECRET_KEY is set and is at least 32 characters
3. **Admin User Issues**: Check ADMIN_USERNAME and ADMIN_PASSWORD environment variables

#### Checking Logs:
- Railway provides logs in the dashboard
- Check the deployment logs for any startup errors

### Production Considerations

1. **Security**: 
   - Use a strong SECRET_KEY (32+ characters)
   - Change default admin credentials
   - Enable HTTPS (Railway provides this by default)

2. **Database**:
   - Neon provides automatic backups
   - Consider connection pooling for high traffic

3. **Monitoring**:
   - Railway provides basic metrics
   - Monitor your Neon database usage

### Support

- Railway.com: Check their documentation and support
- Neon: Check their documentation for database issues
- Application issues: Check the logs in Railway dashboard