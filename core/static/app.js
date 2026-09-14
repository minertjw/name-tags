const generatorForm = document.querySelector("#generator-form");
const templateInput = document.querySelector("#template");
const csvInput = document.querySelector("#csv-file");
const fontSelect = document.querySelector("#font-id");
const customFontLabel = document.querySelector("#custom-font-label");
const previewImage = document.querySelector("#preview-image");
const previewEmpty = document.querySelector("#preview-empty");
const previewState = document.querySelector("#preview-state");
const generatorMessage = document.querySelector("#generator-message");
const generateTagsButton = document.querySelector("#generate-tags");
const downloadPreviewButton = document.querySelector("#download-preview");
let previewTimer;
let previewController;
let previewUrl;
let previewBlob;
let csvIsValid = false;

document.querySelectorAll("[data-tab]").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll("[data-tab]").forEach((candidate) => {
      const selected = candidate === tab;
      candidate.classList.toggle("is-active", selected);
      candidate.setAttribute("aria-selected", String(selected));
      const panel = document.querySelector(`#${candidate.dataset.tab}`);
      panel.hidden = !selected;
      panel.classList.toggle("is-active", selected);
    });
  });
});

document.querySelectorAll("[data-sync]").forEach((control) => {
  control.addEventListener("input", () => {
    document.querySelector(`#${control.dataset.sync}`).value = control.value;
  });
});

fontSelect.addEventListener("change", () => {
  customFontLabel.classList.toggle("is-hidden", fontSelect.value !== "custom");
  schedulePreview();
});

generatorForm.addEventListener("input", schedulePreview);
generatorForm.addEventListener("change", schedulePreview);
templateInput.addEventListener("change", () => {
  document.querySelector("#template-name").textContent = templateInput.files[0]?.name || "No template selected";
  generateTagsButton.disabled = !(csvIsValid && templateInput.files.length);
});

function schedulePreview() {
  window.clearTimeout(previewTimer);
  if (!templateInput.files.length || !generatorForm.reportValidity()) return;
  previewState.textContent = "Changes pending";
  previewTimer = window.setTimeout(renderPreview, 500);
}

function generatorData(includeCsv = false) {
  const data = new FormData(generatorForm);
  if (fontSelect.value === "custom") data.set("font_id", "0");
  if (!includeCsv) data.delete("csv");
  return data;
}

async function renderPreview() {
  previewController?.abort();
  previewController = new AbortController();
  previewState.textContent = "Rendering";
  setMessage("");
  try {
    const response = await fetch("/api/generator/preview", {
      method: "POST",
      body: generatorData(),
      signal: previewController.signal,
    });
    const blob = await response.blob();
    if (!response.ok) throw new Error(await readError(blob));
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewBlob = blob;
    previewUrl = URL.createObjectURL(blob);
    previewImage.src = previewUrl;
    previewImage.hidden = false;
    previewEmpty.hidden = true;
    previewState.textContent = "Up to date";
    downloadPreviewButton.disabled = false;
  } catch (error) {
    if (error.name === "AbortError") return;
    previewState.textContent = "Could not render";
    setMessage(error.message, true);
  }
}

downloadPreviewButton.addEventListener("click", () => {
  if (previewBlob) downloadBlob(previewBlob, "name_tag_preview.png");
});

csvInput.addEventListener("change", async () => {
  csvIsValid = false;
  generateTagsButton.disabled = true;
  document.querySelector("#csv-preview").hidden = true;
  const file = csvInput.files[0];
  document.querySelector("#csv-count").textContent = file ? "Validating..." : "No CSV selected";
  if (!file) return;
  const data = new FormData();
  data.append("csv", file);
  try {
    const response = await fetch("/api/csv/preview", { method: "POST", body: data });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    csvIsValid = true;
    document.querySelector("#csv-count").textContent = `${result.row_count} ${result.row_count === 1 ? "row" : "rows"}`;
    renderCsvRows(result.rows);
    generateTagsButton.disabled = !templateInput.files.length;
    setMessage("");
  } catch (error) {
    document.querySelector("#csv-count").textContent = "Invalid CSV";
    setMessage(error.message, true);
  }
});

