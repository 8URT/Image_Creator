# Google OAuth Setup Guide

## Overview

Google OAuth is already fully implemented in the application. This guide will help you configure it for both development and production environments.

## Prerequisites

- A Google Cloud Platform account
- Access to [Google Cloud Console](https://console.cloud.google.com/)
- Admin access to your server (for production deployment)

## Step 1: Create Google OAuth Credentials

### 1.1 Create or Select a Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project name for reference

### 1.2 Configure OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen"
2. Choose "External" (unless you have a Google Workspace account)
3. Fill in the required information:
   - **App name**: "Image Creator" (or your preferred name)
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
4. Click "Save and Continue"
5. On the "Scopes" page, click "Add or Remove Scopes" and ensure these are included:
   - `openid`
   - `email`
   - `profile`
6. Click "Save and Continue"
7. Add test users if your app is in "Testing" mode (required for external apps)
8. Review and submit

### 1.3 Create OAuth 2.0 Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as the application type
4. Enter a name: "Image Creator" (or your preferred name)
5. **Authorized JavaScript origins** (add both):
   - `http://localhost:5000` (for development)
   - `https://lemauricienltd.com` (for production)
6. **Authorized redirect URIs** (add both):
   - `http://localhost:5000/auth/google/callback` (for development)
   - `https://lemauricienltd.com/auth/google/callback` (for production)
7. Click "Create"
8. **Important**: Copy the Client ID and Client Secret immediately (you won't be able to see the secret again)

## Step 2: Configure Environment Variables

### 2.1 Development Environment

1. In your project root, copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit the `.env` file and add your Google OAuth credentials:
   ```env
   # Flask Configuration
   FLASK_ENV=development
   SECRET_KEY=your-secret-key-here-change-in-production
   
   # Database
   DATABASE_URL=sqlite:///image_creator_dev.db
   
   # Google OAuth
   GOOGLE_CLIENT_ID=your-google-client-id-here
   GOOGLE_CLIENT_SECRET=your-google-client-secret-here
   
   # Application Settings
   BASE_URL=http://localhost:5000
   ADMIN_EMAIL=admin@example.com
   ```

3. Generate a secure SECRET_KEY:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

### 2.2 Production Environment

On your production server, update the `.env` file:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-here

# Database
DATABASE_URL=sqlite:///image_creator.db

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here

# Session Security (set to True in production with HTTPS)
SESSION_COOKIE_SECURE=True

# Application Settings
BASE_URL=https://lemauricienltd.com
ADMIN_EMAIL=your-admin-email@example.com
```

**Important**: Never commit the `.env` file to version control!

## Step 3: Verify Database Schema

The `google_id` field should already exist in the User model. If you're setting up a fresh database:

```bash
# Activate virtual environment
source venv/bin/activate

# Initialize database (if not already done)
flask db init

# Create migration
flask db migrate -m "Add google_id to users"

# Apply migration
flask db upgrade
```

If the database already exists and was created before the `google_id` field was added, run the migration commands above.

## Step 4: Test the Implementation

### 4.1 Development Testing

1. Start the application:
   ```bash
   flask run
   ```

2. Navigate to the login page: `http://localhost:5000/auth/login`

3. You should see a "Sign in with Google" button if the credentials are configured correctly

4. Click the button and test the OAuth flow:
   - You'll be redirected to Google's consent screen
   - After authorizing, you'll be redirected back to the application
   - You should be logged in automatically

### 4.2 Production Testing

1. Ensure all environment variables are set on the production server
2. Restart the application service:
   ```bash
   sudo systemctl restart image-creator
   ```
3. Visit: `https://lemauricienltd.com/image_creator`
4. Click "Sign in with Google" and test the OAuth flow

## How It Works

1. **User clicks "Sign in with Google"**: 
   - Application redirects to `/auth/google/login`
   - User is sent to Google's OAuth consent screen

2. **User authorizes**: 
   - Google redirects back to `/auth/google/callback` with an authorization code

3. **Server exchanges code for token**: 
   - The app exchanges the authorization code for an access token and ID token

4. **User info retrieved**: 
   - The app extracts user information (email, name, Google ID) from the ID token

5. **User created/linked**: 
   - If user exists with the Google ID → User is logged in
   - If user exists with the email but no Google ID → Google account is linked to existing user
   - If user doesn't exist → New user is created with Google account

6. **User logged in**: 
   - User session is created
   - User is redirected to the main page or the page they were trying to access

## Troubleshooting

### "Google OAuth is not configured" error

**Symptoms**: Button doesn't appear or error message shows

**Solutions**:
- Check that `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in your `.env` file
- Verify there are no typos in the environment variable names
- Restart the application after adding environment variables
- In production, ensure the systemd service has access to the `.env` file

### "Failed to initiate Google login" error

**Symptoms**: Clicking the button results in an error

**Solutions**:
- Verify the OAuth client is properly registered in `app/__init__.py`
- Check that the redirect URI matches exactly what's configured in Google Cloud Console
- Ensure the Google+ API or Identity Toolkit API is enabled in Google Cloud Console
- Check application logs for detailed error messages

### "Failed to retrieve user information from Google" error

**Symptoms**: OAuth flow starts but fails during callback

**Solutions**:
- Check that the OAuth scopes include `openid email profile`
- Verify the redirect URI in Google Cloud Console matches your callback URL exactly
- Ensure your app is published or test users are added (for external apps in testing mode)
- Check that the user's Google account has email verified

### Redirect URI mismatch

**Symptoms**: Google shows "redirect_uri_mismatch" error

**Solutions**:
- The redirect URI must match **exactly** (including http/https, port, and path)
- **Production redirect URI**: `https://lemauricienltd.com/auth/google/callback`
- **Development redirect URI**: `http://localhost:5000/auth/google/callback`
- Check both "Authorized JavaScript origins" and "Authorized redirect URIs" in Google Cloud Console
- Ensure no trailing slashes or extra characters
- Wait a few minutes after updating Google Cloud Console settings (changes may take time to propagate)

### Database errors

**Symptoms**: OAuth works but user creation fails

**Solutions**:
- Ensure the `google_id` column exists in the `users` table
- Run database migrations: `flask db upgrade`
- Check database permissions
- Verify database connection is working

### OAuth button not appearing

**Solutions**:
- Check that `GOOGLE_CLIENT_ID` is set (even if secret is missing, the button should appear)
- Verify the login template is correctly checking for `google_auth_url`
- Check browser console for JavaScript errors
- Ensure the application has restarted after adding environment variables

## Security Notes

1. **Never commit `.env` file**: It contains sensitive credentials
2. **Use HTTPS in production**: OAuth requires secure connections in production
3. **Set `SESSION_COOKIE_SECURE=True`**: In production with HTTPS
4. **Rotate secrets regularly**: Change your `SECRET_KEY` and OAuth credentials periodically
5. **Limit redirect URIs**: Only add the exact URIs you need in Google Cloud Console
6. **Use strong SECRET_KEY**: Generate a secure random key (32+ characters)
7. **Restrict OAuth app access**: In Google Cloud Console, limit who can use the OAuth app if possible

## Production Checklist

Before deploying to production, ensure:

- [ ] OAuth credentials configured in production `.env` file
- [ ] `BASE_URL=https://lemauricienltd.com` set in production `.env`
- [ ] `SESSION_COOKIE_SECURE=True` in production `.env`
- [ ] Redirect URI `https://lemauricienltd.com/auth/google/callback` added in Google Cloud Console
- [ ] Authorized JavaScript origin `https://lemauricienltd.com` added in Google Cloud Console
- [ ] HTTPS enabled on the server (SSL certificate configured)
- [ ] Database migrations applied (`flask db upgrade`)
- [ ] Application service restarted (`sudo systemctl restart image-creator`)
- [ ] Test OAuth flow at `https://lemauricienltd.com/image_creator`
- [ ] Verify OAuth button appears on login page
- [ ] Test complete OAuth flow end-to-end

## Deployment Details

**Production Server Configuration:**
- **Domain**: `lemauricienltd.com`
- **Application URL**: `https://lemauricienltd.com/image_creator`
- **Login URL**: `https://lemauricienltd.com/auth/login`
- **OAuth Callback**: `https://lemauricienltd.com/auth/google/callback`
- **Server IP**: `178.128.18.58` (DigitalOcean droplet)
- **Internal Port**: `8000` (proxied through Nginx)
- **Service Name**: `image-creator` (systemd)

## Quick Reference

### Google Cloud Console URLs
- **OAuth Consent Screen**: `https://console.cloud.google.com/apis/credentials/consent`
- **Credentials**: `https://console.cloud.google.com/apis/credentials`
- **API Library**: `https://console.cloud.google.com/apis/library`

### Application URLs
- **Development**: `http://localhost:5000`
- **Production**: `https://lemauricienltd.com`

### OAuth Redirect URIs
- **Development**: `http://localhost:5000/auth/google/callback`
- **Production**: `https://lemauricienltd.com/auth/google/callback`

### Environment Variables Required
```env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
BASE_URL=https://lemauricienltd.com  # or http://localhost:5000 for dev
SESSION_COOKIE_SECURE=True  # for production only
```

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Documentation](https://docs.authlib.org/)
- [Flask-Login Documentation](https://flask-login.readthedocs.io/)
