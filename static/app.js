/**
 * NexusAI Studio v6.0 - Master Client Controller
 * Real Google OAuth 2.0 Integration, Multi-User Isolation, CEO Verification, Vision & RAG.
 */

function getOrCreateUserId() {
  let uid = localStorage.getItem('nexus_user_id');
  if (!uid) {
    uid = 'usr_' + Math.random().toString(36).substring(2, 11) + '_' + Date.now().toString(36);
    localStorage.setItem('nexus_user_id', uid);
  }
  return uid;
}

const state = {
  userId: getOrCreateUserId(),
  userName: localStorage.getItem('nexus_user_name') || 'Guest User',
  userEmail: localStorage.getItem('nexus_user_email') || null,
  userRole: localStorage.getItem('nexus_user_role') || 'user',
  userPicture: localStorage.getItem('nexus_user_picture') || null,
  isCeo: localStorage.getItem('nexus_is_ceo') === 'true',
  sessionId: null,
  isProcessing: false,
  isDeepResearchMode: false,
  selectedModel: 'auto',
  attachedDocId: null,
  attachedFilename: null,
  attachedImageMeta: null,
  artifacts: [],
  documents: [],
  memories: [],
  sessions: [],
  googleClientId: null,
  isSpeaking: false,
  isLockedOut: false
};

const elements = {
  // Navigation & Header
  btnToggleSidebar: document.getElementById('btn-toggle-sidebar'),
  historySidebar: document.getElementById('history-sidebar'),
  btnSidebarNew: document.getElementById('btn-sidebar-new'),
  pastSessionsList: document.getElementById('past-sessions-list'),

  btnUserAuth: document.getElementById('btn-user-auth'),
  headerUserName: document.getElementById('header-user-name'),
  headerUserAvatar: document.getElementById('header-user-avatar'),

  btnCeoAccess: document.getElementById('btn-ceo-access'),
  ceoStatusLabel: document.getElementById('ceo-status-label'),
  ceoModal: document.getElementById('ceo-modal'),
  modalHeading: document.getElementById('modal-heading'),
  modalDesc: document.getElementById('modal-desc'),
  btnCloseCeoModal: document.getElementById('btn-close-ceo-modal'),
  btnCancelCeo: document.getElementById('btn-cancel-ceo'),
  btnJoking: document.getElementById('btn-joking'),
  ceoAuthForm: document.getElementById('ceo-auth-form'),
  ceoPasscodeInput: document.getElementById('ceo-passcode-input'),
  ceoAuthMsg: document.getElementById('ceo-auth-msg'),

  // Real Google Sign-In Modal Elements
  authModal: document.getElementById('auth-modal'),
  btnCloseAuthModal: document.getElementById('btn-close-auth-modal'),
  gIdSigninBox: document.getElementById('g_id_signin_box'),
  googleConfigHint: document.getElementById('google-config-hint'),
  btnGuestMode: document.getElementById('btn-guest-mode'),

  selectModel: document.getElementById('select-model'),
  btnToggleResearch: document.getElementById('btn-toggle-research'),
  btnToggleCanvas: document.getElementById('btn-toggle-canvas'),
  canvasCounter: document.getElementById('canvas-counter'),
  btnNewChat: document.getElementById('btn-new-chat'),

  chatFeed: document.getElementById('chat-feed'),
  welcomeHero: document.getElementById('welcome-hero'),
  threadMessages: document.getElementById('thread-messages'),
  starterCards: document.querySelectorAll('.starter-card'),

  chatForm: document.getElementById('chat-form'),
  messageInput: document.getElementById('message-input'),
  btnSendMessage: document.getElementById('btn-send-message'),
  fileInput: document.getElementById('file-input'),
  btnUploadFile: document.getElementById('btn-upload-file'),
  btnVoiceInput: document.getElementById('btn-voice-input'),
  attachmentChip: document.getElementById('attachment-chip'),
  attachmentIcon: document.getElementById('attachment-icon'),
  attachmentName: document.getElementById('attachment-name'),
  btnRemoveAttachment: document.getElementById('btn-remove-attachment'),

  workspaceCanvas: document.getElementById('workspace-canvas'),
  canvasNavBtns: document.querySelectorAll('.canvas-nav-btn'),
  canvasViewContents: document.querySelectorAll('.canvas-view-content'),
  btnCloseCanvas: document.getElementById('btn-close-canvas'),

  plotsGallery: document.getElementById('plots-gallery'),
  dossierContentArea: document.getElementById('dossier-content-area'),
  uploadedDocsList: document.getElementById('uploaded-docs-list'),
  uploadDropzone: document.getElementById('upload-dropzone'),

  tabBadgePlots: document.getElementById('tab-badge-plots'),
  tabBadgeFiles: document.getElementById('tab-badge-files'),
  tabBadgeMemory: document.getElementById('tab-badge-memory'),
  tabBtnUsers: document.getElementById('tab-btn-users'),
  usersDirectoryTable: document.getElementById('users-directory-table'),

  sandboxEditor: document.getElementById('sandbox-editor'),
  consoleOutput: document.getElementById('console-output'),
  btnRunSandbox: document.getElementById('btn-run-sandbox'),

  memoryAddForm: document.getElementById('memory-add-form'),
  memKeyInput: document.getElementById('mem-key-input'),
  memValInput: document.getElementById('mem-val-input'),
  memCatInput: document.getElementById('mem-cat-input'),
  memoryCardsContainer: document.getElementById('memory-cards-container')
};

