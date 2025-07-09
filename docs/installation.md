# Installation Guide

## 💻 System Requirements

### Minimum Requirements
- **Python**: 3.12 or higher
- **Memory**: 512MB RAM (2GB+ recommended for production)
- **Storage**: 1GB free disk space
- **Network**: HTTPS capability for Slack integration

### Recommended for Production
- **Python**: 3.12+
- **Memory**: 4GB+ RAM
- **Storage**: 10GB+ SSD
- **CPU**: 2+ cores
- **Database**: PostgreSQL 13+
- **Cache**: Redis 6+

## 🔧 Installation Methods

### Method 1: Standard Installation

```bash
# 1. Clone repository
git clone https://github.com/arthurinuspace/agora.git
cd agora

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Verify installation
python -c "import fastapi; print('FastAPI installed successfully')"
```

### Method 2: Docker Installation

```bash
# 1. Clone repository
git clone https://github.com/arthurinuspace/agora.git
cd agora

# 2. Build Docker image
docker build -t agora .

# 3. Run with Docker Compose
docker-compose up -d
```

### Method 3: Development Installation

```bash
# 1. Clone repository
git clone https://github.com/arthurinuspace/agora.git
cd agora

# 2. Install in development mode
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 3. Install development dependencies
pip install -r requirements-dev.txt
```

## 🔍 Verification

### Basic Verification
```bash
# Activate virtual environment
source venv/bin/activate

# Test core imports
python -c "from services import ServiceContainer; print('✅ Services imported successfully')"

# Test SOLID architecture
python -c "from services import configure_services, ServiceContainer; container = ServiceContainer(); configure_services(container); print('✅ SOLID architecture verified')"
```

### Advanced Verification
```bash
# Run health check
python -c "from app_factory import create_test_app; app = create_test_app(); print('✅ Application factory working')"

# Test database connection
python database.py

# Run basic tests
python -m pytest test_solid_architecture.py::test_full_solid_architecture -v
```

## 🚫 Troubleshooting

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version

# If < 3.12, install newer Python
# Ubuntu/Debian:
sudo apt update && sudo apt install python3.12

# macOS (with Homebrew):
brew install python@3.12
```

#### Virtual Environment Issues
```bash
# Remove existing venv
rm -rf venv

# Create new venv
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

#### Dependency Installation Issues
```bash
# Clear pip cache
pip cache purge

# Install with verbose output
pip install -r requirements.txt -v

# Install individually if needed
pip install fastapi uvicorn sqlalchemy
```

### Platform-Specific Issues

#### Windows
```bash
# Use Windows-specific activation
venv\Scripts\activate

# Install Visual C++ Build Tools if needed
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

#### macOS
```bash
# Install Xcode command line tools
xcode-select --install

# Use Homebrew for Python
brew install python@3.12
```

#### Linux
```bash
# Install Python development headers
sudo apt-get install python3.12-dev

# Install build essentials
sudo apt-get install build-essential
```

## See Also

- [Quick Start Guide](quick-start.md)
- [Configuration Guide](configuration.md)
- [Development Setup](development/setup.md)
- [Docker Deployment](deployment/docker.md)
