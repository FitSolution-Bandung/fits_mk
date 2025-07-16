odoo.define('fits_management_construction.CurveSChart', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const QWeb = core.qweb;

    const CurveSChart = AbstractAction.extend({
        template: 'CurveSChartTemplate',

        start: function () {
            this._super.apply(this, arguments);
            this.render_chart();
        },

        render_chart: function () {
            const self = this;

            // Fetching data from backend
            $.ajax({
                url: `/curve_s/data/${self.context.curve_id}`,
                method: 'POST',
                contentType: 'application/json',
                dataType: 'json',
                success: function (data) {
                    const ctx = document.getElementById('curve_s_chart').getContext('2d');
                    new Chart(ctx, {
                        type: 'line',
                        data: {
                            labels: data.result.map(d => d.date),
                            datasets: [
                                {
                                    label: 'Actual Weight (%)',
                                    data: data.result.map(d => d.actual_weight),
                                    borderColor: 'rgba(255, 99, 132, 1)',
                                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                                    borderWidth: 2,
                                    pointBackgroundColor: 'rgba(255, 99, 132, 1)',
                                    fill: false,
                                },
                                {
                                    label: 'Plan Weight (%)',
                                    data: data.result.map(d => d.plan_weight),
                                    borderColor: 'rgba(255, 159, 64, 1)',
                                    backgroundColor: 'rgba(255, 159, 64, 0.2)',
                                    borderWidth: 2,
                                    pointBackgroundColor: 'rgba(255, 159, 64, 1)',
                                    fill: false,
                                },
                                {
                                    label: 'Plan Weight B (%)',
                                    data: data.result.map(d => d.plan_weight_b),
                                    borderColor: 'rgba(54, 162, 235, 1)',
                                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                                    borderWidth: 2,
                                    pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                                    fill: false,
                                },
                            ],
                        },
                        options: {
                            responsive: true,
                            title: {
                                display: true,
                                text: 'S-Curve (Project Progress)'
                            },
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 100,
                                    ticks: {
                                        callback: function(value) {
                                            return value + ' %';
                                        }
                                    }
                                },
                                x: {
                                    type: 'time',
                                    time: {
                                        unit: 'month'
                                    },
                                    ticks: {
                                        autoSkip: true,
                                        maxTicksLimit: 10
                                    }
                                }
                            },
                            plugins: {
                                datalabels: {
                                    display: true,
                                    color: 'white',
                                    backgroundColor: function(context) {
                                        return context.dataset.borderColor;
                                    },
                                    borderRadius: 4,
                                    font: {
                                        weight: 'bold'
                                    },
                                    formatter: function(value) {
                                        return value.toFixed(1) + ' %';
                                    }
                                }
                            }
                        },
                        plugins: [ChartDataLabels]  // Aktifkan plugin datalabels
                    });
                },
                error: function () {
                    console.error("Error loading Curva S data");
                }
            });
        },
    });

    core.action_registry.add('curve_s_chart_action', CurveSChart);  // Pastikan tag ini sesuai dengan XML
    return CurveSChart;
});
