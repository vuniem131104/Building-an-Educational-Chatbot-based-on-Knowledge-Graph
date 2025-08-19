import React, { useState } from 'react';
import axios from 'axios';
import './FileUpload.css';

const FileUpload = () => {
  const [files, setFiles] = useState([]);
  const [courseCode, setCourseCode] = useState('');
  const [weekNumber, setWeekNumber] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    setFiles(selectedFiles);
    setUploadStatus('');
  };

  const handleCourseCodeChange = (event) => {
    setCourseCode(event.target.value.toUpperCase());
  };

  const handleWeekNumberChange = (event) => {
    setWeekNumber(event.target.value);
  };

  const validateForm = () => {
    if (!files.length) {
      setUploadStatus('Please select at least one file to upload');
      return false;
    }
    if (!courseCode.trim()) {
      setUploadStatus('Please enter the course code');
      return false;
    }
    if (!weekNumber.trim()) {
      setUploadStatus('Please enter the week number');
      return false;
    }
    if (isNaN(weekNumber) || parseInt(weekNumber) < 1 || parseInt(weekNumber) > 15) {
      setUploadStatus('Week number must be between 1 and 15');
      return false;
    }
    // Validate file types
    const allowedExts = ['pdf', 'doc', 'docx', 'pptx'];
    for (const file of files) {
      const ext = file.name.split('.').pop().toLowerCase();
      if (!allowedExts.includes(ext)) {
        setUploadStatus(`File type .${ext} is not allowed: ${file.name}`);
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsUploading(true);
    setUploadStatus('Uploading files...');

    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });
    formData.append('course_code', courseCode);
    formData.append('week_number', weekNumber);

    try {
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setUploadStatus(`Đang upload... ${percentCompleted}%`);
        },
      });

      if (response.status === 200) {
        const results = response.data.results;
        let statusMsg = '';
        results.forEach((r) => {
          if (r.status === 'success') {
            statusMsg += `✔️ ${r.filename}: Upload successful\n`;
          } else {
            statusMsg += `❌ ${r.filename}: ${r.message}\n`;
          }
        });
        setUploadStatus(statusMsg.trim());
        // Reset form
        setFiles([]);
        setCourseCode('');
        setWeekNumber('');
        document.getElementById('file-input').value = '';
      } else {
        setUploadStatus('Upload failed. Please try again.');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setUploadStatus(
        error.response?.data?.detail || 'An error occurred while uploading the files'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="file-upload-container">
      <div className="file-upload-card">
        <h2 className="title">Upload Educational Materials</h2>
        <form onSubmit={handleSubmit} className="upload-form">
          {/* File Upload Section */}
          <div className="form-group">
            <label htmlFor="file-input" className="form-label">
              <span className="label-text">Select Files</span>
              <span className="required">*</span>
            </label>
            <div className="file-input-wrapper">
              <input
                id="file-input"
                type="file"
                onChange={handleFileChange}
                className="file-input"
                accept=".pdf,.doc,.docx,.pptx"
                multiple
              />
              <div className="file-input-display">
                {files.length ? (
                  <div className="file-info-list">
                    {files.map((file, idx) => (
                      <div key={idx} className="file-info">
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">({formatFileSize(file.size)})</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="file-placeholder">Select files to upload</span>
                )}
              </div>
            </div>
          </div>

          {/* Course Code Section */}
          <div className="form-group">
            <label htmlFor="course-code" className="form-label">
              <span className="label-text">Course Code</span>
              <span className="required">*</span>
            </label>
            <input
              id="course-code"
              type="text"
              value={courseCode}
              onChange={handleCourseCodeChange}
              className="form-input"
              placeholder="Example: INT3405, MAT1093..."
              maxLength={10}
            />
          </div>

          {/* Week Number Section */}
          <div className="form-group">
            <label htmlFor="week-number" className="form-label">
              <span className="label-text">Week Number</span>
              <span className="required">*</span>
            </label>
            <input
              id="week-number"
              type="number"
              value={weekNumber}
              onChange={handleWeekNumberChange}
              className="form-input"
              placeholder="Enter week number (1-15)"
              min="1"
              max="15"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isUploading}
            className={`submit-button ${isUploading ? 'uploading' : ''}`}
          >
            {isUploading ? 'Uploading...' : 'Upload File'}
          </button>
        </form>

        {/* Status Message */}
        {uploadStatus && (
          <div className={`status-message ${uploadStatus.includes('successful') ? 'success' : 'error'}`}>
            {uploadStatus}
          </div>
        )}

        {/* Info Section */}
        <div className="info-section">
          <h3>Information:</h3>
          <ul>
            <li>Bucket will be created with name: <strong>{courseCode || '[Course Code]'}</strong></li>
            <li>Folder: <strong>week-{weekNumber || '[Week Number]'}</strong></li>
            <li>Files:
              <ul>
                {files.length ? files.map((file, idx) => (
                  <li key={idx}><strong>{file.name}</strong></li>
                )) : <li>[Original File Name]</li>}
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