// Initialize Application
async function init() {
  updateUserUI();
  updateCeoUI();
  setupEventListeners();
  await fetchAuthConfig();
  await loadSessionsList();
  await loadMemories();
  await loadDocuments();
}

function updateUserUI() {
  if (state.userEmail) {
    elements.headerUserName.textContent = state.userName.split(' ')[0] || 'User';
    if (state.userPicture) {
      elements.headerUserAvatar.innerHTML = `<img src="${state.userPicture}" style="width:18px;height:18px;border-radius:50%;" alt="avatar" />`;
    } else {
      elements.headerUserAvatar.textContent = state.userName.charAt(0).toUpperCase() || '👤';
    }
    elements.btnUserAuth.title = `Signed in as ${state.userName} (${state.userEmail})`;
  } else {
    elements.headerUserName.textContent = 'Sign In';
    elements.headerUserAvatar.textContent = '👤';
    elements.btnUserAuth.title = 'Sign In with Google';
  }
}

function updateCeoUI() {
  if (state.isCeo) {
    elements.btnCeoAccess.classList.add('authenticated');
    elements.ceoStatusLabel.textContent = '👑 Boss (CEO Hammad)';
    elements.btnCeoAccess.title = 'Authenticated as Founder & CEO Mr. Hammadullah Khalid';
    if (elements.tabBtnUsers) elements.tabBtnUsers.style.display = 'inline-flex';
    loadAdminUsersRoster();
  } else {
    elements.btnCeoAccess.classList.remove('authenticated');
    elements.ceoStatusLabel.textContent = 'CEO Access';
    elements.btnCeoAccess.title = 'CEO Executive Authentication';
    if (elements.tabBtnUsers) elements.tabBtnUsers.style.display = 'none';
  }
}

// Fetch Google OAuth Config & Render Official Google Button
async function fetchAuthConfig() {
  try {
    const res = await fetch('/api/auth/config');
    const data = await res.json();
    state.googleClientId = data.google_client_id;

    if (state.googleClientId && window.google && window.google.accounts) {
      google.accounts.id.initialize({
        client_id: state.googleClientId,
        callback: handleGoogleAuthCredential
      });

      google.accounts.id.renderButton(
        elements.gIdSigninBox,
        { theme: 'filled_black', size: 'large', type: 'standard', shape: 'pill', text: 'continue_with' }
      );
      elements.googleConfigHint.classList.add('hidden');
    } else {
      elements.googleConfigHint.classList.remove('hidden');
    }
  } catch (err) {
    console.error('Error loading auth config:', err);
  }
}

// Handle Real Google OAuth ID Token
async function handleGoogleAuthCredential(response) {
  if (!response || !response.credential) return;

  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential: response.credential })
    });

    const data = await res.json();
    if (res.ok && data.user) {
      saveUserSession(data.user, data.picture);
      elements.authModal.classList.add('hidden');
      alert(`Welcome, ${data.user.name}! Successfully signed in with Google.`);
    } else {
      alert(data.detail || 'Google sign-in failed.');
    }
  } catch (err) {
    console.error('Google Auth Error:', err);
    alert('Authentication error: ' + err.message);
  }
}

function saveUserSession(user, picture = null) {
  state.userId = user.user_id;
  state.userName = user.name;
  state.userEmail = user.email;
  state.userRole = user.role;
  state.userPicture = picture;

  localStorage.setItem('nexus_user_id', user.user_id);
  localStorage.setItem('nexus_user_name', user.name);
  localStorage.setItem('nexus_user_email', user.email);
  localStorage.setItem('nexus_user_role', user.role);
  if (picture) localStorage.setItem('nexus_user_picture', picture);

  if (user.role === 'ceo') {
    state.isCeo = true;
    localStorage.setItem('nexus_is_ceo', 'true');
  }

  updateUserUI();
  updateCeoUI();
  loadSessionsList();
  loadMemories();
  loadDocuments();
}

function triggerCeoLockoutModal(isMandatory = false) {
  state.isLockedOut = isMandatory;
  elements.ceoAuthMsg.classList.add('hidden');
  elements.btnJoking.classList.add('hidden');
  elements.ceoPasscodeInput.value = '';
  
  if (isMandatory) {
    elements.btnCloseCeoModal.style.display = 'none';
    elements.btnCancelCeo.style.display = 'none';
    elements.modalHeading.textContent = '👑 Executive Security Lockout';
    elements.modalDesc.innerHTML = 'You have claimed the identity of Founder & CEO <strong>Mr. Hammadullah Khalid</strong>. This identity requires passcode verification.';
  } else {
    elements.btnCloseCeoModal.style.display = 'block';
    elements.btnCancelCeo.style.display = 'block';
    elements.modalHeading.textContent = 'Executive Security Protocol';
    elements.modalDesc.innerHTML = 'Enter the CEO executive passcode to unlock <strong>VIP Master Mode</strong> with highest priority compute.';
  }

  elements.ceoModal.classList.remove('hidden');
  elements.ceoPasscodeInput.focus();
}

