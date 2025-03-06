document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const uploadForm = document.getElementById('upload-form');
    const extractBtn = document.getElementById('extract-btn');
    const fileInfo = document.getElementById('file-info');
    const filename = document.getElementById('filename');
    const filetype = document.getElementById('filetype');
    const filesize = document.getElementById('filesize');
    const loading = document.getElementById('loading');
    const resultContent = document.getElementById('result-content');

    // File drag & drop events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        dropArea.classList.add('active');
    }

    function unhighlight() {
        dropArea.classList.remove('active');
    }

    // Handle file drop
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            updateFileInfo(files[0]);
        }
    }

    // Handle file selection via click
    dropArea.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (fileInput.files.length > 0) {
            updateFileInfo(fileInput.files[0]);
        }
    });

    // Update file information
    function updateFileInfo(file) {
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(2);
        fileInfo.classList.remove('d-none');
        filename.textContent = file.name;
        filetype.textContent = file.type || 'Unknown';
        filesize.textContent = `${fileSizeMB} MB`;
    }

    // Form submission
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!fileInput.files || fileInput.files.length === 0) {
            showAlert('Please select a file first', 'danger');
            return;
        }

        const file = fileInput.files[0];
        const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
        
        if (!allowedTypes.includes(file.type)) {
            showAlert('Unsupported file type. Please upload PDF, PNG, or JPG/JPEG files.', 'danger');
            return;
        }

        // Show loading state
        loading.classList.remove('d-none');
        resultContent.innerHTML = '';
        extractBtn.disabled = true;
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/extract', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'An error occurred during extraction');
            }
            
            displayResults(data);
        } catch (error) {
            console.error('Error:', error);
            showError(error.message);
        } finally {
            loading.classList.add('d-none');
            extractBtn.disabled = false;
        }
    });

    // Display extraction results
    function displayResults(data) {
        if (!data || data.length === 0) {
            showError('No results were returned');
            return;
        }

        // Create results container
        let resultsHtml = '';

        // Add page selector if multiple pages
        if (data.length > 1) {
            resultsHtml += '<div class="page-selector">';
            for (let i = 0; i < data.length; i++) {
                resultsHtml += `<button class="page-btn ${i === 0 ? 'active' : ''}" data-page="${i}">
                                    ${i + 1}
                                </button>`;
            }
            resultsHtml += '</div>';
        }

        // Add page content containers
        for (let i = 0; i < data.length; i++) {
            const page = data[i];
            const docType = page.document_type || 'UNKNOWN';
            const confidence = page.ocr_results?.confidence_score || 0;
            const formattedText = page.formatted_text || {};
            
            resultsHtml += `
                <div class="page-content ${i === 0 ? '' : 'd-none'}" data-page="${i}">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="doc-type ${docType.toLowerCase()}">${docType}</span>
                        <div class="confidence-container" style="width: 150px;">
                            <div class="confidence-text">${(confidence * 100).toFixed(1)}% confidence</div>
                            <div class="confidence-bar">
                                <div class="confidence-value" style="width: ${confidence * 100}%"></div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="result-section">
                        <h6>Document Type</h6>
                        <p>${formattedText.document_type || 'Unknown'}</p>
                    </div>
                    
                    <div class="result-section">
                        <h6>Key Information</h6>
                        <div class="key-info">
                            ${formatKeyInformation(formattedText.key_information)}
                        </div>
                    </div>
                    
                    <div class="result-section">
                        <h6>Categories</h6>
                        <div class="categories">
                            ${formatCategories(formattedText.potential_categories)}
                        </div>
                    </div>
                    
                    <div class="result-section">
                        <h6>Raw JSON</h6>
                        <div class="json-viewer">${formatJson(page)}</div>
                    </div>
                </div>
            `;
        }

        resultContent.innerHTML = resultsHtml;

        // Add page selection functionality
        document.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const pageIndex = this.dataset.page;
                
                // Update active button
                document.querySelectorAll('.page-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');
                
                // Show selected page content
                document.querySelectorAll('.page-content').forEach(content => {
                    content.classList.add('d-none');
                });
                document.querySelector(`.page-content[data-page="${pageIndex}"]`).classList.remove('d-none');
            });
        });
    }

    // Format key information
    function formatKeyInformation(keyInfo) {
        if (!keyInfo || Object.keys(keyInfo).length === 0) {
            return '<p class="text-muted">No key information detected</p>';
        }

        let html = '<table class="table table-sm table-bordered">';
        html += '<thead><tr><th>Field</th><th>Value</th></tr></thead><tbody>';
        
        for (const [key, value] of Object.entries(keyInfo)) {
            const formattedKey = key.replace(/_/g, ' ')
                .split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                .join(' ');
                
            html += `<tr>
                        <td>${formattedKey}</td>
                        <td>${value || 'N/A'}</td>
                    </tr>`;
        }
        
        html += '</tbody></table>';
        return html;
    }

    // Format categories
    function formatCategories(categories) {
        if (!categories || categories.length === 0) {
            return '<p class="text-muted">No categories detected</p>';
        }

        return categories.map(category => 
            `<span class="badge bg-secondary me-2 mb-2">${category}</span>`
        ).join('');
    }

    // Format JSON with syntax highlighting
    function formatJson(json) {
        const jsonString = JSON.stringify(json, null, 2);
        return jsonString.replace(/("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, 
            match => {
                let cls = 'number';
                if (/^"/.test(match)) {
                    if (/:$/.test(match)) {
                        cls = 'key';
                    } else {
                        cls = 'string';
                    }
                } else if (/true|false/.test(match)) {
                    cls = 'boolean';
                } else if (/null/.test(match)) {
                    cls = 'null';
                }
                return `<span class="${cls}">${match}</span>`;
            }
        ).replace(/\n/g, '<br>').replace(/\s{2}/g, '&nbsp;&nbsp;');
    }

    // Show error message
    function showError(message) {
        resultContent.innerHTML = `
            <div class="alert alert-danger">
                <strong>Error:</strong> ${message}
            </div>
        `;
    }

    // Show alert message
    function showAlert(message, type = 'info') {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        
        resultContent.innerHTML = alertHtml + resultContent.innerHTML;
    }
});