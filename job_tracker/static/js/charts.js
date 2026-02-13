// Chart initialisation functions for the dashboard and analytics pages
// Uses Chart.js which is loaded from CDN in base.html

/**
 * Creates the applications by status doughnut chart.
 * Expects a canvas element with the given id.
 */
function initStatusChart(canvasId, statusData) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !statusData) {
        return null;
    }

    // colour mapping for each application status
    var statusColours = {
        'draft': '#6c757d',
        'applied': '#0d6efd',
        'screening': '#0dcaf0',
        'interview': '#fd7e14',
        'assessment': '#6f42c1',
        'offer': '#198754',
        'accepted': '#20c997',
        'rejected': '#dc3545',
        'withdrawn': '#adb5bd'
    };

    var labels = Object.keys(statusData);
    var values = Object.values(statusData);
    var colours = labels.map(function (label) {
        return statusColours[label] || '#6c757d';
    });

    return new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: labels.map(function (l) {
                // capitalise the first letter for display
                return l.charAt(0).toUpperCase() + l.slice(1);
            }),
            datasets: [{
                data: values,
                backgroundColor: colours,
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        pointStyleWidth: 10
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            var total = context.dataset.data.reduce(function (a, b) { return a + b; }, 0);
                            var percentage = ((context.parsed / total) * 100).toFixed(1);
                            return context.label + ': ' + context.parsed + ' (' + percentage + '%)';
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

/**
 * Creates the monthly application trend line chart.
 * Expects arrays of month labels and count values.
 */
function initTrendChart(canvasId, months, counts) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !months || !counts) {
        return null;
    }

    return new Chart(canvas, {
        type: 'line',
        data: {
            labels: months,
            datasets: [{
                label: 'Applications',
                data: counts,
                borderColor: '#0d6efd',
                backgroundColor: 'rgba(13, 110, 253, 0.1)',
                fill: true,
                tension: 0.3,
                pointBackgroundColor: '#0d6efd',
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    titleFont: { size: 13 },
                    bodyFont: { size: 12 },
                    padding: 10,
                    cornerRadius: 6
                }
            }
        }
    });
}

/**
 * Creates a bar chart for applications by job board / source platform.
 */
function initBoardChart(canvasId, boardData) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !boardData) {
        return null;
    }

    var labels = Object.keys(boardData);
    var values = Object.values(boardData);

    // different colour for each board
    var boardColours = [
        '#0d6efd', '#198754', '#fd7e14', '#6f42c1',
        '#dc3545', '#0dcaf0', '#ffc107', '#20c997'
    ];

    return new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Applications',
                data: values,
                backgroundColor: boardColours.slice(0, labels.length),
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

/**
 * Creates a response rate gauge-style chart.
 * Shows percentage as a half doughnut.
 */
function initResponseRateChart(canvasId, rate) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) {
        return null;
    }

    var responded = parseFloat(rate) || 0;
    var noResponse = 100 - responded;

    return new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels: ['Responded', 'No Response'],
            datasets: [{
                data: [responded, noResponse],
                backgroundColor: ['#198754', '#e9ecef'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            rotation: -90,
            circumference: 180,
            cutout: '75%',
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            return context.label + ': ' + context.parsed.toFixed(1) + '%';
                        }
                    }
                }
            }
        }
    });
}
