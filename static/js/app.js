// State
let selectedFile = null;

document.addEventListener('DOMContentLoaded', () => {
  setupDragAndDrop();
  checkSystemHealth();
});

function checkSystemHealth() {
  fetch('/api/health')
    .then(r => r.json())
    .then(data => {
      const statusText = document.getElementById('statusText');
      if (data.credentials_configured) {
        statusText.textContent = 'Google Cloud APIs Active';
      } else {
        statusText.textContent = 'Demo Mode (No Credentials)';
      }
    })
    .catch(() => {
      const statusText = document.getElementById('statusText');
      statusText.textContent = 'Local Server Running';
    });
}

function updateRadioSelection(radio) {
  document.querySelectorAll('.radio-card').forEach(card => {
    card.classList.remove('selected');
  });
  if (radio.checked) {
    radio.closest('.radio-card').classList.add('selected');
  }
}

function setupDragAndDrop() {
  const dropzone = document.getElementById('dropzone');

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
      handleFileSelect(files);
    }
  }, false);
}

function handleFileSelect(files) {
  if (!files || files.length === 0) return;
  const file = files[0];
  selectedFile = file;

  // Sync to hidden input if triggered from drop
  const fileInput = document.getElementById('fileInput');
  const dataTransfer = new DataTransfer();
  dataTransfer.items.add(file);
  fileInput.files = dataTransfer.files;

  // Show preview card
  const previewCard = document.getElementById('filePreviewCard');
  const fileNameText = document.getElementById('fileNameText');
  const fileSizeText = document.getElementById('fileSizeText');
  const thumbImg = document.getElementById('thumbImg');
  const fileIconPdf = document.getElementById('fileIconPdf');

  fileNameText.textContent = file.name;
  fileSizeText.textContent = formatBytes(file.size);

  if (file.type.startsWith('image/')) {
    const reader = new FileReader();
    reader.onload = (e) => {
      thumbImg.src = e.target.result;
      thumbImg.style.display = 'block';
      fileIconPdf.style.display = 'none';
    };
    reader.readAsDataURL(file);
  } else {
    thumbImg.style.display = 'none';
    fileIconPdf.style.display = 'block';
  }

  previewCard.style.display = 'flex';
}