generateTagsButton.addEventListener("click", async () => {
  if (!generatorForm.reportValidity()) return;
  await runDownload(generateTagsButton, "/api/generator/batch", generatorData(true), "generated_name_tags.zip", "Generating tags...");
});

function renderCsvRows(rows) {
  const container = document.querySelector("#csv-preview");
  const table = document.createElement("table");
  const head = document.createElement("tr");
  ["Top", "Middle", "Bottom"].forEach((label) => {
    const cell = document.createElement("th");
    cell.textContent = label;
    head.append(cell);
  });
  const tableHead = document.createElement("thead");
  tableHead.append(head);
  table.append(tableHead);
  const body = document.createElement("tbody");
  rows.forEach((row) => {
    const line = document.createElement("tr");
    [row.top, row.middle, row.bottom].forEach((value) => {
      const cell = document.createElement("td");
      cell.textContent = value;
      line.append(cell);
    });
    body.append(line);
  });
  table.append(body);
  container.replaceChildren(table);
  container.hidden = false;
}

const pdfForm = document.querySelector("#pdf-form");
const pdfFilesInput = document.querySelector("#pdf-images");
const pdfFolderInput = document.querySelector("#pdf-folder");
const generatePdfButton = document.querySelector("#generate-pdf");
let pdfFiles = [];

[pdfFilesInput, pdfFolderInput].forEach((input) => input.addEventListener("change", () => {
  pdfFiles = Array.from(input.files).filter((file) => /\.(png|jpe?g|bmp|gif)$/i.test(file.name));
  const otherInput = input === pdfFilesInput ? pdfFolderInput : pdfFilesInput;
  otherInput.value = "";
  document.querySelector("#image-count").textContent = pdfFiles.length ? `${pdfFiles.length} ${pdfFiles.length === 1 ? "image" : "images"}` : "No images selected";
  generatePdfButton.disabled = pdfFiles.length === 0;
  logActivity(pdfFiles.length ? `${pdfFiles.length} images ready for layout.` : "Select name tag images to begin.", true);
}));

pdfForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!pdfFiles.length) return;
  const data = new FormData();
  pdfFiles.forEach((file) => data.append("images", file, file.name));
  const mode = new FormData(pdfForm).get("mode");
  data.append("mode", mode);
  logActivity("Building print-ready pages...");
  generatePdfButton.disabled = true;
  const originalText = generatePdfButton.textContent;
  generatePdfButton.textContent = "Generating...";
  try {
    const response = await fetch("/api/pdf", { method: "POST", body: data });
    const blob = await response.blob();
    if (!response.ok) throw new Error(await readError(blob));
    const filename = mode === "combined" ? "output_combined.pdf" : "name_tag_pdfs.zip";
    downloadBlob(blob, filename);
    logActivity(`${filename} is ready.`);
  } catch (error) {
    logActivity(`Error: ${error.message}`);
  } finally {
    generatePdfButton.disabled = false;
    generatePdfButton.textContent = originalText;
  }
});

async function runDownload(button, url, data, filename, busyText) {
  const originalText = button.textContent;
  button.disabled = true;
  button.textContent = busyText;
  setMessage(busyText);
  try {
    const response = await fetch(url, { method: "POST", body: data });
    const blob = await response.blob();
    if (!response.ok) throw new Error(await readError(blob));
    downloadBlob(blob, filename);
    setMessage(`${filename} is ready.`);
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

async function readError(blob) {
  try {
    return (JSON.parse(await blob.text())).error || "The request could not be completed.";
  } catch {
    return "The request could not be completed.";
  }
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function setMessage(text, isError = false) {
  generatorMessage.textContent = text;
  generatorMessage.classList.toggle("is-error", isError);
}

function logActivity(text, replace = false) {
  const log = document.querySelector("#activity-log");
  const item = document.createElement("li");
  item.textContent = text;
  if (replace) log.replaceChildren(item);
  else log.append(item);
  log.scrollTop = log.scrollHeight;
}