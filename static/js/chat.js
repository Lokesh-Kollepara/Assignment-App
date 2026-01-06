/**
 * Chat client for PDF Hint Chatbot
 */

class ChatClient {
    constructor() {
        this.sessionId = this.getOrCreateSessionId();
        this.apiUrl = '/api';
        this.messageContainer = document.getElementById('messages');
        this.messageInput = document.getElementById('message-input');
        this.sendButton = document.getElementById('send-button');
        this.clearButton = document.getElementById('clear-button');
        this.statusElement = document.getElementById('status');
        this.sidebar = document.getElementById('sidebar');
        this.toggleSidebarBtn = document.getElementById('toggle-sidebar');
        this.questionsList = document.getElementById('questions-list');

        this.initializeEventListeners();
        this.autoResizeTextarea();
        this.loadAssignmentQuestions();
    }

    /**
     * Get or create a session ID from localStorage
     */
    getOrCreateSessionId() {
        let sessionId = localStorage.getItem('chatSessionId');
        if (!sessionId) {
            sessionId = this.generateUUID();
            localStorage.setItem('chatSessionId', sessionId);
        }
        return sessionId;
    }

    /**
     * Generate a UUID v4
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Initialize event listeners
     */
    initializeEventListeners() {
        // Send button click
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Enter key to send (Shift+Enter for new line)
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Clear button click
        this.clearButton.addEventListener('click', () => this.clearHistory());

        // Toggle sidebar button
        this.toggleSidebarBtn.addEventListener('click', () => this.toggleSidebar());

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => this.autoResizeTextarea());
    }

    /**
     * Auto-resize textarea based on content
     */
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
    }

    /**
     * Send a message to the chatbot
     */
    async sendMessage() {
        const message = this.messageInput.value.trim();

        if (!message) {
            return;
        }

        // Disable input while sending
        this.setInputState(false);

        // Display user message
        this.addMessageToUI('user', message);

        // Clear input
        this.messageInput.value = '';
        this.autoResizeTextarea();

        // Show loading indicator
        this.showLoading();

        try {
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get response');
            }

            const data = await response.json();

            // Update session ID if new
            this.sessionId = data.session_id;
            localStorage.setItem('chatSessionId', this.sessionId);

            // Hide loading and display assistant response
            this.hideLoading();
            this.addMessageToUI('assistant', data.response);

        } catch (error) {
            this.hideLoading();
            this.addMessageToUI('error', `Error: ${error.message}. Please try again.`);
            console.error('Error:', error);
        } finally {
            // Re-enable input
            this.setInputState(true);
            this.messageInput.focus();
        }
    }

    /**
     * Add a message to the UI
     */
    addMessageToUI(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;

        messageDiv.appendChild(contentDiv);
        this.messageContainer.appendChild(messageDiv);

        // Scroll to bottom
        this.scrollToBottom();
    }

    /**
     * Show loading indicator
     */
    showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant-message loading';
        loadingDiv.id = 'loading-indicator';

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = 'Thinking...';

        loadingDiv.appendChild(contentDiv);
        this.messageContainer.appendChild(loadingDiv);

        this.scrollToBottom();
    }

    /**
     * Hide loading indicator
     */
    hideLoading() {
        const loadingDiv = document.getElementById('loading-indicator');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    /**
     * Clear conversation history
     */
    async clearHistory() {
        if (!confirm('Are you sure you want to clear the conversation history?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiUrl}/clear/${this.sessionId}`, {
                method: 'POST',
            });

            if (!response.ok) {
                throw new Error('Failed to clear history');
            }

            // Clear messages from UI
            this.messageContainer.innerHTML = '';

            // Add welcome message back
            this.addMessageToUI('system', 'Welcome!\n\nI\'m your educational assistant. I provide hints to help you learn, not direct answers.\n\nAsk me anything about your class materials or assignments!');

            this.showStatus('History cleared', 3000);

        } catch (error) {
            this.addMessageToUI('error', 'Failed to clear history. Please try again.');
            console.error('Error:', error);
        }
    }

    /**
     * Set input state (enabled/disabled)
     */
    setInputState(enabled) {
        this.messageInput.disabled = !enabled;
        this.sendButton.disabled = !enabled;
    }

    /**
     * Scroll to bottom of messages
     */
    scrollToBottom() {
        this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
    }

    /**
     * Show status message
     */
    showStatus(message, duration = 3000) {
        this.statusElement.textContent = message;
        this.statusElement.style.opacity = '1';

        setTimeout(() => {
            this.statusElement.style.opacity = '0';
            setTimeout(() => {
                this.statusElement.textContent = '';
            }, 300);
        }, duration);
    }

    /**
     * Load assignment questions from API
     */
    async loadAssignmentQuestions() {
        try {
            const response = await fetch(`${this.apiUrl}/assignment-questions`);

            if (!response.ok) {
                throw new Error('Failed to load assignment questions');
            }

            const data = await response.json();
            this.renderQuestions(data.assignments);

        } catch (error) {
            console.error('Error loading questions:', error);
            this.questionsList.innerHTML = '<div class="loading">Failed to load questions</div>';
        }
    }

    /**
     * Render assignment questions in sidebar
     */
    renderQuestions(assignments) {
        if (!assignments || assignments.length === 0) {
            this.questionsList.innerHTML = '<div class="loading">No assignment questions found</div>';
            return;
        }

        this.questionsList.innerHTML = '';

        assignments.forEach(assignment => {
            // Create assignment group
            const groupDiv = document.createElement('div');
            groupDiv.className = 'assignment-group';

            // Assignment title
            const titleDiv = document.createElement('div');
            titleDiv.className = 'assignment-title';
            titleDiv.textContent = assignment.filename;
            groupDiv.appendChild(titleDiv);

            // Render questions
            assignment.questions.forEach(question => {
                const questionItem = document.createElement('div');
                questionItem.className = 'question-item';

                // Question text (full text which already includes the ID)
                const questionText = document.createElement('div');
                questionText.className = 'question-item-text';
                questionText.textContent = question.text;
                questionItem.appendChild(questionText);

                // Badges for question types
                if (question.has_scenario || question.has_table || question.has_image) {
                    const badgesDiv = document.createElement('div');
                    badgesDiv.className = 'question-badges';

                    if (question.has_scenario) {
                        const badge = document.createElement('span');
                        badge.className = 'badge badge-scenario';
                        badge.textContent = 'Scenario';
                        badgesDiv.appendChild(badge);
                    }

                    if (question.has_table) {
                        const badge = document.createElement('span');
                        badge.className = 'badge badge-table';
                        badge.textContent = 'Table';
                        badgesDiv.appendChild(badge);
                    }

                    if (question.has_image) {
                        const badge = document.createElement('span');
                        badge.className = 'badge badge-image';
                        badge.textContent = 'Image';
                        badgesDiv.appendChild(badge);
                    }

                    questionItem.appendChild(badgesDiv);
                }

                // Click handler
                questionItem.addEventListener('click', () => this.handleQuestionClick(question));

                groupDiv.appendChild(questionItem);
            });

            this.questionsList.appendChild(groupDiv);
        });
    }

    /**
     * Handle question click - populate chat input
     */
    handleQuestionClick(question) {
        // Populate message input with question text
        this.messageInput.value = question.text;
        this.autoResizeTextarea();

        // Focus on input
        this.messageInput.focus();

        // On mobile, collapse sidebar after selection
        if (window.innerWidth <= 768) {
            this.sidebar.classList.add('collapsed');
        }
    }

    /**
     * Toggle sidebar visibility
     */
    toggleSidebar() {
        this.sidebar.classList.toggle('collapsed');
    }
}

// Initialize chat client when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatClient = new ChatClient();
    console.log('PDF Hint Chatbot initialized');
});
