# 🖼️ Social Media Image Creator

A comprehensive Flask-based web application for creating professional social media images with customizable text, fonts, layouts, and branding options.

## ✨ Features

### 🎨 Image Creation Tools
- **Image Creator**: Main tool for creating social media images with customizable text, fonts, and layouts
- **Turf Magazine Creator**: Specialized tool with Turf logo support
- **Bulk Watermarking**: Batch process multiple images with watermarks
- **Quote Creator**: Create quote images with styled text
- **Long Title Creator**: Create images with extended titles
- **Photo Watermarker**: Add watermarks to photos

### 🔐 Authentication & User Management
- **Dual Authentication**: Google OAuth 2.0 and username/password login
- **User Management**: Admin panel for managing users, roles, and permissions
- **Session Management**: Secure session handling with Flask-Login
- **Fallback Authentication**: Emergency access system for administrators

### 👥 Admin Panel
- **User Management**: Create, edit, and manage user accounts
- **Template Configuration**: Dynamically configure tool templates (fonts, layouts, colors)
- **Usage Logging**: Track tool usage and user activity
- **Dashboard**: Overview of system statistics and activity

### 🎯 Advanced Features
- **Dynamic Font Selection**: Multiple Google Fonts (Fira Sans, Parkinsans, Hanken Grotesk, Inter, DM Sans)
- **Text Customization**: 
  - Title font weight (400-900)
  - Title kerning (-2px to 0px)
  - Vertical text block positioning
  - Subtitle background with customizable colors
- **Image Controls**:
  - Zoom (1-300%)
  - Horizontal/vertical offset
  - Cover/Fit to frame modes
- **Automatic Date Stamping**: French format date stamp with website branding
- **Logo Management**: Optional Turf logo, ML Info logo positioning
- **French Typography**: Automatic non-breaking spaces and apostrophes for French text

## 📐 Image Format

- **Canvas Size**: 1000×1250px (4:5 ratio, ideal for Facebook/Instagram)
- **Export Format**: High-quality PNG
- **Text Positioning**: Top Left, Bottom Left, Top Center, Bottom Center
- **Text Length**: Up to 400 characters for titles, 60 for subtitles

## 🚀 Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone git@github.com:8URT/Image_Creator.git
   cd Image_Creator
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   ```
   Edit `.env` and configure:
   - `SECRET_KEY`: Flask secret key (generate with `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `GOOGLE_CLIENT_ID`: Google OAuth client ID
   - `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
   - `FALLBACK_PASSWORD_HASH`: Bcrypt hash for fallback authentication
   - `FALLBACK_ENABLED`: Enable/disable fallback authentication
   - `ADMIN_EMAIL`: Admin user email
   - `ADMIN_PASSWORD`: Admin user password

5. **Initialize database**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application**
   ```bash
   python run.py
   ```
   Or for development:
   ```bash
   flask run --host=0.0.0.0 --port=8085
   ```

## 🌐 Deployment

### Production Deployment with Gunicorn and Nginx

1. **Install Gunicorn** (if not already installed)
   ```bash
   pip install gunicorn
   ```

2. **Configure Systemd Service**
   - Copy `systemd.service.example` to `/etc/systemd/system/image-creator.service`
   - Edit the service file with your paths
   - Enable and start the service:
     ```bash
     sudo systemctl enable image-creator
     sudo systemctl start image-creator
     ```

3. **Configure Nginx**
   - Copy `nginx.conf` to your Nginx configuration
   - Update server name and paths
   - Test and reload Nginx:
     ```bash
     sudo nginx -t
     sudo systemctl reload nginx
     ```

4. **Set up SSL** (recommended)
   - Use Let's Encrypt with Certbot
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

See `README_DEPLOYMENT.md` for detailed deployment instructions.

## 📁 Project Structure

```
Image_Creator/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration classes
│   ├── models.py            # Database models
│   ├── admin/               # Admin panel blueprint
│   │   ├── routes.py        # Admin routes
│   │   ├── forms.py         # Admin forms
│   │   └── decorators.py    # Admin decorators
│   ├── auth/                # Authentication blueprint
│   │   ├── routes.py        # Auth routes (login, OAuth)
│   │   └── decorators.py    # Auth decorators
│   ├── main/                # Main application blueprint
│   │   └── routes.py        # Main routes (tools dashboard)
│   ├── static/              # Static files
│   │   └── assets/          # Images, logos, etc.
│   └── templates/           # Jinja2 templates
│       ├── admin/           # Admin panel templates
│       ├── tools/           # Tool templates
│       ├── base.html        # Base template
│       └── login.html       # Login page
├── instance/                # Database instance
├── migrations/              # Database migrations
├── requirements.txt         # Python dependencies
├── run.py                   # Application entry point
├── gunicorn_config.py       # Gunicorn configuration
├── nginx.conf               # Nginx configuration example
├── deploy.sh                # Deployment script
└── README.md                # This file
```

## 🔧 Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key for session security
- `SQLALCHEMY_DATABASE_URI`: Database connection string (default: SQLite)
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `FALLBACK_PASSWORD_HASH`: Bcrypt hash for emergency access
- `FALLBACK_ENABLED`: Enable fallback authentication (True/False)

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://yourdomain.com/auth/authorize`
6. Copy Client ID and Client Secret to `.env`

