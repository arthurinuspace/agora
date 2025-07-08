// Reusable UI Components

// Data Table Component
class DataTable {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            columns: [],
            data: [],
            pagination: true,
            pageSize: 20,
            sortable: true,
            searchable: true,
            selectable: false,
            actions: [],
            ...options
        };
        
        this.currentPage = 1;
        this.totalPages = 1;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        this.searchQuery = '';
        this.selectedRows = new Set();
        
        this.init();
    }

    init() {
        this.render();
        this.attachEventListeners();
    }

    render() {
        this.container.innerHTML = `
            ${this.options.searchable ? this.renderSearchBar() : ''}
            <div class="data-table-container">
                <table class="data-table">
                    <thead>
                        ${this.renderHeader()}
                    </thead>
                    <tbody>
                        ${this.renderBody()}
                    </tbody>
                </table>
            </div>
            ${this.options.pagination ? this.renderPagination() : ''}
        `;
    }

    renderSearchBar() {
        return `
            <div class="table-controls">
                <div class="search-container">
                    <input type="text" class="search-input" placeholder="Search..." value="${this.searchQuery}">
                    <i class="fas fa-search search-icon"></i>
                </div>
                ${this.options.actions.length > 0 ? this.renderActions() : ''}
            </div>
        `;
    }

    renderActions() {
        return `
            <div class="table-actions">
                ${this.options.actions.map(action => `
                    <button class="btn ${action.class || 'btn-outline'}" 
                            data-action="${action.name}"
                            ${action.requiresSelection ? 'disabled' : ''}>
                        ${action.icon ? `<i class="${action.icon}"></i>` : ''}
                        ${action.label}
                    </button>
                `).join('')}
            </div>
        `;
    }

    renderHeader() {
        return `
            <tr>
                ${this.options.selectable ? '<th><input type="checkbox" class="select-all"></th>' : ''}
                ${this.options.columns.map(column => `
                    <th ${this.options.sortable && column.sortable !== false ? 'class="sortable" data-column="' + column.key + '"' : ''}>
                        ${column.label}
                        ${this.options.sortable && column.sortable !== false ? this.renderSortIcon(column.key) : ''}
                    </th>
                `).join('')}
            </tr>
        `;
    }

    renderSortIcon(columnKey) {
        if (this.sortColumn === columnKey) {
            return `<i class="fas fa-sort-${this.sortDirection === 'asc' ? 'up' : 'down'} sort-icon"></i>`;
        }
        return '<i class="fas fa-sort sort-icon"></i>';
    }

    renderBody() {
        const filteredData = this.getFilteredData();
        const paginatedData = this.getPaginatedData(filteredData);
        
        if (paginatedData.length === 0) {
            return `
                <tr>
                    <td colspan="${this.options.columns.length + (this.options.selectable ? 1 : 0)}" class="text-center">
                        <div class="empty-state">
                            <div class="empty-state-icon">
                                <i class="fas fa-inbox"></i>
                            </div>
                            <div class="empty-state-title">No data found</div>
                            <div class="empty-state-description">
                                ${this.searchQuery ? 'Try adjusting your search criteria' : 'No items to display'}
                            </div>
                        </div>
                    </td>
                </tr>
            `;
        }

        return paginatedData.map((row, index) => `
            <tr data-row-id="${row.id || index}" ${this.selectedRows.has(row.id || index) ? 'class="selected"' : ''}>
                ${this.options.selectable ? `<td><input type="checkbox" class="row-select" value="${row.id || index}"></td>` : ''}
                ${this.options.columns.map(column => `
                    <td>
                        ${this.renderCell(row, column)}
                    </td>
                `).join('')}
            </tr>
        `).join('');
    }

    renderCell(row, column) {
        let value = this.getNestedValue(row, column.key);
        
        if (column.render) {
            return column.render(value, row);
        }
        
        if (column.type === 'badge') {
            const badgeClass = column.badgeClass ? column.badgeClass(value) : 'badge-secondary';
            return `<span class="badge ${badgeClass}">${value}</span>`;
        }
        
        if (column.type === 'date') {
            return this.formatDate(value);
        }
        
        if (column.type === 'number') {
            return this.formatNumber(value);
        }
        
        return this.escapeHtml(value);
    }

    renderPagination() {
        if (this.totalPages <= 1) return '';
        
        return `
            <div class="pagination">
                <div class="pagination-info">
                    Showing ${((this.currentPage - 1) * this.options.pageSize) + 1}-${Math.min(this.currentPage * this.options.pageSize, this.getFilteredData().length)} 
                    of ${this.getFilteredData().length} items
                </div>
                <div class="pagination-controls">
                    <button class="pagination-btn" ${this.currentPage <= 1 ? 'disabled' : ''} data-page="${this.currentPage - 1}">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    ${this.generatePageNumbers()}
                    <button class="pagination-btn" ${this.currentPage >= this.totalPages ? 'disabled' : ''} data-page="${this.currentPage + 1}">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>
        `;
    }

    generatePageNumbers() {
        const pages = [];
        const maxVisible = 5;
        let start = Math.max(1, this.currentPage - Math.floor(maxVisible / 2));
        let end = Math.min(this.totalPages, start + maxVisible - 1);
        
        if (end - start + 1 < maxVisible) {
            start = Math.max(1, end - maxVisible + 1);
        }
        
        for (let i = start; i <= end; i++) {
            pages.push(`
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" data-page="${i}">
                    ${i}
                </button>
            `);
        }
        
        return pages.join('');
    }

    attachEventListeners() {
        // Search
        const searchInput = this.container.querySelector('.search-input');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.searchQuery = e.target.value;
                this.currentPage = 1;
                this.render();
            }, 300));
        }

        // Sorting
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.sortable')) {
                const column = e.target.closest('.sortable').dataset.column;
                this.sort(column);
            }
        });

        // Pagination
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('.pagination-btn') && !e.target.closest('.pagination-btn').disabled) {
                const page = parseInt(e.target.closest('.pagination-btn').dataset.page);
                this.goToPage(page);
            }
        });

        // Selection
        this.container.addEventListener('change', (e) => {
            if (e.target.classList.contains('select-all')) {
                this.toggleAllSelection(e.target.checked);
            } else if (e.target.classList.contains('row-select')) {
                this.toggleRowSelection(e.target.value, e.target.checked);
            }
        });

        // Actions
        this.container.addEventListener('click', (e) => {
            if (e.target.closest('[data-action]')) {
                const actionName = e.target.closest('[data-action]').dataset.action;
                const action = this.options.actions.find(a => a.name === actionName);
                if (action && action.handler) {
                    action.handler(this.getSelectedData());
                }
            }
        });
    }

    // Data methods
    setData(data) {
        this.options.data = data;
        this.currentPage = 1;
        this.selectedRows.clear();
        this.render();
    }

    addRow(row) {
        this.options.data.push(row);
        this.render();
    }

    removeRow(id) {
        this.options.data = this.options.data.filter(row => (row.id || row) !== id);
        this.selectedRows.delete(id);
        this.render();
    }

    updateRow(id, updates) {
        const index = this.options.data.findIndex(row => (row.id || row) === id);
        if (index !== -1) {
            this.options.data[index] = { ...this.options.data[index], ...updates };
            this.render();
        }
    }

    getFilteredData() {
        let filtered = [...this.options.data];
        
        if (this.searchQuery) {
            const query = this.searchQuery.toLowerCase();
            filtered = filtered.filter(row => {
                return this.options.columns.some(column => {
                    const value = this.getNestedValue(row, column.key);
                    return String(value).toLowerCase().includes(query);
                });
            });
        }
        
        if (this.sortColumn) {
            filtered.sort((a, b) => {
                const aVal = this.getNestedValue(a, this.sortColumn);
                const bVal = this.getNestedValue(b, this.sortColumn);
                
                let comparison = 0;
                if (aVal < bVal) comparison = -1;
                if (aVal > bVal) comparison = 1;
                
                return this.sortDirection === 'desc' ? -comparison : comparison;
            });
        }
        
        return filtered;
    }

    getPaginatedData(data) {
        if (!this.options.pagination) return data;
        
        this.totalPages = Math.ceil(data.length / this.options.pageSize);
        const start = (this.currentPage - 1) * this.options.pageSize;
        const end = start + this.options.pageSize;
        
        return data.slice(start, end);
    }

    getSelectedData() {
        return this.options.data.filter(row => this.selectedRows.has(row.id || row));
    }

    // Action methods
    sort(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        this.render();
    }

    goToPage(page) {
        if (page >= 1 && page <= this.totalPages) {
            this.currentPage = page;
            this.render();
        }
    }

    toggleAllSelection(checked) {
        const visibleData = this.getPaginatedData(this.getFilteredData());
        visibleData.forEach(row => {
            const id = row.id || row;
            if (checked) {
                this.selectedRows.add(id);
            } else {
                this.selectedRows.delete(id);
            }
        });
        this.updateActionButtons();
        this.render();
    }

    toggleRowSelection(id, checked) {
        if (checked) {
            this.selectedRows.add(id);
        } else {
            this.selectedRows.delete(id);
        }
        this.updateActionButtons();
        this.updateSelectAllState();
    }

    updateSelectAllState() {
        const selectAll = this.container.querySelector('.select-all');
        if (!selectAll) return;
        
        const visibleData = this.getPaginatedData(this.getFilteredData());
        const visibleSelected = visibleData.filter(row => this.selectedRows.has(row.id || row));
        
        if (visibleSelected.length === 0) {
            selectAll.indeterminate = false;
            selectAll.checked = false;
        } else if (visibleSelected.length === visibleData.length) {
            selectAll.indeterminate = false;
            selectAll.checked = true;
        } else {
            selectAll.indeterminate = true;
            selectAll.checked = false;
        }
    }

    updateActionButtons() {
        const hasSelection = this.selectedRows.size > 0;
        this.container.querySelectorAll('[data-action]').forEach(btn => {
            const action = this.options.actions.find(a => a.name === btn.dataset.action);
            if (action && action.requiresSelection) {
                btn.disabled = !hasSelection;
            }
        });
    }

    // Utility methods
    getNestedValue(obj, path) {
        return path.split('.').reduce((o, p) => o && o[p], obj);
    }

    formatDate(dateString) {
        if (!dateString) return '';
        return new Date(dateString).toLocaleDateString();
    }

    formatNumber(num) {
        if (typeof num !== 'number') return num;
        return new Intl.NumberFormat().format(num);
    }

    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

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
}

