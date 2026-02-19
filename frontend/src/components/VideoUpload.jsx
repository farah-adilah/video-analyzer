import { useState } from 'react';
import './VideoUpload.css';

function VideoUpload({ onVideoSelect }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);


  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'video/mp4') {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      onVideoSelect(file);
    } else {
      alert('Please select an MP4 video file');
    }
  };

  return (
    <div className="video-upload">
      <div className="upload-area">
        <input
          type="file"
          accept="video/mp4"
          onChange={handleFileChange}
          id="video-input"
          style={{ display: 'none' }}
        />
        <label htmlFor="video-input" className="upload-button">
          {selectedFile ? `Selected: ${selectedFile.name}` : 'Upload Video (.mp4)'}
        </label>
        {previewUrl && (
          <video 
            src={previewUrl} 
            controls 
            style={{ maxWidth: '100%', marginTop: '10px' }}
          />
        )}
      </div>
    </div>
  );
}

export default VideoUpload;