function setupEventListeners() {
  // Sidebar Toggle
  elements.btnToggleSidebar.addEventListener('click', () => {
    elements.historySidebar.classList.toggle('collapsed');
  });

  elements.btnSidebarNew.addEventListener('click', startNewThread);
  elements.btnNewChat.addEventListener('click', startNewThread);

  // User Auth Modal
  elements.btnUserAuth.addEventListener('click', () => {
    if (state.userEmail) {
      if (confirm(`Signed in as ${state.userName} (${state.userEmail}). Would you like to sign out?`)) {
        localStorage.removeItem('nexus_user_email');
        localStorage.removeItem('nexus_user_name');
        localStorage.removeItem('nexus_user_picture');
        state.userEmail = null;
        state.userPicture = null;
        state.userName = 'Guest User';
        updateUserUI();
      }
    } else {
      elements.authModal.classList.remove('hidden');
    }
  });

  elements.btnCloseAuthModal.addEventListener('click', () => elements.authModal.classList.add('hidden'));
  elements.btnGuestMode.addEventListener('click', () => elements.authModal.classList.add('hidden'));

  // CEO Access Button Click
  elements.btnCeoAccess.addEventListener('click', () => {
    if (state.isCeo) {
      if (confirm('You are currently authenticated as CEO Mr. Hammadullah Khalid. Would you like to log out of CEO Mode?')) {
        state.isCeo = false;
        localStorage.setItem('nexus_is_ceo', 'false');
        updateCeoUI();
      }
    } else {
      triggerCeoLockoutModal(false);
    }
  });

  elements.btnCloseCeoModal.addEventListener('click', () => {
    if (!state.isLockedOut) elements.ceoModal.classList.add('hidden');
  });

  elements.btnCancelCeo.addEventListener('click', () => {
    if (!state.isLockedOut) elements.ceoModal.classList.add('hidden');
  });

  elements.btnJoking.addEventListener('click', () => {
    elements.ceoModal.classList.add('hidden');
    state.isLockedOut = false;
    state.isCeo = false;
    localStorage.setItem('nexus_is_ceo', 'false');
    updateCeoUI();
  });

  elements.ceoAuthForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const passcode = elements.ceoPasscodeInput.value.trim();
    if (!passcode) return;

    try {
      const res = await fetch('/api/auth/ceo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ passcode: passcode })
      });

      const data = await res.json();
      if (res.ok && data.authenticated) {
        state.isCeo = true;
        state.isLockedOut = false;
        localStorage.setItem('nexus_is_ceo', 'true');
        updateCeoUI();

        elements.ceoAuthMsg.className = 'auth-msg success';
        elements.ceoAuthMsg.textContent = '✓ Verified: Welcome Boss Mr. Hammadullah Khalid!';
        elements.ceoAuthMsg.classList.remove('hidden');
        elements.btnJoking.classList.add('hidden');

        setTimeout(() => {
          elements.ceoModal.classList.add('hidden');
          handleAgentQuery('I am authenticated as CEO Mr. Hammadullah Khalid.');
        }, 900);
      } else {
        elements.ceoAuthMsg.className = 'auth-msg error';
        elements.ceoAuthMsg.textContent = '❌ Wrong Passcode: You are not recognized as CEO.';
        elements.ceoAuthMsg.classList.remove('hidden');
        elements.btnJoking.classList.remove('hidden');
      }
    } catch (err) {
      elements.ceoAuthMsg.className = 'auth-msg error';
      elements.ceoAuthMsg.textContent = '❌ Authentication Error: ' + err.message;
      elements.ceoAuthMsg.classList.remove('hidden');
      elements.btnJoking.classList.remove('hidden');
    }
  });

  // Model Selector
  elements.selectModel.addEventListener('change', (e) => {
    state.selectedModel = e.target.value;
  });

  // Deep Research Mode Toggle
  elements.btnToggleResearch.addEventListener('click', () => {
    state.isDeepResearchMode = !state.isDeepResearchMode;
    if (state.isDeepResearchMode) {
      elements.btnToggleResearch.classList.add('active');
      elements.messageInput.placeholder = "🔎 Deep Research Mode: Enter topic to compile multi-source dossier...";
      if (!elements.messageInput.value.startsWith('Deep research on ')) {
        elements.messageInput.value = 'Deep research on ' + elements.messageInput.value;
      }
    } else {
      elements.btnToggleResearch.classList.remove('active');
      elements.messageInput.placeholder = "Ask anything, upload images/PDFs, run Python code, plot charts, search live web...";
      elements.messageInput.value = elements.messageInput.value.replace(/^Deep research on\s*/i, '');
    }
    elements.messageInput.focus();
  });

  // Canvas Drawer Toggle
  elements.btnToggleCanvas.addEventListener('click', () => {
    elements.workspaceCanvas.classList.toggle('closed');
  });

  elements.btnCloseCanvas.addEventListener('click', () => {
    elements.workspaceCanvas.classList.add('closed');
  });

  // Canvas Tabs
  elements.canvasNavBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      elements.canvasNavBtns.forEach(b => b.classList.remove('active'));
      elements.canvasViewContents.forEach(v => v.classList.remove('active'));

      btn.classList.add('active');
      const targetId = btn.getAttribute('data-tab');
      const targetView = document.getElementById(targetId);
      if (targetView) targetView.classList.add('active');
    });
  });

  // File Upload Attachments
  elements.btnUploadFile.addEventListener('click', () => elements.fileInput.click());
  elements.uploadDropzone.addEventListener('click', () => elements.fileInput.click());

  elements.fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) await handleFileUpload(file);
  });

  // Dropzone drag-and-drop
  elements.uploadDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadDropzone.style.borderColor = '#38bdf8';
  });

  elements.uploadDropzone.addEventListener('dragleave', () => {
    elements.uploadDropzone.style.borderColor = '';
  });

  elements.uploadDropzone.addEventListener('drop', async (e) => {
    e.preventDefault();
    elements.uploadDropzone.style.borderColor = '';
    if (e.dataTransfer.files.length > 0) {
      await handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  // Remove Attachment Pill
  elements.btnRemoveAttachment.addEventListener('click', () => {
    state.attachedDocId = null;
    state.attachedFilename = null;
    state.attachedImageMeta = null;
    elements.attachmentChip.classList.add('hidden');
  });

  // Voice Input (Web Speech API)
  if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    elements.btnVoiceInput.addEventListener('click', () => {
      elements.btnVoiceInput.classList.add('recording');
      recognition.start();
    });

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      elements.messageInput.value = transcript;
      elements.btnVoiceInput.classList.remove('recording');
      elements.messageInput.focus();
    };

    recognition.onerror = () => elements.btnVoiceInput.classList.remove('recording');
    recognition.onend = () => elements.btnVoiceInput.classList.remove('recording');
  }

  // Capability Starter Cards
  elements.starterCards.forEach(card => {
    card.addEventListener('click', () => {
      const prompt = card.getAttribute('data-prompt');
      if (prompt) handleAgentQuery(prompt);
    });
  });

  // Auto-expanding textarea & Enter handling
  elements.messageInput.addEventListener('input', () => {
    elements.messageInput.style.height = 'auto';
    elements.messageInput.style.height = `${Math.min(elements.messageInput.scrollHeight, 140)}px`;
    if (elements.messageInput.value.trim().length > 0) {
      elements.btnSendMessage.classList.add('active');
    } else {
      elements.btnSendMessage.classList.remove('active');
    }
  });

  elements.messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      elements.chatForm.dispatchEvent(new Event('submit'));
    }
  });

  // Chat Form Submit
  elements.chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = elements.messageInput.value.trim();
    if (query && !state.isProcessing) {
      handleAgentQuery(query);
    }
  });

  // Live Sandbox Run Code Button
  elements.btnRunSandbox.addEventListener('click', async () => {
    const code = elements.sandboxEditor.value.trim();
    if (!code) return;
    elements.btnRunSandbox.disabled = true;
    elements.btnRunSandbox.textContent = 'Running...';
    elements.consoleOutput.textContent = 'Executing Python code...';

    try {
      const res = await fetch('/api/sandbox/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code })
      });
      const data = await res.json();
      elements.consoleOutput.textContent = data.output || '[Finished with no output]';

      if (data.images && data.images.length > 0) {
        data.images.forEach(img => addArtifact(img, 'Interactive Sandbox Plot'));
        openCanvasTab('view-artifacts');
      }
    } catch (err) {
      elements.consoleOutput.textContent = 'Execution error: ' + err.message;
    } finally {
      elements.btnRunSandbox.disabled = false;
      elements.btnRunSandbox.textContent = '▶ Run Code';
    }
  });

  // Add Memory Form
  elements.memoryAddForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const key = elements.memKeyInput.value.trim();
    const val = elements.memValInput.value.trim();
    const cat = elements.memCatInput.value.trim() || 'general';

    if (key && val) {
      await fetch('/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: state.userId, key, value: val, category: cat })
      });
      elements.memKeyInput.value = '';
      elements.memValInput.value = '';
      await loadMemories();
    }
  });
}

