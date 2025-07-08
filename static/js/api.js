// API Service for Admin Dashboard

class APIService {
    constructor() {
        this.baseURL = '/api/admin';
        this.token = null;
    }

    // Authentication
    async authenticate(token) {
        this.token = token;
        try {
            const response = await this.request('/auth/verify', { method: 'POST' });
            return response.success;
        } catch (error) {
            console.error('Authentication failed:', error);
            return false;
        }
    }

    // Generic request method
    async request(endpoint, options = {}) {
        const url = this.baseURL + endpoint;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }

        if (config.body && typeof config.body === 'object') {
            config.body = JSON.stringify(config.body);
        }

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Dashboard Overview
    async getOverviewStats(period = '30d') {
        return await this.request(`/overview/stats?period=${period}`);
    }

    async getActivityChart(period = '7d') {
        return await this.request(`/overview/activity?period=${period}`);
    }

    async getRecentActivity(limit = 10) {
        return await this.request(`/overview/recent?limit=${limit}`);
    }

    // Poll Management
    async getPolls(filters = {}, page = 1, limit = 20) {
        const params = new URLSearchParams({
            page: page.toString(),
            limit: limit.toString(),
            ...filters
        });
        return await this.request(`/polls?${params}`);
    }

    async getPoll(pollId) {
        return await this.request(`/polls/${pollId}`);
    }

    async createPoll(pollData) {
        return await this.request('/polls', {
            method: 'POST',
            body: pollData
        });
    }

    async updatePoll(pollId, updates) {
        return await this.request(`/polls/${pollId}`, {
            method: 'PUT',
            body: updates
        });
    }

    async deletePoll(pollId) {
        return await this.request(`/polls/${pollId}`, {
            method: 'DELETE'
        });
    }

    async endPoll(pollId) {
        return await this.request(`/polls/${pollId}/end`, {
            method: 'POST'
        });
    }

    async duplicatePoll(pollId, options = {}) {
        return await this.request(`/polls/${pollId}/duplicate`, {
            method: 'POST',
            body: options
        });
    }

    async exportPolls(pollIds, format = 'csv', options = {}) {
        const body = {
            poll_ids: pollIds,
            format,
            ...options
        };
        
        const response = await fetch(this.baseURL + '/polls/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            throw new Error(`Export failed: ${response.statusText}`);
        }

        return response.blob();
    }

    // User Management
    async getUsers(filters = {}, page = 1, limit = 20) {
        const params = new URLSearchParams({
            page: page.toString(),
            limit: limit.toString(),
            ...filters
        });
        return await this.request(`/users?${params}`);
    }

    async getUser(userId) {
        return await this.request(`/users/${userId}`);
    }

    async updateUserRole(userId, teamId, role) {
        return await this.request(`/users/${userId}/role`, {
            method: 'PUT',
            body: { team_id: teamId, role }
        });
    }

    async getUserActivity(userId, period = '30d') {
        return await this.request(`/users/${userId}/activity?period=${period}`);
    }

    async getUserStats(userId) {
        return await this.request(`/users/${userId}/stats`);
    }

    // Analytics
    async getTeamAnalytics(teamId, period = '30d') {
        return await this.request(`/analytics/team/${teamId}?period=${period}`);
    }

    async getPollAnalytics(pollId) {
        return await this.request(`/analytics/poll/${pollId}`);
    }

    async getEngagementMetrics(period = '30d') {
        return await this.request(`/analytics/engagement?period=${period}`);
    }

    async getPopularPolls(teamId, period = '30d', limit = 10) {
        return await this.request(`/analytics/popular?team_id=${teamId}&period=${period}&limit=${limit}`);
    }

    // Templates
    async getTemplates(category = '') {
        const params = category ? `?category=${category}` : '';
        return await this.request(`/templates${params}`);
    }

    async getTemplate(templateId) {
        return await this.request(`/templates/${templateId}`);
    }

    async createTemplate(templateData) {
        return await this.request('/templates', {
            method: 'POST',
            body: templateData
        });
    }

    async updateTemplate(templateId, updates) {
        return await this.request(`/templates/${templateId}`, {
            method: 'PUT',
            body: updates
        });
    }

    async deleteTemplate(templateId) {
        return await this.request(`/templates/${templateId}`, {
            method: 'DELETE'
        });
    }

    async getTemplateCategories() {
        return await this.request('/templates/categories');
    }

