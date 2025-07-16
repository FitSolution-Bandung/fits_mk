/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { loadJsPDF, loadHtml2Canvas, loadChartJS } from "./library";

class CurveSChart extends Component {
  static template = "fits_management_construction.CurveSChart";
  static props = {
    action: { type: Object, optional: true },
    actionId: { type: Number, optional: true },
    className: { type: String, optional: true },
    context: { type: Object, optional: true },
    state: { type: Object, optional: true },
  };

  setup() {
    this.actionService = useService("action");
    this.chartRef = useRef("chart");
    this.http = useService("http");
    this.chart = null;
    this.orm = useService("orm");
    this.rpc = useService("rpc");
    this.view = useService("view");
    this.company = useService("company");

    const curveId =
      this.props.action?.context?.active_id ||
      this.props.context?.active_id ||
      this.props.state?.active_id;

    onMounted(async () => {
      console.log("CurveSChart component mounted");
      console.log("Props:", this.props);
      console.log("CurveId:", curveId);

      if (curveId) {
        await this.loadAndRenderChart(curveId);
      } else {
        console.error("curveId tidak ditemukan dalam context atau state");
      }
    });
  }

  async loadAndRenderChart(curveId) {
    try {
      const result = await this.http.get(`/curve_s/data/${curveId}`);
      console.log("Data received:", result);

      if (result && !result.error) {
        const Chart = await loadChartJS();
        this.renderChart(
          result.data,
          result.project_name,
          result.last_updated_date
        );
      } else {
        console.error("Error loading data:", result.error || "Data not found");
      }
    } catch (error) {
      console.error("Failed to load chart data:", error);
    }
  }

  async printToPDF() {
    const jsPDF = await loadJsPDF();
    const html2canvas = await loadHtml2Canvas();

    if (this.chartRef.el) {
      const canvas = await html2canvas(this.chartRef.el, {
        scale: 3,
        dpi: 300,
        useCORS: true,
        logging: false,
      });

      const imgData = canvas.toDataURL("image/png", 1.0);

      const pdf = new jsPDF.jsPDF({
        orientation: "landscape",
        unit: "mm",
        format: "a4",
        compress: false,
      });

      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();

      const headerHeight = 35;
      const footerHeight = 20;
      const contentArea = pageHeight - headerHeight - footerHeight;

      const companyData = await this.orm.read(
        "res.company",
        [this.env.services.company.currentCompany.id],
        [
          "name",
          "street",
          "street2",
          "city",
          "state_id",
          "zip",
          "country_id",
          "phone",
          "email",
          "website",
          "vat",
          "logo",
        ]
      );
      const company = companyData[0];

      pdf.setDrawColor(229, 229, 229);
      pdf.line(10, 35, pageWidth - 10, 35);

      if (company.logo) {
        const logoData = `data:image/png;base64,${company.logo}`;
        pdf.addImage(logoData, "PNG", 10, 10, 20, 20);

        pdf.setFontSize(11);
        pdf.text(company.name, 35, 15);
        pdf.setFontSize(9);

        let address = [company.street];
        if (company.street2) address.push(company.street2);
        if (company.city) {
          let cityLine = `${company.city}`;
          if (company.state_id) cityLine += ` ${company.state_id[1]}`;
          if (company.zip) cityLine += ` ${company.zip}`;
          address.push(cityLine);
        }
        if (company.country_id) address.push(company.country_id[1]);

        let y = 20;
        address.forEach((line) => {
          pdf.text(line, 35, y);
          y += 4;
        });
      }

      pdf.setFontSize(14);
      const projectNameText = `S Curve - ${this.projectName}`;
      const projectNameTextWidth = pdf.getTextWidth(projectNameText);
      pdf.text(
        projectNameText,
        (pageWidth - projectNameTextWidth) / 2,
        headerHeight - 15
      );

      const maxImgWidth = pageWidth - 40;
      const maxImgHeight = contentArea - 20;
      const imgAspectRatio = canvas.width / canvas.height;

      let imgWidth = maxImgWidth;
      let imgHeight = imgWidth / imgAspectRatio;

      if (imgHeight > maxImgHeight) {
        imgHeight = maxImgHeight;
        imgWidth = imgHeight * imgAspectRatio;
      }

      const centerX = (pageWidth - imgWidth) / 2;

      pdf.addImage(
        imgData,
        "PNG",
        centerX,
        headerHeight + 10,
        imgWidth + 10,
        imgHeight + 5,
        undefined,
        "FAST"
      );

      pdf.setDrawColor(229, 229, 229);
      pdf.line(10, pageHeight - 15, pageWidth - 10, pageHeight - 15);

      let contactInfo = [];
      if (company.phone) contactInfo.push(company.phone);
      if (company.email) contactInfo.push(company.email);
      if (company.website) contactInfo.push(company.website);
      if (company.vat) contactInfo.push(company.vat);

      const contactText = contactInfo.join(" ");
      pdf.setFontSize(8);
      const contactTextWidth = pdf.getTextWidth(contactText);
      pdf.text(
        contactText,
        (pageWidth - contactTextWidth) / 2,
        pageHeight - 12
      );

      pdf.save(`S Curve - ${this.projectName}.pdf`);
    }
  }