function startNewThread() {
  state.sessionId = null;
  state.attachedDocId = null;
  state.attachedImageMeta = null;
  elements.attachmentChip.classList.add('hidden');
  elements.threadMessages.innerHTML = '';
  elements.welcomeHero.classList.remove('hidden');
  elements.messageInput.value = '';
  elements.messageInput.style.height = 'auto';
  elements.btnSendMessage.classList.remove('active');
  elements.messageInput.focus();
}

function openCanvasTab(tabId) {
  elements.canvasNavBtns.forEach(b => {
    if (b.getAttribute('data-tab') === tabId) b.classList.add('active');
    else b.classList.remove('active');
  });
  elements.canvasViewContents.forEach(v => {
    if (v.id === tabId) v.classList.add('active');
    else v.classList.remove('active');
  });
  elements.workspaceCanvas.classList.remove('closed');
}

// Load Past Sessions for This User
async function loadSessionsList() {
  try {
    const res = await fetch(`/api/sessions?user_id=${encodeURIComponent(state.userId)}`);
    const data = await res.json();
    state.sessions = data.sessions || [];
    renderSessionsList();
  } catch (err) {
    console.error('Error loading sessions:', err);
  }
}

function renderSessionsList() {
  elements.pastSessionsList.innerHTML = '';
  if (state.sessions.length === 0) {
    elements.pastSessionsList.innerHTML = '<div class="empty-sessions-hint">No past conversations</div>';
    return;
  }

  state.sessions.forEach(sess => {
    const item = document.createElement('div');
    item.className = `session-item ${state.sessionId === sess.session_id ? 'active' : ''}`;
    item.innerHTML = `
      <span class="session-title-text" title="${escapeHtml(sess.title)}">${escapeHtml(sess.title)}</span>
      <button class="btn-del-session" title="Delete Conversation">✕</button>
    `;

    item.querySelector('.session-title-text').addEventListener('click', () => {
      loadSessionMessages(sess.session_id);
    });

    item.querySelector('.btn-del-session').addEventListener('click', async (e) => {
      e.stopPropagation();
      await fetch(`/api/sessions/${encodeURIComponent(sess.session_id)}?user_id=${encodeURIComponent(state.userId)}`, { method: 'DELETE' });
      if (state.sessionId === sess.session_id) startNewThread();
      await loadSessionsList();
    });

    elements.pastSessionsList.appendChild(item);
  });
}

