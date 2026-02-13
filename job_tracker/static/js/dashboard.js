// Dashboard interactivity - handles auto refresh, tooltips, and confirmation dialogs

document.addEventListener('DOMContentLoaded', function () {

    // enable bootstrap tooltips throughout the page
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // confirm before deleting anything
    var deleteLinks = document.querySelectorAll('.btn-outline-danger, .btn-danger');
    deleteLinks.forEach(function (link) {
        // only attach to links that go to a delete url
        if (link.href && link.href.indexOf('delete') !== -1) {
            link.addEventListener('click', function (e) {
                if (!confirm('Are you sure you want to delete this? This action cannot be undone.')) {
                    e.preventDefault();
                }
            });
        }
    });

    // auto dismiss alert messages after 5 seconds
    var alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // highlight the current nav link based on the url
    var currentPath = window.location.pathname;
    var navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(function (link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // handle filter form reset
    var resetBtn = document.getElementById('resetFilters');
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            var form = this.closest('form');
            var inputs = form.querySelectorAll('input, select');
            inputs.forEach(function (input) {
                if (input.type === 'text' || input.type === 'date') {
                    input.value = '';
                } else if (input.tagName === 'SELECT') {
                    input.selectedIndex = 0;
                }
            });
            form.submit();
        });
    }

    // keyboard shortcut: press 'n' to go to new application form
    document.addEventListener('keydown', function (e) {
        // dont trigger if typing in an input field
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            return;
        }
        if (e.key === 'n' && !e.ctrlKey && !e.metaKey) {
            var newAppLink = document.querySelector('a[href*="create"]');
            if (newAppLink) {
                window.location.href = newAppLink.href;
            }
        }
    });
});