// Modal Component
class Modal {
    constructor(options = {}) {
        this.options = {
            title: '',
            content: '',
            size: 'medium', // small, medium, large
            closable: true,
            backdrop: true,
            ...options
        };
        
        this.element = null;
        this.overlay = null;
        this.isOpen = false;
        
        this.create();
    }

    create() {
        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.className = 'modal-overlay';
        
        // Create modal
        this.element = document.createElement('div');
        this.element.className = `modal modal-${this.options.size}`;
        
        this.element.innerHTML = `
            <div class="modal-header">
                <h3 class="modal-title">${this.options.title}</h3>
                ${this.options.closable ? '<button class="modal-close">&times;</button>' : ''}
            </div>
            <div class="modal-body">
                ${this.options.content}
            </div>
            ${this.options.footer ? `<div class="modal-footer">${this.options.footer}</div>` : ''}
        `;
        
        this.overlay.appendChild(this.element);
        
        // Event listeners
        if (this.options.closable) {
            this.element.querySelector('.modal-close').addEventListener('click', () => this.close());
        }
        
        if (this.options.backdrop) {
            this.overlay.addEventListener('click', (e) => {
                if (e.target === this.overlay) this.close();
            });
        }
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen && this.options.closable) {
                this.close();
            }
        });
    }

    show() {
        document.body.appendChild(this.overlay);
        setTimeout(() => {
            this.overlay.classList.add('active');
            this.isOpen = true;
        }, 10);
        
        if (this.options.onShow) {
            this.options.onShow();
        }
    }

    hide() {
        this.overlay.classList.remove('active');
        setTimeout(() => {
            if (this.overlay.parentNode) {
                document.body.removeChild(this.overlay);
            }
            this.isOpen = false;
        }, 300);
        
        if (this.options.onHide) {
            this.options.onHide();
        }
    }

    close() {
        if (this.options.onClose && this.options.onClose() === false) {
            return; // Prevent closing if onClose returns false
        }
        this.hide();
    }

    setTitle(title) {
        const titleElement = this.element.querySelector('.modal-title');
        if (titleElement) {
            titleElement.textContent = title;
        }
    }

    setContent(content) {
        const bodyElement = this.element.querySelector('.modal-body');
        if (bodyElement) {
            bodyElement.innerHTML = content;
        }
    }

    setFooter(footer) {
        let footerElement = this.element.querySelector('.modal-footer');
        if (!footerElement) {
            footerElement = document.createElement('div');
            footerElement.className = 'modal-footer';
            this.element.appendChild(footerElement);
        }
        footerElement.innerHTML = footer;
    }
}