// Load previous session messages
async function loadSessionMessages(sessionId) {
  try {
    const res = await fetch(`/api/sessions/${encodeURIComponent(sessionId)}?user_id=${encodeURIComponent(state.userId)}`);
    if (!res.ok) return;
    const data = await res.json();
    
    state.sessionId = data.session_id;
    elements.welcomeHero.classList.add('hidden');
    elements.threadMessages.innerHTML = '';

    const messages = data.messages || [];
    messages.forEach(m => {
      if (m.role === 'user') {
        const userRow = document.createElement('div');
        userRow.className = 'user-msg-row';
        userRow.innerHTML = `<div class="user-msg-bubble">${escapeHtml(m.content)}</div>`;
        elements.threadMessages.appendChild(userRow);
      } else {
        const agentRow = document.createElement('div');
        agentRow.className = 'agent-msg-row';
        agentRow.innerHTML = `
          <div class="agent-header">
            <div class="agent-spark">✦</div>
            <span class="agent-title">NexusAI Autonomous OS</span>
            <span class="agent-tag">NexusAI Core</span>
          </div>
          <div class="agent-prose">
            ${formatMarkdown(m.content, m.sources || [])}
          </div>
          <div class="agent-action-bar">
            <button class="btn-msg-action btn-copy" data-text="${escapeHtml(m.content)}" title="Copy text">
              <span>📋 Copy</span>
            </button>
            <button class="btn-msg-action btn-tts" title="Read Aloud with Voice">
              <span>🔊 Read Aloud</span>
            </button>
          </div>
        `;

        agentRow.querySelector('.btn-copy').addEventListener('click', () => {
          navigator.clipboard.writeText(m.content);
        });
        agentRow.querySelector('.btn-tts').addEventListener('click', () => {
          speakText(m.content);
        });

        elements.threadMessages.appendChild(agentRow);
      }
    });

    renderSessionsList();
    scrollToBottom();
  } catch (err) {
    console.error('Error loading session messages:', err);
  }
}

// Handle File Upload
async function handleFileUpload(file) {
  if (!file) return;

  const isImage = file.type.startsWith('image/') || /\.(png|jpe?g|webp|bmp|gif)$/i.test(file.name);
  const endpoint = isImage ? '/api/upload/image' : '/api/upload';

  elements.attachmentName.textContent = `Uploading ${file.name}...`;
  elements.attachmentChip.classList.remove('hidden');
  elements.btnUploadFile.classList.add('recording');

  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', state.userId);

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(errData.detail || 'Upload failed');
    }

    const data = await res.json();

    if (isImage && data.image) {
      state.attachedImageMeta = data.image;
      state.attachedDocId = null;
      elements.attachmentIcon.textContent = '🖼️';
      elements.attachmentName.textContent = `${file.name} (${data.image.width}×${data.image.height}px)`;
      
      if (!elements.messageInput.value.trim()) {
        elements.messageInput.value = 'Describe what is happening in this image in detail.';
        elements.btnSendMessage.classList.add('active');
      }
      addArtifact(data.image.data_uri, `Uploaded Image: ${file.name}`);
      openCanvasTab('view-artifacts');
    } else {
      state.attachedDocId = data.file_id;
      state.attachedFilename = data.filename;
      state.attachedImageMeta = null;
      elements.attachmentIcon.textContent = '📄';
      elements.attachmentName.textContent = `${data.filename} (${data.metadata.word_count || 0} words)`;
      
      if (!elements.messageInput.value.trim()) {
        elements.messageInput.value = 'Analyze this uploaded document and summarize the key points and data tables.';
        elements.btnSendMessage.classList.add('active');
      }
      await loadDocuments();
      openCanvasTab('view-rag');
    }

    elements.attachmentChip.classList.remove('hidden');
    elements.messageInput.focus();
  } catch (err) {
    console.error('File upload error:', err);
    alert('Upload failed: ' + err.message);
    elements.attachmentChip.classList.add('hidden');
  } finally {
    elements.btnUploadFile.classList.remove('recording');
    elements.fileInput.value = '';
  }
}

// Load Documents
async function loadDocuments() {
  try {
    const res = await fetch(`/api/documents?user_id=${encodeURIComponent(state.userId)}`);
    const data = await res.json();
    state.documents = data.documents || [];
    elements.tabBadgeFiles.textContent = state.documents.length;
    renderDocumentsList();
  } catch (err) {
    console.error('Error loading documents:', err);
  }
}

function renderDocumentsList() {
  elements.uploadedDocsList.innerHTML = '';
  if (state.documents.length === 0) {
    elements.uploadedDocsList.innerHTML = '<div style="font-size:0.75rem;color:#64748b;text-align:center;padding:1rem;">No files uploaded to your private RAG index yet.</div>';
    return;
  }

  state.documents.forEach(doc => {
    const card = document.createElement('div');
    card.className = 'doc-card';
    card.innerHTML = `
      <div>
        <div class="doc-name">📄 ${escapeHtml(doc.doc_name)}</div>
        <div class="doc-info">${escapeHtml(doc.metadata.file_type || 'file')} · ${doc.metadata.word_count || 0} words</div>
      </div>
      <button class="btn-del" title="Remove Document">✕</button>
    `;
    card.querySelector('.btn-del').addEventListener('click', async () => {
      await fetch(`/api/documents/${encodeURIComponent(doc.doc_id)}`, { method: 'DELETE' });
      await loadDocuments();
    });
    elements.uploadedDocsList.appendChild(card);
  });
}

