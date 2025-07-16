/** @odoo-module **/

import { loadJS } from "@web/core/assets";

let jsPDFPromise = null;
let html2canvasPromise = null;
let chartJsPromise = null;

export async function loadJsPDF() {
    if (!jsPDFPromise) {
        jsPDFPromise = loadJS('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js');
    }
    await jsPDFPromise;
    return window.jspdf;
}

export async function loadHtml2Canvas() {
    if (!html2canvasPromise) {
        html2canvasPromise = loadJS('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js');
    }
    await html2canvasPromise;
    return window.html2canvas;
}

export async function loadChartJS() {
    if (!chartJsPromise) {
        chartJsPromise = Promise.all([
            loadJS('https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js'),
            loadJS('https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js')
        ]);
    }
    await chartJsPromise;
    
    if (window.Chart && window.ChartDataLabels) {
        window.Chart.register(window.ChartDataLabels);
    }
    
    return window.Chart;
}