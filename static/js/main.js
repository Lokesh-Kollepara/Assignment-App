/**
 * Main JavaScript for PDF Hint Chatbot Landing Page
 */

let currentUploadType = null;

// DOM Elements
const modal = document.getElementById('upload-modal');
const modalTitle = document.getElementById('modal-title');
const uploadArea = document.getElementById('upload-area');
const uploadProgress = document.getElementById('upload-progress');
const uploadSuccess = document.getElementById('upload-success');
const fileInput = document.getElementById('file-input');
const progressFill = document.getElementById('progress-fill');
const uploadStatus = document.getElementById('upload-status');
const successMessage = document.getElementById('success-message');

/**
 * Show upload modal for the specified type
 */
function showUploadModal(type) {
    currentUploadType = type;

    // Update modal title based on type
    if (type === 'assignment') {
        modalTitle.textContent = 'Upload Assignment';
    } else {
        modalTitle.textContent = 'Upload Class Material';
    }

    // Reset modal state
    resetUpload();

    // Show modal
    modal.classList.add('active');
}

/**
 * Close upload modal
 */
function closeUploadModal() {
    modal.classList.remove('active');
    currentUploadType = null;
    resetUpload();
}

/**
 * Reset upload state
 */
function resetUpload() {
    uploadArea.style.display = 'block';
    uploadProgress.style.display = 'none';
    uploadSuccess.style.display = 'none';
    fileInput.value = '';
    progressFill.style.width = '0%';
}

/**
 * Navigate to chatbot page
 */
function goToChatbot() {
    window.location.href = '/chatbot';
}

/**
 * Handle file selection
 */
function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please select a PDF file.');
        return;
    }

    // Start upload
    uploadFile(file);
}

/**
 * Upload file to server
 */
async function uploadFile(file) {
    // Show progress
    uploadArea.style.display = 'none';
    uploadProgress.style.display = 'block';
    uploadStatus.textContent = 'Uploading...';

    // Determine endpoint based on type
    const endpoint = currentUploadType === 'assignment'
        ? '/api/upload/assignment'
        : '/api/upload/material';

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    try {
        // Simulate progress (since we can't track actual upload progress with fetch easily)
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressFill.style.width = progress + '%';
        }, 200);

        // Make request
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });

        // Clear progress interval
        clearInterval(progressInterval);
        progressFill.style.width = '100%';

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();

        // Show success
        setTimeout(() => {
            uploadProgress.style.display = 'none';
            uploadSuccess.style.display = 'block';
            successMessage.textContent = data.message || `${file.name} uploaded successfully!`;
        }, 500);

    } catch (error) {
        console.error('Upload error:', error);
        uploadProgress.style.display = 'none';
        uploadArea.style.display = 'block';
        alert('Upload failed: ' + error.message);
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // File input change
    fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFileSelect(file);
    });

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');

        const file = e.dataTransfer.files[0];
        handleFileSelect(file);
    });

    // Close modal on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeUploadModal();
        }
    });

    // Close modal on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeUploadModal();
        }
    });
});

console.log('PDF Hint Chatbot - Landing Page Initialized');