// Load Memories
async function loadMemories() {
  try {
    const res = await fetch(`/api/memory?user_id=${encodeURIComponent(state.userId)}`);
    const data = await res.json();
    state.memories = data.memories || [];
    elements.tabBadgeMemory.textContent = state.memories.length;
    renderMemories();
  } catch (err) {
    console.error('Error loading memory:', err);
  }
}

function renderMemories() {
  elements.memoryCardsContainer.innerHTML = '';
  if (state.memories.length === 0) {
    elements.memoryCardsContainer.innerHTML = '<div style="font-size:0.75rem;color:#64748b;text-align:center;padding:1rem;">No facts in your private memory yet.</div>';
    return;
  }

  state.memories.forEach(item => {
    const card = document.createElement('div');
    card.className = 'mem-item';
    card.innerHTML = `
      <div>
        <div class="mem-k">${escapeHtml(item.key)} <span style="font-size:0.625rem;color:#64748b;font-weight:normal;">[${escapeHtml(item.category)}]</span></div>
        <div class="mem-v">${escapeHtml(item.value)}</div>
      </div>
      <button class="btn-del" title="Delete Memory">✕</button>
    `;
    card.querySelector('.btn-del').addEventListener('click', async () => {
      await fetch(`/api/memory/${encodeURIComponent(item.key)}?user_id=${encodeURIComponent(state.userId)}`, { method: 'DELETE' });
      await loadMemories();
    });
    elements.memoryCardsContainer.appendChild(card);
  });
}

// Load Admin Users Roster (CEO CRM)
async function loadAdminUsersRoster() {
  if (!state.isCeo) return;
  try {
    const res = await fetch('/api/admin/users?is_ceo=true');
    if (!res.ok) return;
    const data = await res.json();
    const users = data.users || [];
    
    if (elements.usersDirectoryTable) {
      if (users.length === 0) {
        elements.usersDirectoryTable.innerHTML = '<div style="font-size:0.75rem;color:#64748b;padding:1rem;text-align:center;">No registered users yet.</div>';
        return;
      }

      elements.usersDirectoryTable.innerHTML = `
        <table class="crm-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Auth Type</th>
              <th>Role</th>
              <th>Chats</th>
              <th>Joined</th>
            </tr>
          </thead>
          <tbody>
            ${users.map(u => `
              <tr>
                <td style="font-weight:700;color:#fff;">${escapeHtml(u.name)}</td>
                <td style="font-family:monospace;color:#93c5fd;">${escapeHtml(u.email)}</td>
                <td><span style="font-size:0.6875rem;color:${u.auth_provider==='google'?'#38bdf8':'#cbd5e1'};">${escapeHtml(u.auth_provider.toUpperCase())}</span></td>
                <td><span style="font-size:0.625rem;padding:0.1rem 0.35rem;border-radius:4px;background:${u.role==='ceo'?'rgba(229,184,105,0.2)':'#1e2233'};color:${u.role==='ceo'?'#e5b869':'#cbd5e1'};font-weight:700;">${escapeHtml(u.role.toUpperCase())}</span></td>
                <td style="font-weight:700;">${u.total_chats || 0}</td>
                <td style="color:#64748b;font-size:0.6875rem;">${new Date(u.created_at * 1000).toLocaleDateString()}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    }
  } catch (err) {
    console.error('Error loading CRM users:', err);
  }
}

// Add Artifact
function addArtifact(imgDataUrl, title = 'Visual Plot') {
  const empty = elements.plotsGallery.querySelector('.canvas-empty-state');
  if (empty) empty.remove();

  state.artifacts.push(imgDataUrl);
  elements.tabBadgePlots.textContent = state.artifacts.length;
  elements.canvasCounter.textContent = state.artifacts.length;

  const card = document.createElement('div');
  card.className = 'chat-chart-card';
  card.innerHTML = `
    <div style="font-size:0.75rem;font-weight:700;color:#fff;margin-bottom:0.5rem;width:100%;display:flex;justify-content:space-between;align-items:center;">
      <span>${escapeHtml(title)}</span>
      <a href="${imgDataUrl}" download="nexus_visual_${Date.now()}.png" style="font-size:0.6875rem;color:#38bdf8;text-decoration:none;font-weight:700;">Download PNG ⬇</a>
    </div>
    <img src="${imgDataUrl}" class="chat-chart-img" alt="Visual Artifact" />
  `;
  elements.plotsGallery.prepend(card);
}