// Toast Notification Component
class Toast {
    static container = null;

    static init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            document.body.appendChild(this.container);
        }
    }

    static show(message, type = 'info', duration = 3000) {
        this.init();
        
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

        this.container.appendChild(toast);

        // Show animation
        setTimeout(() => toast.classList.add('show'), 100);

        // Auto remove
        setTimeout(() => {
            this.remove(toast);
        }, duration);

        // Close button
        toast.querySelector('.toast-close').addEventListener('click', () => {
            this.remove(toast);
        });

        return toast;
    }

    static remove(toast) {
        toast.classList.remove('show');
        setTimeout(() => {
            if (toast.parentNode) {
                this.container.removeChild(toast);
            }
        }, 300);
    }

    static success(message, duration) {
        return this.show(message, 'success', duration);
    }

    static error(message, duration) {
        return this.show(message, 'error', duration);
    }

    static warning(message, duration) {
        return this.show(message, 'warning', duration);
    }

    static info(message, duration) {
        return this.show(message, 'info', duration);
    }
}

// Loading Component
class Loading {
    static overlay = null;

    static show(message = 'Loading...') {
        if (!this.overlay) {
            this.overlay = document.createElement('div');
            this.overlay.className = 'loading-spinner';
            this.overlay.innerHTML = `
                <div class="spinner-container">
                    <div class="spinner"></div>
                    <div class="loading-message">${message}</div>
                </div>
            `;
            document.body.appendChild(this.overlay);
        }
        
        this.overlay.querySelector('.loading-message').textContent = message;
        this.overlay.classList.add('active');
    }

