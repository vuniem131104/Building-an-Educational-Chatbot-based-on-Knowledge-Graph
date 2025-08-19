# Educational Platform - File Upload System

A comprehensive file upload system for educational purposes, allowing students and teachers to upload course materials organized by course code and week number.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 16+ (for frontend development)
- Python 3.11+ (for backend development)

### Start the System
```bash
./start.sh
```

### Stop the System
```bash
./stop.sh
```

## 📋 Features

### Frontend (ReactJS)
- **File Upload Interface**: Modern, responsive design
- **Course Organization**: Files organized by course code
- **Week Management**: Files categorized by week number  
- **Real-time Progress**: Upload progress tracking
- **File Validation**: Size and type validation
- **Responsive Design**: Works on desktop and mobile

### Backend (FastAPI)
- **MinIO Integration**: Secure file storage
- **RESTful API**: Clean API endpoints
- **File Organization**: Automatic bucket and folder structure
- **Validation**: Comprehensive input validation
- **Logging**: Detailed operation logging
- **CORS Support**: Frontend integration ready

### Storage (MinIO)
- **Bucket Structure**: `{course_code}` (e.g., `int3405`)
- **Folder Structure**: `tuan-{week_number}` (e.g., `tuan-1`)
- **File Names**: Original filenames preserved

## 🏗️ Architecture

```
frontend/                 # ReactJS frontend application
├── src/
│   ├── FileUpload.js    # Main upload component
│   ├── FileUpload.css   # Styling
│   └── ...
└── package.json

services/
└── file_upload/         # FastAPI backend service
    ├── src/
    │   └── file_upload/
    │       └── main.py  # FastAPI application
    └── Dockerfile

libs/                    # Shared libraries
├── storage/             # MinIO integration
├── logger/              # Logging utilities
└── base/                # Base models

docker-compose.yml       # Container orchestration
```

## 🌐 Endpoints

### Frontend
- **Development**: http://localhost:3000
- **Production**: Configurable

### Backend API
- **Base URL**: http://localhost:8000
- **Health Check**: `GET /api/health`
- **File Upload**: `POST /api/upload`
- **List Files**: `GET /api/files/{bucket_name}`

### MinIO Console
- **URL**: http://localhost:9001
- **Username**: minioadmin
- **Password**: minioadmin123

## 📁 File Organization Example

```
MinIO Storage:
├── int3405/                 # Course: INT3405
│   ├── tuan-1/              # Week 1
│   │   ├── lecture.pdf
│   │   └── homework.docx
│   ├── tuan-2/              # Week 2
│   │   └── quiz.pdf
│   └── ...
├── mat1093/                 # Course: MAT1093
│   ├── tuan-1/
│   │   └── chapter1.pdf
│   └── ...
```

## 🛠️ Development

### Frontend Development
```bash
cd frontend
npm install
npm start
```

### Backend Development
```bash
cd services/file_upload
pip install -e .
python -m uvicorn file_upload.main:app --reload --host 0.0.0.0 --port 8000
```

### Full Stack with Docker
```bash
docker-compose up -d
```

## 📝 Usage

1. **Access Frontend**: Open http://localhost:3000
2. **Select File**: Choose file to upload
3. **Enter Course Code**: Input course identifier (e.g., INT3405)
4. **Enter Week Number**: Input week number (1-20)
5. **Upload**: Click upload button
6. **Verify**: Check MinIO console for uploaded files

## 🔧 Configuration

### MinIO Settings
- **Endpoint**: localhost:9000 (development)
- **Access Key**: minioadmin
- **Secret Key**: minioadmin123
- **Secure**: false (development)

### File Limits
- **Maximum Size**: 50MB
- **Supported Types**: All file types
- **Week Range**: 1-20

## 📊 Monitoring

### Health Checks
- **Frontend**: React development server status
- **Backend**: `GET /api/health`
- **MinIO**: MinIO console accessibility

### Logs
- **Backend**: Comprehensive logging with structured data
- **MinIO**: Docker container logs
- **Frontend**: Browser console logs

## 🚨 Troubleshooting

### Common Issues
1. **Port Conflicts**: Ensure ports 3000, 8000, 9000, 9001 are available
2. **Docker Issues**: Run `docker-compose down` and retry
3. **Frontend Issues**: Clear npm cache and reinstall dependencies
4. **Backend Issues**: Check MinIO connectivity

### Debug Commands
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs minio
docker-compose logs file-upload-api

# Restart services
docker-compose restart
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