// Render Dossier Tab
function renderDossierTab(dossierData) {
  elements.dossierContentArea.innerHTML = `
    <div style="background:#11131c;border:1px solid #2c3248;border-radius:12px;padding:1.25rem;display:flex;flex-direction:column;gap:0.875rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #202434;padding-bottom:0.75rem;">
        <div>
          <span style="font-size:0.6875rem;font-weight:800;color:#e5b869;text-transform:uppercase;">Verified Intelligence Dossier</span>
          <h2 style="font-size:1.15rem;font-weight:800;color:#fff;margin-top:0.25rem;">${escapeHtml(dossierData.topic)}</h2>
        </div>
        <button id="btn-export-dossier" style="background:#1e2233;border:1px solid #2c3248;color:#e5b869;font-size:0.75rem;font-weight:700;padding:0.4rem 0.75rem;border-radius:6px;cursor:pointer;">Export Report ⬇</button>
      </div>

      <div style="font-size:0.75rem;color:#94a3b8;display:flex;gap:0.75rem;">
        <span>🔍 ${dossierData.sources_investigated_count} Sources Investigated</span>
        <span>⏱️ ${(dossierData.investigation_time_ms / 1000).toFixed(2)}s Research Latency</span>
      </div>

      <div class="agent-prose" style="margin-top:0.5rem;">
        ${formatMarkdown(dossierData.dossier_markdown, dossierData.sources)}
      </div>
    </div>
  `;

  document.getElementById('btn-export-dossier').addEventListener('click', () => {
    const blob = new Blob([dossierData.dossier_markdown], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `NexusAI_Research_Dossier_${Date.now()}.md`;
    a.click();
  });

  openCanvasTab('view-dossier');
}

// Text-to-Speech (TTS)
function speakText(text) {
  if (!('speechSynthesis' in window)) return;

  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
    state.isSpeaking = false;
    document.querySelectorAll('.btn-tts').forEach(b => b.classList.remove('speaking'));
    return;
  }

  const clean = text.replace(/<[^>]+>/g, '').replace(/\[\d+\]/g, '').slice(0, 600);
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.05;
  utterance.pitch = 1.0;

  utterance.onstart = () => state.isSpeaking = true;
  utterance.onend = () => {
    state.isSpeaking = false;
    document.querySelectorAll('.btn-tts').forEach(b => b.classList.remove('speaking'));
  };

  window.speechSynthesis.speak(utterance);
}

// Main Agent Execution Flow
async function handleAgentQuery(query) {
  state.isProcessing = true;

  elements.welcomeHero.classList.add('hidden');
  elements.messageInput.value = '';
  elements.messageInput.style.height = 'auto';
  elements.btnSendMessage.classList.remove('active');

  const userRow = document.createElement('div');
  userRow.className = 'user-msg-row';
  userRow.innerHTML = `<div class="user-msg-bubble">${escapeHtml(query)}</div>`;
  elements.threadMessages.appendChild(userRow);

  const msgId = `msg-${Date.now()}`;
  const agentRow = document.createElement('div');
  agentRow.className = 'agent-msg-row';
  agentRow.id = msgId;

  agentRow.innerHTML = `
    <div class="agent-header">
      <div class="agent-spark">✦</div>
      <span class="agent-title">NexusAI Autonomous OS</span>
      <span class="agent-tag" id="${msgId}-tag">ReAct Planning...</span>
    </div>

    <!-- Active Tool Execution Card -->
    <div class="react-trace-box" id="${msgId}-trace">
      <div class="trace-top">
        <div style="display:flex;align-items:center;gap:0.5rem;">
          <div style="width:12px;height:12px;border:2px solid rgba(147,197,253,0.3);border-top-color:#93c5fd;border-radius:50%;animation:spin 0.8s linear infinite;"></div>
          <span id="${msgId}-status-text">Autonomous ReAct planning & tool selection...</span>
        </div>
      </div>
    </div>

    <div id="${msgId}-content"></div>
  `;

  elements.threadMessages.appendChild(agentRow);
  scrollToBottom();

  try {
    const res = await fetch('/api/agent/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        user_id: state.userId,
        is_ceo: state.isCeo,
        session_id: state.sessionId,
        has_attachments: Boolean(state.attachedDocId),
        attached_doc_id: state.attachedDocId,
        has_image: Boolean(state.attachedImageMeta),
        image_metadata: state.attachedImageMeta,
        selected_model: state.selectedModel
      })
    });

    const rawText = await res.text();
    let data;
    try {
      data = JSON.parse(rawText);
    } catch (e) {
      throw new Error(`Server error: ${rawText.slice(0, 150)}`);
    }

    if (!res.ok) {
      throw new Error(data.detail || `Server error (${res.status})`);
    }

    if (data.trigger_ceo_lockout) {
      triggerCeoLockoutModal(true);
    }

    state.sessionId = data.session_id;

    renderAgentResponse(msgId, data);
    await loadSessionsList();
    await loadMemories();
  } catch (err) {
    console.error('Agent run error:', err);
    const trace = document.getElementById(`${msgId}-trace`);
    if (trace) trace.remove();
    const content = document.getElementById(`${msgId}-content`);
    if (content) {
      content.innerHTML = `<div style="color:#f87171;font-size:0.875rem;">Execution error: ${err.message}</div>`;
    }
  } finally {
    state.isProcessing = false;
    scrollToBottom();
  }
}

