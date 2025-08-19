# File Upload Frontend

ReactJS frontend application for uploading files to MinIO storage.

## Features

- File upload with drag and drop support
- Course code input
- Week number input  
- Real-time upload progress
- File validation
- Responsive design

## Structure

- Files are stored in MinIO with structure:
  - **Bucket**: Course code (lowercase)
  - **Folder**: `tuan-{week_number}`
  - **File**: Original filename

## Development

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

```bash
cd frontend
npm install
```

### Running

```bash
npm start
```

The app will be available at http://localhost:3000

### Building

```bash
npm run build
```

## API Integration

The frontend communicates with the backend API at:
- Development: http://localhost:8000
- Production: Configure via proxy in package.json

### API Endpoints

- `POST /api/upload` - Upload file
- `GET /api/files/{bucket_name}` - List files in bucket
- `GET /api/health` - Health check