    static hide() {
        if (this.overlay) {
            this.overlay.classList.remove('active');
        }
    }
}

// Form Validator Component
class FormValidator {
    constructor(formElement, rules = {}) {
        this.form = formElement;
        this.rules = rules;
        this.errors = {};
        
        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => {
            if (!this.validate()) {
                e.preventDefault();
            }
        });

        // Real-time validation
        Object.keys(this.rules).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.addEventListener('blur', () => {
                    this.validateField(fieldName);
                });
                field.addEventListener('input', () => {
                    this.clearFieldError(fieldName);
                });
            }
        });
    }

    validate() {
        this.errors = {};
        let isValid = true;

        Object.keys(this.rules).forEach(fieldName => {
            if (!this.validateField(fieldName)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateField(fieldName) {
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        const rules = this.rules[fieldName];
        const value = field ? field.value.trim() : '';

        this.clearFieldError(fieldName);

        for (const rule of rules) {
            if (!this.checkRule(value, rule)) {
                this.setFieldError(fieldName, rule.message);
                return false;
            }
        }

        return true;
    }

    checkRule(value, rule) {
        switch (rule.type) {
            case 'required':
                return value.length > 0;
            case 'min':
                return value.length >= rule.value;
            case 'max':
                return value.length <= rule.value;
            case 'email':
                return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            case 'pattern':
                return new RegExp(rule.value).test(value);
            case 'custom':
                return rule.validator(value);
            default:
                return true;
        }
    }

    setFieldError(fieldName, message) {
        this.errors[fieldName] = message;
        
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.classList.add('error');
            
            let errorElement = field.parentNode.querySelector('.form-error');
            if (!errorElement) {
                errorElement = document.createElement('div');
                errorElement.className = 'form-error';
                field.parentNode.appendChild(errorElement);
            }
            errorElement.textContent = message;
        }
    }

    clearFieldError(fieldName) {
        delete this.errors[fieldName];
        
        const field = this.form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.classList.remove('error');
            
            const errorElement = field.parentNode.querySelector('.form-error');
            if (errorElement) {
                errorElement.remove();
            }
        }
    }

    getErrors() {
        return this.errors;
    }

    hasErrors() {
        return Object.keys(this.errors).length > 0;
    }
}

// Export components
window.DataTable = DataTable;
window.Modal = Modal;
window.Toast = Toast;
window.Loading = Loading;
window.FormValidator = FormValidator;