  async saveAsImage() {
    const html2canvas = await loadHtml2Canvas();

    if (this.chartRef.el) {
      // Render original chart
      const originalCanvas = await html2canvas(this.chartRef.el, {
        scale: 3,
        dpi: 300,
        useCORS: true,
        logging: false,
      });

      // Create new canvas with extra space for title
      const newCanvas = document.createElement("canvas");
      const padding = 100; // Space for title
      newCanvas.width = originalCanvas.width;
      newCanvas.height = originalCanvas.height + padding;

      const context = newCanvas.getContext("2d");

      // Fill background
      context.fillStyle = "white";
      context.fillRect(0, 0, newCanvas.width, newCanvas.height);

      // Draw original chart image
      context.drawImage(
        originalCanvas,
        0,
        padding,
        originalCanvas.width,
        originalCanvas.height
      );

      // Add text
      context.font = "bold 64px Arial"; // Make text bigger and bold
      context.fillStyle = "black";

      const text = `S Curve - ${this.projectName}`;
      const textWidth = context.measureText(text).width;
      const centerX = (newCanvas.width - textWidth) / 2;

      context.fillText(text, centerX, padding / 2 + 10); // Position text in the middle of padding area

      // Convert to image and download
      const imgData = newCanvas.toDataURL("image/png", 1.0);

      const link = document.createElement("a");
      link.href = imgData;
      link.download = `S Curve - ${this.projectName}.png`;
      link.click();
    }
  }

  async renderChart(data, projectName, lastUpdatedDate) {
    this.projectName = projectName;

    if (this.chart) {
      this.chart.destroy();
    }

    if (!this.chartRef.el) {
      console.error("Canvas element not found");
      return;
    }

    const ctx = this.chartRef.el.getContext("2d");

    // Format tanggal dari data.dates
    const formattedDates = data.dates.map((date) => {
      const d = new Date(date);
      return d.toLocaleDateString("id-ID", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    });

    function formatDate(date) {
      return date.toISOString().split("T")[0]; // Mengambil hanya bagian tanggal
    }

    // Buat task unik untuk sumbu Y
    const uniqueTasks = [...new Set(data.wbs_name.flat())];

    console.log(
      data.wbs_name.flatMap((tasks, index) => {
        return tasks.map((task) => {
          const startDate = new Date(data.start_date[index]);
          const endDate = new Date(data.end_date[index]);

          return {
            x: [startDate, endDate],
            y: task,
          };
        });
      })
    );

    const ganttDatasets = [
      {
        label: "Plan Date",
        data: data.wbs_name.flatMap((tasks, index) => {
          return tasks.map((task) => {
            const startDate = new Date(data.start_date[index]);
            const endDate = new Date(data.end_date[index]);

            return {
              x: ['2022'],
              y: task,
            };
          });
        }),
        backgroundColor: "rgba(0, 123, 255, 0.7)",
        borderColor: "rgba(0, 123, 255, 1)",
        borderWidth: 1,
        barPercentage: 0.3,
        barThickness: 20,
      },
    ];

    // const actualBars = {
    //   label: `Actual (${task})`,
    //   data: (data.actual_date[index] || []).map((date) => ({
    //     x: [new Date(data.start_date[index]), new Date(data.end_date[index])],
    //     y: task,
    //   })),
    //   backgroundColor: "rgba(40, 167, 69, 0.7)",
    //   borderColor: "rgba(40, 167, 69, 1)",
    //   borderWidth: 1,
    // };

    // console.log(data.start_date[index]);

    // return [planBars, actualBars];
    //   return [planBars];
    // });

    // Inisialisasi Chart
    this.chart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: formattedDates, // Menampilkan tanggal pada sumbu X
        datasets: [
          ganttDatasets,
          {
            label: "Bobot Rencana (%)",
            data: data.plan_weights,
            borderColor: "#2196F3",
            backgroundColor: "rgba(33, 150, 243, 0.1)",
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            tension: 0.4,
            fill: false,
            pointBackgroundColor: "#2196F3",
            yAxisID: "y1", // Sumbu Y untuk Bobot Rencana
            type: "line",
          },
          {
            label: "Bobot Aktual (%)",
            data: data.actual_weights,
            borderColor: "#4CAF50",
            backgroundColor: "rgba(76, 175, 80, 0.1)",
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            tension: 0.4,
            fill: false,
            pointBackgroundColor: "#4CAF50",
            yAxisID: "y1", // Sumbu Y untuk Bobot Aktual
            type: "line",
          },
          // ...ganttPlanBars, // Menambahkan bar gantt untuk rencana
          // ...ganttActualBars, // Menambahkan bar gantt untuk aktual
        ],
      },
      options: {
        indexAxis: "y", // Set sumbu X horizontal, Y vertikal
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          datalabels: {
            display: false,
          },
          legend: {
            display: true,
            position: "top",
            labels: {
              usePointStyle: true,
              padding: 20,
            },
          },
        },
        scales: {
          y: {
            type: "category",
            labels: uniqueTasks, // Menampilkan task pada sumbu Y
            position: "left",
            grid: {
              drawOnChartArea: false,
            },
            ticks: {
              autoSkip: false, // Menjaga agar task tetap terlihat
            },
          },
          x: {
            beginAtZero: true,
            max: formattedDates.length, // Menyesuaikan batas sumbu X
            ticks: {
              callback: (value) => formattedDates[value] || "", // Tanggal pada sumbu X
            },
            grid: {
              drawBorder: true,
            },
          },
          y1: {
            type: "linear",
            position: "right",
            min: 0,
            max: 100,
            ticks: {
              callback: (value) => `${value}%`,
            },
            grid: {
              drawOnChartArea: false,
            },
          },
        },
        interaction: {
          mode: "nearest",
          intersect: true,
        },
      },
    });
  }
}

registry.category("actions").add("curve_s_chart", CurveSChart);