    async getPopularTemplates(limit = 10) {
        return await this.request(`/templates/popular?limit=${limit}`);
    }

    // Scheduled Polls
    async getScheduledPolls(teamId = '') {
        const params = teamId ? `?team_id=${teamId}` : '';
        return await this.request(`/scheduled${params}`);
    }

    async createScheduledPoll(scheduleData) {
        return await this.request('/scheduled', {
            method: 'POST',
            body: scheduleData
        });
    }

    async updateScheduledPoll(scheduleId, updates) {
        return await this.request(`/scheduled/${scheduleId}`, {
            method: 'PUT',
            body: updates
        });
    }

    async cancelScheduledPoll(scheduleId) {
        return await this.request(`/scheduled/${scheduleId}`, {
            method: 'DELETE'
        });
    }

    // Search
    async searchPolls(query, filters = {}, page = 1, limit = 20) {
        const params = new URLSearchParams({
            q: query,
            page: page.toString(),
            limit: limit.toString(),
            ...filters
        });
        return await this.request(`/search/polls?${params}`);
    }

    async searchUsers(query, filters = {}, page = 1, limit = 20) {
        const params = new URLSearchParams({
            q: query,
            page: page.toString(),
            limit: limit.toString(),
            ...filters
        });
        return await this.request(`/search/users?${params}`);
    }

    // Settings
    async getTeamSettings(teamId) {
        return await this.request(`/settings/team/${teamId}`);
    }

    async updateTeamSettings(teamId, settings) {
        return await this.request(`/settings/team/${teamId}`, {
            method: 'PUT',
            body: settings
        });
    }

    async getSystemSettings() {
        return await this.request('/settings/system');
    }

    async updateSystemSettings(settings) {
        return await this.request('/settings/system', {
            method: 'PUT',
            body: settings
        });
    }

    // Security
    async getSecurityReport() {
        return await this.request('/security/report');
    }

    async getSecurityEvents(limit = 50) {
        return await this.request(`/security/events?limit=${limit}`);
    }

    async validateConfiguration() {
        return await this.request('/security/config/validate');
    }

    async getSystemHealth() {
        return await this.request('/system/health');
    }

    async getSystemMetrics() {
        return await this.request('/system/metrics');
    }

    // Notifications
    async getNotifications(limit = 20) {
        return await this.request(`/notifications?limit=${limit}`);
    }

    async markNotificationRead(notificationId) {
        return await this.request(`/notifications/${notificationId}/read`, {
            method: 'POST'
        });
    }

    async markAllNotificationsRead() {
        return await this.request('/notifications/read-all', {
            method: 'POST'
        });
    }
}

// Error handling utility
class APIError extends Error {
    constructor(message, status, response) {
        super(message);
        this.name = 'APIError';
        this.status = status;
        this.response = response;
    }
}

// Request interceptor for automatic token refresh
class AuthenticatedAPIService extends APIService {
    constructor() {
        super();
        this.refreshPromise = null;
    }

    async request(endpoint, options = {}) {
        try {
            return await super.request(endpoint, options);
        } catch (error) {
            if (error.status === 401 && !options._retry) {
                // Token might be expired, try to refresh
                try {
                    await this.refreshToken();
                    return await super.request(endpoint, { ...options, _retry: true });
                } catch (refreshError) {
                    // Refresh failed, redirect to login
                    this.handleAuthFailure();
                    throw refreshError;
                }
            }
            throw error;
        }
    }

    async refreshToken() {
        if (this.refreshPromise) {
            return await this.refreshPromise;
        }

        this.refreshPromise = this.performTokenRefresh();
        try {
            const result = await this.refreshPromise;
            this.refreshPromise = null;
            return result;
        } catch (error) {
            this.refreshPromise = null;
            throw error;
        }
    }

    async performTokenRefresh() {
        // Implementation depends on your auth system
        // This is a placeholder
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            throw new Error('Token refresh failed');
        }

        const data = await response.json();
        this.token = data.access_token;
        localStorage.setItem('access_token', data.access_token);
        
        if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token);
        }

        return data;
    }

    handleAuthFailure() {
        // Clear stored tokens
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        
        // Redirect to login or show auth modal
        window.location.href = '/login';
    }
}

// Export the API service
window.apiService = new AuthenticatedAPIService();

// Initialize with stored token if available
document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('access_token');
    if (token) {
        window.apiService.token = token;
    }
});