## 🎨 Tool Features

### Image Creator
- Multiple font options (Fira Sans, Parkinsans, Hanken Grotesk, Inter)
- Title font weight control (400-900)
- Title kerning adjustment (-2px to 0px)
- Vertical text block positioning
- Subtitle background toggle with color customization
- Image zoom, offset, and sizing controls
- Optional Turf logo (top-right)
- Automatic date stamping (top-right)
- ML Info logo (bottom-center)

### Turf Magazine Creator
- All Image Creator features
- Turf logo (top-left, always visible)
- ML Info logo (bottom-center)

### Bulk Watermarking
- Batch process multiple images
- Customizable watermark positioning
- WebP output format support

## 🔒 Security Features

- Password hashing with bcrypt
- Session security (HttpOnly cookies)
- CSRF protection (Flask-WTF)
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection (Jinja2 auto-escaping)
- Environment variable secrets management

## 📝 Usage

1. **Login**: Access the application and log in with Google OAuth or username/password
2. **Select Tool**: Choose from the tools dashboard
3. **Upload Image**: Drag & drop, click to upload, or paste an image
4. **Customize**: Adjust text, fonts, colors, and positioning
5. **Generate**: Click "Generate Image" to preview
6. **Download**: Click "Download Image" to save your creation

## 👨‍💼 Admin Features

Access the admin panel at `/admin` (admin users only):

- **Dashboard**: System overview and statistics
- **Users**: Manage user accounts, roles, and permissions
- **Templates**: Configure tool templates dynamically
- **Logs**: View usage logs and user activity

## 🛠️ Development

### Running in Development Mode

```bash
export FLASK_APP=run.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=8085
```

### Database Migrations

```bash
# Create a new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback last migration
flask db downgrade
```

## 📦 Dependencies

Key dependencies:
- Flask: Web framework
- Flask-Login: User session management
- Flask-SQLAlchemy: Database ORM
- Flask-Migrate: Database migrations
- Flask-WTF: Form handling and CSRF protection
- Authlib: OAuth 2.0 authentication
- bcrypt: Password hashing
- gunicorn: WSGI server (production)

See `requirements.txt` for complete list.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary software. All rights reserved.

## 📞 Support

For issues, questions, or contributions, please contact the development team.

## 🎯 Roadmap

- [ ] Additional font options
- [ ] More template customization options
- [ ] Export to additional formats (JPG, WebP)
- [ ] Batch processing improvements
- [ ] Advanced image filters
- [ ] Template presets
- [ ] User-created templates

---

**Version**: 1.0.0  
**Last Updated**: 2026