// Render Agent Response
function renderAgentResponse(msgId, data) {
  const tagBadge = document.getElementById(`${msgId}-tag`);
  if (tagBadge) {
    tagBadge.textContent = data.engine_name || data.model_used || 'NexusAI Core';
  }

  const traceBox = document.getElementById(`${msgId}-trace`);
  const contentBox = document.getElementById(`${msgId}-content`);
  if (!contentBox) return;

  if (data.tool_steps && data.tool_steps.length > 0) {
    traceBox.innerHTML = `
      <div class="trace-top">
        <span>⚡ ReAct Autonomous Tools Executed (${data.tool_steps.length})</span>
        <span style="font-size:0.6875rem;color:#848c9f;">${(data.latency_ms / 1000).toFixed(2)}s</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:0.375rem;margin-top:0.375rem;">
        ${data.tool_steps.map(step => `
          <div class="trace-step-item">
            <strong style="color:#e5b869;">Tool: ${escapeHtml(step.tool)}</strong> · Action: ${escapeHtml(step.action)}
            <div style="color:#94a3b8;margin-top:0.2rem;font-size:0.6875rem;">Output: ${escapeHtml(step.output.slice(0, 140))}${step.output.length > 140 ? '...' : ''}</div>
          </div>
        `).join('')}
      </div>
    `;

    const pythonStep = data.tool_steps.find(s => s.tool === 'code_sandbox');
    if (pythonStep && pythonStep.input) {
      elements.sandboxEditor.value = pythonStep.input;
      elements.consoleOutput.textContent = pythonStep.output;
    }
  } else {
    if (traceBox) traceBox.remove();
  }

  let html = '';

  if (data.images && data.images.length > 0) {
    data.images.forEach(imgData => {
      html += `
        <div class="chat-chart-card">
          <img src="${imgData}" class="chat-chart-img" alt="Visual Plot" />
        </div>
      `;
      addArtifact(imgData, `Plot from "${data.query.slice(0, 30)}..."`);
    });
    openCanvasTab('view-artifacts');
  }

  if (data.dossier_data && data.dossier_data.dossier_markdown) {
    renderDossierTab(data.dossier_data);
  }

  html += `
    <div class="agent-prose">
      ${formatMarkdown(data.answer, data.sources)}
    </div>
  `;

  html += `
    <div class="agent-action-bar">
      <button class="btn-msg-action btn-copy" data-text="${escapeHtml(data.answer)}" title="Copy text">
        <span>📋 Copy</span>
      </button>
      <button class="btn-msg-action btn-tts" data-speech="${escapeHtml(data.answer)}" title="Read Aloud with Voice">
        <span>🔊 Read Aloud</span>
      </button>
    </div>
  `;

  contentBox.innerHTML = html;

  const ttsBtn = contentBox.querySelector('.btn-tts');
  if (ttsBtn) {
    ttsBtn.addEventListener('click', () => {
      ttsBtn.classList.toggle('speaking');
      speakText(data.answer);
    });
  }

  const copyBtn = contentBox.querySelector('.btn-copy');
  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(data.answer);
      copyBtn.innerHTML = `<span>✓ Copied!</span>`;
      setTimeout(() => copyBtn.innerHTML = `<span>📋 Copy</span>`, 2000);
    });
  }

  scrollToBottom();
}

function formatMarkdown(md, sources) {
  if (!md) return '';
  let text = escapeHtml(md);

  // Parse Mermaid blocks
  text = text.replace(/```mermaid([\s\S]*?)```/g, (match, code) => {
    return `<div style="background:#090a0f;border:1px solid #202434;border-radius:8px;padding:1rem;margin:1rem 0;font-family:monospace;font-size:0.75rem;color:#38bdf8;overflow-x:auto;">
      <div style="font-weight:700;color:#e5b869;margin-bottom:0.5rem;font-size:0.6875rem;text-transform:uppercase;">🎨 Interactive Diagram Code</div>
      <pre>${code.trim()}</pre>
    </div>`;
  });

  // Tables
  text = text.replace(/((?:\|[^\n]+\|\n?)+)/g, (match) => {
    const lines = match.trim().split('\n').filter(l => l.includes('|'));
    if (lines.length < 2) return match;

    let tableHtml = '<div class="table-wrapper"><table class="markdown-table">';
    let isHeader = true;

    lines.forEach((line, idx) => {
      if (line.match(/^\|[\s-:]+\|/)) {
        isHeader = false;
        return;
      }
      const cells = line.split('|').filter((_, cIdx, arr) => cIdx > 0 && cIdx < arr.length - 1);
      if (cells.length === 0) return;

      tableHtml += '<tr>';
      cells.forEach(cell => {
        const cleanCell = cell.trim().replace(/&lt;br&gt;/gi, '<br>');
        if (isHeader && idx === 0) tableHtml += `<th>${cleanCell}</th>`;
        else tableHtml += `<td>${cleanCell}</td>`;
      });
      tableHtml += '</tr>';
    });

    tableHtml += '</table></div>';
    return tableHtml;
  });

  // Headings
  text = text.replace(/###\s+([^\n]+)/g, '<h3>$1</h3>');
  text = text.replace(/##\s+([^\n]+)/g, '<h2>$1</h2>');
  text = text.replace(/#\s+([^\n]+)/g, '<h1>$1</h1>');

  // Bold
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  // Citations
  text = text.replace(/\[(\d+)\]/g, (match, num) => {
    const idx = parseInt(num) - 1;
    const url = sources && sources[idx] ? sources[idx].url : '#';
    return `<a class="citation-link" href="${url}" target="_blank" rel="noopener noreferrer" title="Source #${num}">[${num}]</a>`;
  });

  // Bullet items
  text = text.replace(/^\*\s+([^\n]+)/gm, '<li>$1</li>');
  text = text.replace(/^-\s+([^\n]+)/gm, '<li>$1</li>');
  text = text.replace(/(<li>.+<\/li>)/s, '<ul>$1</ul>');

  const paras = text.split('\n\n').filter(p => p.trim());
  return paras.map(p => {
    if (p.startsWith('<h1>') || p.startsWith('<h2>') || p.startsWith('<h3>') || p.startsWith('<ul>') || p.startsWith('<div class="table-wrapper">') || p.startsWith('<div style="background:#090a0f')) return p;
    return `<p>${p}</p>`;
  }).join('');
}

function scrollToBottom() {
  setTimeout(() => {
    elements.chatFeed.scrollTo({
      top: elements.chatFeed.scrollHeight,
      behavior: 'smooth'
    });
  }, 50);
}

function escapeHtml(text) {
  if (!text) return '';
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

document.addEventListener('DOMContentLoaded', init);