function clearSelectedFile() {
  selectedFile = null;
  const fileInput = document.getElementById('fileInput');
  fileInput.value = '';
  document.getElementById('filePreviewCard').style.display = 'none';
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

async function handleFormSubmit(event) {
  event.preventDefault();

  const fileInput = document.getElementById('fileInput');
  if (!fileInput.files || fileInput.files.length === 0) {
    alert('Please select or upload a blank certificate template file.');
    return;
  }

  const submitBtn = document.getElementById('submitBtn');
  const btnText = document.getElementById('btnText');
  const btnSpinner = document.getElementById('btnSpinner');

  submitBtn.disabled = true;
  btnText.textContent = 'Uploading to Drive & Sheets...';
  btnSpinner.style.display = 'inline-block';

  const form = document.getElementById('activityForm');
  const formData = new FormData(form);

  try {
    const response = await fetch('/api/register', {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (result.success && result.data) {
      showSuccessView(result.data);
    } else {
      alert('Error registering activity: ' + (result.message || 'Unknown error'));
    }
  } catch (error) {
    console.error('Submission failed:', error);
    alert('Failed to connect to server: ' + error.message);
  } finally {
    submitBtn.disabled = false;
    btnText.textContent = 'REGISTER ACTIVITY';
    btnSpinner.style.display = 'none';
  }
}

function showSuccessView(data) {
  const form = document.getElementById('activityForm');
  const successContainer = document.getElementById('successContainer');
  const detailsGrid = document.getElementById('detailsGrid');

  form.style.display = 'none';
  successContainer.style.display = 'block';

  // Build key-value fields
  const fields = [
    { key: 'Activity ID', val: data['Activity ID'], highlight: true },
    { key: 'Template ID', val: data['Template ID'], highlight: true },
    { key: 'Activity Name', val: data['Activity Name'] },
    { key: 'Software', val: data['Software'] },
    { key: 'Organising Project', val: data['Organising Project'] },
    { key: 'Coordinator', val: data['Coordinator'] },
    { key: 'Activity Type', val: data['Activity Type'] },
    { key: 'Certificate Type', val: data['Certificate Type'] },
    { key: 'Duration', val: `${data['Start Date']} to ${data['End Date']}` },
    { key: 'Registered Timestamp', val: data['Registered At'] || 'Just now' }
  ];

  detailsGrid.innerHTML = fields.map(f => `
    <div class="detail-item">
      <span class="detail-key">${f.key}</span>
      <span class="detail-value ${f.highlight ? 'highlight' : ''}">${escapeHtml(f.val)}</span>
    </div>
  `).join('');

  // Handle template preview
  const previewImg = document.getElementById('successPreviewImg');
  const pdfSuccessBadge = document.getElementById('pdfSuccessBadge');
  const pdfFilenameText = document.getElementById('pdfFilenameText');
  const fileUrl = data['LocalFileUrl'];
  const filename = data['Filename'] || 'template';

  const isImage = /\.(png|jpe?g|webp)$/i.test(filename);
  if (isImage && fileUrl) {
    previewImg.src = fileUrl;
    previewImg.style.display = 'block';
    pdfSuccessBadge.style.display = 'none';
  } else {
    previewImg.style.display = 'none';
    pdfSuccessBadge.style.display = 'block';
    pdfFilenameText.textContent = filename;
  }

  // Setup buttons
  const viewFullBtn = document.getElementById('viewFullBtn');
  viewFullBtn.href = fileUrl || '#';

  const downloadBtn = document.getElementById('downloadTemplateBtn');
  downloadBtn.href = fileUrl || '#';
  downloadBtn.setAttribute('download', filename);

  const openDriveBtn = document.getElementById('openDriveBtn');
  if (data['Drive View Link']) {
    openDriveBtn.href = data['Drive View Link'];
    openDriveBtn.style.display = 'inline-flex';
  } else {
    openDriveBtn.style.display = 'none';
  }

  const openSheetBtn = document.getElementById('openSheetBtn');
  if (data['Spreadsheet Link']) {
    openSheetBtn.href = data['Spreadsheet Link'];
  }

  // Scroll to top of card
  document.getElementById('registrationCard').scrollIntoView({ behavior: 'smooth' });
}

function resetToRegistration() {
  const form = document.getElementById('activityForm');
  const successContainer = document.getElementById('successContainer');

  form.reset();
  clearSelectedFile();

  // Reset radio to default
  const defaultRadio = document.querySelector('input[name="certificate_type"][value="Participation"]');
  if (defaultRadio) {
    defaultRadio.checked = true;
    updateRadioSelection(defaultRadio);
  }

  successContainer.style.display = 'none';
  form.style.display = 'block';
}

function switchTab(tab) {
  const tabRegister = document.getElementById('tabRegister');
  const tabRecent = document.getElementById('tabRecent');
  const registrationCard = document.getElementById('registrationCard');
  const recentCard = document.getElementById('recentCard');

  if (tab === 'register') {
    tabRegister.classList.add('active');
    tabRecent.classList.remove('active');
    registrationCard.style.display = 'block';
    recentCard.style.display = 'none';
  } else {
    tabRecent.classList.add('active');
    tabRegister.classList.remove('active');
    registrationCard.style.display = 'none';
    recentCard.style.display = 'block';
    loadRecentActivities();
  }
}

async function loadRecentActivities() {
  const tbody = document.getElementById('recentTableBody');
  tbody.innerHTML = `
    <tr>
      <td colspan="10" style="text-align: center; padding: 2rem; color: #64748b;">
        <span class="spinner" style="border-color: rgba(10,58,96,0.3); border-top-color: #0a3a60; margin-right: 8px;"></span>
        Fetching live records from Google Sheet...
      </td>
    </tr>
  `;

  try {
    const res = await fetch('/api/activities');
    const data = await res.json();

    if (data.activities && data.activities.length > 0) {
      tbody.innerHTML = data.activities.map(item => `
        <tr>
          <td><strong>${escapeHtml(item['Activity ID'] || '-')}</strong></td>
          <td>${escapeHtml(item['Activity Name'] || '-')}</td>
          <td>${escapeHtml(item['Software'] || '-')}</td>
          <td>${escapeHtml(item['Organising Project'] || '-')}</td>
          <td>${escapeHtml(item['Coordinator'] || '-')}</td>
          <td>${escapeHtml(item['Activity Type'] || '-')}</td>
          <td>${escapeHtml((item['Start Date'] || '') + ' - ' + (item['End Date'] || ''))}</td>
          <td><span style="background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem;">${escapeHtml(item['Certificate Type'] || '-')}</span></td>
          <td><code>${escapeHtml(item['Template ID'] || '-')}</code></td>
          <td style="color: #64748b; font-size: 0.8rem;">${escapeHtml(item['Timestamp'] || item['Registered At'] || '-')}</td>
        </tr>
      `).join('');
    } else {
      tbody.innerHTML = `
        <tr>
          <td colspan="10" style="text-align: center; padding: 2rem; color: #64748b;">
            No records found or unable to read sheet directly. Register an activity to add new rows!
          </td>
        </tr>
      `;
    }
  } catch (err) {
    tbody.innerHTML = `
      <tr>
        <td colspan="10" style="text-align: center; padding: 2rem; color: #ef4444;">
          Failed to fetch records: ${err.message}
        </td>
      </tr>
    `;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
