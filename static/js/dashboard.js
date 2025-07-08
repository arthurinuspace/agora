// Dashboard Main JavaScript

class AdminDashboard {
    constructor() {
        this.currentSection = 'overview';
        this.charts = {};
        this.pollsData = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.filters = {};
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.setupTooltips();
    }

    setupEventListeners() {
        // Sidebar navigation
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const section = e.currentTarget.dataset.section;
                this.switchSection(section);
            });
        });

        // Sidebar toggle for mobile
        const sidebarToggle = document.querySelector('.sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => {
                document.querySelector('.sidebar').classList.toggle('open');
            });
        }

        // Global search
        const globalSearch = document.getElementById('global-search');
        if (globalSearch) {
            globalSearch.addEventListener('input', this.debounce((e) => {
                this.performGlobalSearch(e.target.value);
            }, 300));
        }

        // Modal controls
        this.setupModalControls();

        // Filter controls
        this.setupFilterControls();

        // Action buttons
        this.setupActionButtons();

        // Table interactions
        this.setupTableInteractions();
    }

    setupModalControls() {
        // Close modal when clicking overlay or close button
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay') || 
                e.target.classList.contains('modal-close')) {
                this.closeModal();
            }
        });

        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }

    setupFilterControls() {
        const filterInputs = [
            'poll-status-filter',
            'poll-type-filter',
            'date-from-filter',
            'date-to-filter'
        ];

        filterInputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    this.updateFilters();
                });
            }
        });

        const clearFiltersBtn = document.getElementById('clear-filters-btn');
        if (clearFiltersBtn) {
            clearFiltersBtn.addEventListener('click', () => {
                this.clearFilters();
            });
        }
    }

    setupActionButtons() {
        // New poll button
        const newPollBtn = document.getElementById('new-poll-btn');
        if (newPollBtn) {
            newPollBtn.addEventListener('click', () => {
                this.showCreatePollModal();
            });
        }

        // Export polls button
        const exportPollsBtn = document.getElementById('export-polls-btn');
        if (exportPollsBtn) {
            exportPollsBtn.addEventListener('click', () => {
                this.showExportModal();
            });
        }

        // Activity period selector
        const activityPeriod = document.getElementById('activity-period');
        if (activityPeriod) {
            activityPeriod.addEventListener('change', (e) => {
                this.updateActivityChart(e.target.value);
            });
        }
    }

    setupTableInteractions() {
        // Select all checkbox
        const selectAllPolls = document.getElementById('select-all-polls');
        if (selectAllPolls) {
            selectAllPolls.addEventListener('change', (e) => {
                this.toggleAllPolls(e.target.checked);
            });
        }
    }

    async loadInitialData() {
        try {
            this.showLoading(true);
            
            // Load overview data
            await this.loadOverviewData();
            
            // Load polls data
            await this.loadPollsData();
            
            this.showLoading(false);
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showToast('Failed to load dashboard data', 'error');
            this.showLoading(false);
        }
    }

    async loadOverviewData() {
        try {
            const [stats, activity, recentActivity] = await Promise.all([
                window.apiService.getOverviewStats(),
                window.apiService.getActivityChart(),
                window.apiService.getRecentActivity()
            ]);

            this.updateOverviewStats(stats);
            this.updateActivityChart(activity);
            this.updateRecentActivity(recentActivity);
        } catch (error) {
            console.error('Failed to load overview data:', error);
            // Use mock data for demonstration
            this.loadMockOverviewData();
        }
    }

    loadMockOverviewData() {
        // Mock data for demonstration
        const mockStats = {
            total_polls: 127,
            total_votes: 2847,
            active_users: 89,
            active_polls: 12
        };

        const mockActivity = {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            polls_created: [5, 8, 12, 7, 15, 3, 9],
            votes_cast: [45, 67, 89, 54, 123, 34, 78]
        };

        const mockRecentActivity = [
            {
                type: 'poll_created',
                title: 'New poll created',
                description: '"Team lunch preferences" by @john.doe',
                time: '2 minutes ago',
                icon: 'fas fa-plus',
                color: 'bg-success'
            },
            {
                type: 'poll_ended',
                title: 'Poll ended',
                description: '"Project timeline" reached 50 votes',
                time: '15 minutes ago',
                icon: 'fas fa-flag-checkered',
                color: 'bg-warning'
            },
            {
                type: 'user_voted',
                title: 'High engagement',
                description: '"Weekly retrospective" received 25 votes',
                time: '1 hour ago',
                icon: 'fas fa-chart-line',
                color: 'bg-info'
            }
        ];

        this.updateOverviewStats(mockStats);
        this.updateActivityChart(mockActivity);
        this.updateRecentActivity(mockRecentActivity);
    }

    updateOverviewStats(stats) {
        document.getElementById('total-polls').textContent = this.formatNumber(stats.total_polls || 0);
        document.getElementById('total-votes').textContent = this.formatNumber(stats.total_votes || 0);
        document.getElementById('active-users').textContent = this.formatNumber(stats.active_users || 0);
        document.getElementById('active-polls').textContent = this.formatNumber(stats.active_polls || 0);
    }

    updateActivityChart(data) {
        const ctx = document.getElementById('activity-chart');
        if (!ctx) return;

        // Destroy existing chart if it exists
        if (this.charts.activity) {
            this.charts.activity.destroy();
        }

        this.charts.activity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [
                    {
                        label: 'Polls Created',
                        data: data.polls_created || [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Votes Cast',
                        data: data.votes_cast || [],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    updateRecentActivity(activities) {
        const container = document.getElementById('recent-activity-list');
        if (!container) return;

        container.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <div class="activity-icon ${activity.color}">
                    <i class="${activity.icon}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-description">${activity.description}</div>
                    <div class="activity-time">${activity.time}</div>
                </div>
            </div>
        `).join('');
    }

    async loadPollsData(page = 1) {
        try {
            const response = await this.getPollsWithFilters(page);
            this.pollsData = response.polls || [];
            this.currentPage = response.page || 1;
            this.totalPages = response.total_pages || 1;
            
            this.updatePollsTable();
            this.updatePagination();
        } catch (error) {
            console.error('Failed to load polls data:', error);
            this.loadMockPollsData();
        }
    }

    async getPollsWithFilters(page = 1) {
        // In a real implementation, this would call the API
        // For now, return mock data
        return {
            polls: [
                {
                    id: 1,
                    question: "What should we have for lunch?",
                    type: "single",
                    status: "active",
                    votes: 15,
                    created: "2024-01-15T10:30:00Z",
                    creator: "john.doe"
                },
                {
                    id: 2,
                    question: "Which project should we prioritize?",
                    type: "multiple",
                    status: "ended",
                    votes: 42,
                    created: "2024-01-14T14:20:00Z",
                    creator: "jane.smith"
                }
            ],
            page: page,
            total_pages: 5,
            total_count: 127
        };
    }

    loadMockPollsData() {
        this.pollsData = [
            {
                id: 1,
                question: "What should we have for team lunch?",
                type: "single",
                status: "active",
                votes: 15,
                created: "2024-01-15T10:30:00Z",
                creator: "john.doe"
            },
            {
                id: 2,
                question: "Which project should we prioritize next quarter?",
                type: "multiple",
                status: "ended",
                votes: 42,
                created: "2024-01-14T14:20:00Z",
                creator: "jane.smith"
            },
            {
                id: 3,
                question: "Best time for weekly team meetings?",
                type: "single",
                status: "active",
                votes: 28,
                created: "2024-01-13T09:15:00Z",
                creator: "mike.johnson"
            }
        ];
        
        this.updatePollsTable();
        this.updatePagination();
    }

    updatePollsTable() {
        const tbody = document.getElementById('polls-table-body');
        if (!tbody) return;

        tbody.innerHTML = this.pollsData.map(poll => `
            <tr data-poll-id="${poll.id}">
                <td>
                    <input type="checkbox" class="poll-checkbox" value="${poll.id}">
                </td>
                <td>
                    <div class="poll-question">
                        <span class="question-text">${this.escapeHtml(poll.question)}</span>
                    </div>
                </td>
                <td>
                    <span class="badge ${poll.type === 'single' ? 'badge-primary' : 'badge-info'}">
                        ${poll.type === 'single' ? 'Single Choice' : 'Multiple Choice'}
                    </span>
                </td>
                <td>
                    <span class="badge ${poll.status === 'active' ? 'badge-success' : 'badge-secondary'}">
                        ${poll.status === 'active' ? 'Active' : 'Ended'}
                    </span>
                </td>
                <td>${poll.votes}</td>
                <td>${this.formatDate(poll.created)}</td>
                <td>@${poll.creator}</td>
                <td>
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-outline" onclick="dashboard.viewPoll(${poll.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="dashboard.editPoll(${poll.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-outline" onclick="dashboard.duplicatePoll(${poll.id})" title="Duplicate">
                            <i class="fas fa-copy"></i>
                        </button>
                        ${poll.status === 'active' ? 
                            `<button class="btn btn-sm btn-warning" onclick="dashboard.endPoll(${poll.id})" title="End Poll">
                                <i class="fas fa-stop"></i>
                            </button>` : ''
                        }
                        <button class="btn btn-sm btn-danger" onclick="dashboard.deletePoll(${poll.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

        // Add event listeners for checkboxes
        tbody.querySelectorAll('.poll-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateSelectAllState();
            });
        });
    }

    updatePagination() {
        const container = document.getElementById('polls-pagination');
        if (!container) return;

        const startItem = (this.currentPage - 1) * 20 + 1;
        const endItem = Math.min(this.currentPage * 20, this.pollsData.length);
        const totalItems = this.pollsData.length;

        container.innerHTML = `
            <div class="pagination-info">
                Showing ${startItem}-${endItem} of ${totalItems} polls
            </div>
            <div class="pagination-controls">
                <button class="pagination-btn" ${this.currentPage <= 1 ? 'disabled' : ''} 
                        onclick="dashboard.goToPage(${this.currentPage - 1})">
                    <i class="fas fa-chevron-left"></i>
                </button>
                ${this.generatePageNumbers()}
                <button class="pagination-btn" ${this.currentPage >= this.totalPages ? 'disabled' : ''} 
                        onclick="dashboard.goToPage(${this.currentPage + 1})">
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>
        `;
    }

    generatePageNumbers() {
        const pages = [];
        const maxVisiblePages = 5;
        let startPage = Math.max(1, this.currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(this.totalPages, startPage + maxVisiblePages - 1);

        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            pages.push(`
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                        onclick="dashboard.goToPage(${i})">
                    ${i}
                </button>
            `);
        }

        return pages.join('');
    }

    switchSection(section) {
        // Update sidebar
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');

        // Update content
        document.querySelectorAll('.content-section').forEach(section => {
            section.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');

        // Update page title
        const titles = {
            overview: 'Dashboard Overview',
            polls: 'Poll Management',
            users: 'User Management',
            analytics: 'Analytics',
            templates: 'Templates',
            settings: 'Settings',
            security: 'Security'
        };
        document.getElementById('page-title').textContent = titles[section] || section;

        this.currentSection = section;

        // Load section-specific data
        this.loadSectionData(section);
    }

    async loadSectionData(section) {
        switch (section) {
            case 'overview':
                await this.loadOverviewData();
                break;
            case 'polls':
                await this.loadPollsData();
                break;
            case 'users':
                // Load users data
                break;
            case 'analytics':
                // Load analytics data
                break;
            case 'templates':
                // Load templates data
                break;
            case 'settings':
                // Load settings data
                break;
            case 'security':
                // Load security data
                break;
        }
    }

    // Poll Actions
    async viewPoll(pollId) {
        try {
            const poll = await window.apiService.getPoll(pollId);
            this.showPollDetailsModal(poll);
        } catch (error) {
            console.error('Failed to load poll details:', error);
            this.showToast('Failed to load poll details', 'error');
        }
    }

    async editPoll(pollId) {
        // Implementation for edit poll
        this.showToast('Edit functionality coming soon', 'info');
    }

    async duplicatePoll(pollId) {
        try {
            const result = await window.apiService.duplicatePoll(pollId);
            this.showToast('Poll duplicated successfully', 'success');
            await this.loadPollsData();
        } catch (error) {
            console.error('Failed to duplicate poll:', error);
            this.showToast('Failed to duplicate poll', 'error');
        }
    }

    async endPoll(pollId) {
        if (!confirm('Are you sure you want to end this poll?')) {
            return;
        }

        try {
            await window.apiService.endPoll(pollId);
            this.showToast('Poll ended successfully', 'success');
            await this.loadPollsData();
        } catch (error) {
            console.error('Failed to end poll:', error);
            this.showToast('Failed to end poll', 'error');
        }
    }

    async deletePoll(pollId) {
        if (!confirm('Are you sure you want to delete this poll? This action cannot be undone.')) {
            return;
        }

        try {
            await window.apiService.deletePoll(pollId);
            this.showToast('Poll deleted successfully', 'success');
            await this.loadPollsData();
        } catch (error) {
            console.error('Failed to delete poll:', error);
            this.showToast('Failed to delete poll', 'error');
        }
    }

    // Filter methods
    updateFilters() {
        this.filters = {
            status: document.getElementById('poll-status-filter')?.value || '',
            type: document.getElementById('poll-type-filter')?.value || '',
            date_from: document.getElementById('date-from-filter')?.value || '',
            date_to: document.getElementById('date-to-filter')?.value || ''
        };

        this.loadPollsData(1); // Reset to first page
    }

    clearFilters() {
        document.getElementById('poll-status-filter').value = '';
        document.getElementById('poll-type-filter').value = '';
        document.getElementById('date-from-filter').value = '';
        document.getElementById('date-to-filter').value = '';
        
        this.filters = {};
        this.loadPollsData(1);
    }

    // Selection methods
    toggleAllPolls(checked) {
        document.querySelectorAll('.poll-checkbox').forEach(checkbox => {
            checkbox.checked = checked;
        });
    }

    updateSelectAllState() {
        const checkboxes = document.querySelectorAll('.poll-checkbox');
        const selectAll = document.getElementById('select-all-polls');
        
        if (!selectAll) return;

        const checkedCount = document.querySelectorAll('.poll-checkbox:checked').length;
        
        if (checkedCount === 0) {
            selectAll.indeterminate = false;
            selectAll.checked = false;
        } else if (checkedCount === checkboxes.length) {
            selectAll.indeterminate = false;
            selectAll.checked = true;
        } else {
            selectAll.indeterminate = true;
            selectAll.checked = false;
        }
    }

    getSelectedPolls() {
        return Array.from(document.querySelectorAll('.poll-checkbox:checked'))
            .map(checkbox => parseInt(checkbox.value));
    }

    // Navigation methods
    async goToPage(page) {
        if (page < 1 || page > this.totalPages) return;
        await this.loadPollsData(page);
    }

    // Modal methods
    showPollDetailsModal(poll) {
        const modal = document.getElementById('poll-details-modal');
        const content = document.getElementById('poll-details-content');
        
        content.innerHTML = `
            <div class="poll-details">
                <h4>${this.escapeHtml(poll.question)}</h4>
                <div class="poll-meta">
                    <span class="badge ${poll.type === 'single' ? 'badge-primary' : 'badge-info'}">
                        ${poll.type === 'single' ? 'Single Choice' : 'Multiple Choice'}
                    </span>
                    <span class="badge ${poll.status === 'active' ? 'badge-success' : 'badge-secondary'}">
                        ${poll.status === 'active' ? 'Active' : 'Ended'}
                    </span>
                </div>
                <div class="poll-options">
                    ${poll.options ? poll.options.map(option => `
                        <div class="option-item">
                            <span class="option-text">${this.escapeHtml(option.text)}</span>
                            <span class="option-votes">${option.vote_count} votes</span>
                            <div class="progress">
                                <div class="progress-bar" style="width: ${(option.vote_count / poll.total_votes * 100) || 0}%"></div>
                            </div>
                        </div>
                    `).join('') : ''}
                </div>
            </div>
        `;
        
        this.showModal('poll-details-modal');
    }

    showCreatePollModal() {
        // Implementation for create poll modal
        this.showToast('Create poll functionality coming soon', 'info');
    }

    showExportModal() {
        const selectedPolls = this.getSelectedPolls();
        if (selectedPolls.length === 0) {
            this.showToast('Please select polls to export', 'warning');
            return;
        }
        
        // Implementation for export modal
        this.showToast(`Exporting ${selectedPolls.length} polls...`, 'info');
    }

    showModal(modalId) {
        document.getElementById('modal-overlay').classList.add('active');
        document.getElementById(modalId).style.display = 'block';
    }

    closeModal() {
        document.getElementById('modal-overlay').classList.remove('active');
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }

    // Search methods
    async performGlobalSearch(query) {
        if (!query.trim()) return;
        
        try {
            const results = await window.apiService.searchPolls(query);
            // Handle search results
            console.log('Search results:', results);
        } catch (error) {
            console.error('Search failed:', error);
        }
    }

    // Utility methods
    showLoading(show) {
        const spinner = document.getElementById('loading-spinner');
        if (spinner) {
            spinner.classList.toggle('active', show);
        }
    }

    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        const icons = {
            success: 'fas fa-check',
            error: 'fas fa-times',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        toast.innerHTML = `
            <div class="toast-icon">
                <i class="${icons[type] || icons.info}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-message">${message}</div>
            </div>
            <button class="toast-close">
                <i class="fas fa-times"></i>
            </button>
        `;

        container.appendChild(toast);

        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);

        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        }, duration);

        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => container.removeChild(toast), 300);
        });
    }

    setupTooltips() {
        // Simple tooltip implementation
        document.addEventListener('mouseover', (e) => {
            if (e.target.hasAttribute('title')) {
                const title = e.target.getAttribute('title');
                e.target.setAttribute('data-original-title', title);
                e.target.removeAttribute('title');
                
                const tooltip = document.createElement('div');
                tooltip.className = 'tooltip';
                tooltip.textContent = title;
                document.body.appendChild(tooltip);
                
                const rect = e.target.getBoundingClientRect();
                tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
                tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
                
                e.target._tooltip = tooltip;
            }
        });

        document.addEventListener('mouseout', (e) => {
            if (e.target._tooltip) {
                document.body.removeChild(e.target._tooltip);
                e.target._tooltip = null;
                
                if (e.target.hasAttribute('data-original-title')) {
                    e.target.setAttribute('title', e.target.getAttribute('data-original-title'));
                    e.target.removeAttribute('data-original-title');
                }
            }
        });
    }

    // Helper methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new AdminDashboard();
});

// CSS for tooltips
const tooltipStyles = `
    .tooltip {
        position: absolute;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        z-index: 10000;
        pointer-events: none;
        white-space: nowrap;
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = tooltipStyles;
document.head.appendChild(styleSheet);