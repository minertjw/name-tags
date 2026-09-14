const generatorForm = document.querySelector("#generator-form");
const templateInput = document.querySelector("#template");
const csvInput = document.querySelector("#csv-file");
const fontSelect = document.querySelector("#font-id");
const customFontLabel = document.querySelector("#custom-font-label");
const previewState = document.querySelector("#preview-state");
const generatorMessage = document.querySelector("#generator-message");
const generateTagsButton = document.querySelector("#generate-tags");
const textBoxesInput = document.querySelector("#text-boxes");
const resetBoxesButton = document.querySelector("#reset-boxes");
const defaultTextBoxes = JSON.parse(textBoxesInput.value);
let textBoxes = structuredClone(defaultTextBoxes);
let previewTimer;
let previewController;
const previewUrls = {};
const previewBlobs = {};
let csvIsValid = false;
const minimumBoxSize = 0.03;

updateBoxOverlays();

document.querySelectorAll(".text-box").forEach((element) => {
  element.addEventListener("pointerdown", beginBoxInteraction);
  element.addEventListener("keydown", adjustBoxWithKeyboard);
});

resetBoxesButton.addEventListener("click", () => {
  textBoxes = structuredClone(defaultTextBoxes);
  updateBoxOverlays();
  schedulePreview();
});

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

fontSelect.addEventListener("change", () => {
  customFontLabel.classList.toggle("is-hidden", fontSelect.value !== "custom");
  schedulePreview();
});

generatorForm.addEventListener("input", schedulePreview);
generatorForm.addEventListener("change", schedulePreview);
templateInput.addEventListener("change", () => {
  const template = templateInput.files[0];
  document.querySelector("#template-name").textContent = template?.name || "No template selected";
  document.querySelectorAll(".box-overlay").forEach((overlay) => {
    overlay.hidden = !template;
  });
  if (template) updateTemplateAspectRatio(template);
  generateTagsButton.disabled = !(csvIsValid && templateInput.files.length);
});

function updateTemplateAspectRatio(file) {
  const url = URL.createObjectURL(file);
  const image = new Image();
  image.addEventListener("load", () => {
    document.querySelectorAll(".preview-stage").forEach((stage) => {
      stage.style.aspectRatio = `${image.naturalWidth} / ${image.naturalHeight}`;
    });
    URL.revokeObjectURL(url);
  });
  image.addEventListener("error", () => URL.revokeObjectURL(url));
  image.src = url;
}

function beginBoxInteraction(event) {
  if (event.button !== 0) return;
  event.preventDefault();
  const element = event.currentTarget;
  const stageBounds = element.closest(".preview-stage").getBoundingClientRect();
  const box = textBoxes.find((candidate) => candidate.name === element.dataset.boxName);
  const startBox = { ...box };
  const handle = event.target.dataset.handle || "move";
  const startX = event.clientX;
  const startY = event.clientY;
  element.focus();
  element.setPointerCapture(event.pointerId);

  const move = (moveEvent) => {
    const deltaX = (moveEvent.clientX - startX) / stageBounds.width;
    const deltaY = (moveEvent.clientY - startY) / stageBounds.height;
    resizeOrMoveBox(box, startBox, handle, deltaX, deltaY);
    updateBoxOverlays();
    previewState.textContent = "Changes pending";
  };
  const finish = () => {
    element.removeEventListener("pointermove", move);
    element.removeEventListener("pointerup", finish);
    element.removeEventListener("pointercancel", finish);
    schedulePreview();
  };
  element.addEventListener("pointermove", move);
  element.addEventListener("pointerup", finish);
  element.addEventListener("pointercancel", finish);
}

function resizeOrMoveBox(box, start, handle, deltaX, deltaY) {
  if (handle === "move") {
    box.top = clamp(start.top + deltaY, 0, 1 - start.height);
    return;
  }

  let left = start.left;
  let top = start.top;
  let right = start.left + start.width;
  let bottom = start.top + start.height;
  if (handle.includes("w")) left = clamp(start.left + deltaX, 0, right - minimumBoxSize);
  if (handle.includes("e")) right = clamp(right + deltaX, left + minimumBoxSize, 1);
  if (handle.includes("n")) top = clamp(start.top + deltaY, 0, bottom - minimumBoxSize);
  if (handle.includes("s")) bottom = clamp(bottom + deltaY, top + minimumBoxSize, 1);
  box.left = left;
  box.top = top;
  box.width = right - left;
  box.height = bottom - top;
}

function adjustBoxWithKeyboard(event) {
  if (!["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(event.key)) return;
  if (!event.shiftKey && !["ArrowUp", "ArrowDown"].includes(event.key)) return;
  event.preventDefault();
  const box = textBoxes.find((candidate) => candidate.name === event.currentTarget.dataset.boxName);
  const amount = event.altKey ? 0.001 : 0.005;
  if (event.shiftKey) {
    if (event.key === "ArrowLeft") box.width = Math.max(minimumBoxSize, box.width - amount);
    if (event.key === "ArrowRight") box.width = Math.min(1 - box.left, box.width + amount);
    if (event.key === "ArrowUp") box.height = Math.max(minimumBoxSize, box.height - amount);
    if (event.key === "ArrowDown") box.height = Math.min(1 - box.top, box.height + amount);
  } else {
    if (event.key === "ArrowUp") box.top = Math.max(0, box.top - amount);
    if (event.key === "ArrowDown") box.top = Math.min(1 - box.height, box.top + amount);
  }
  updateBoxOverlays();
  schedulePreview();
}

function updateBoxOverlays() {
  textBoxes.forEach((box) => {
    document.querySelectorAll(`[data-box-name="${box.name}"]`).forEach((element) => {
      element.style.left = `${box.left * 100}%`;
      element.style.top = `${box.top * 100}%`;
      element.style.width = `${box.width * 100}%`;
      element.style.height = `${box.height * 100}%`;
    });
  });
  textBoxesInput.value = JSON.stringify(textBoxes);
}

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

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
    await Promise.all(["long", "short"].map(async (previewCase) => {
      const data = generatorData();
      data.set("preview_case", previewCase);
      const response = await fetch("/api/generator/preview", {
        method: "POST",
        body: data,
        signal: previewController.signal,
      });
      const blob = await response.blob();
      if (!response.ok) throw new Error(await readError(blob));
      if (previewUrls[previewCase]) URL.revokeObjectURL(previewUrls[previewCase]);
      previewBlobs[previewCase] = blob;
      previewUrls[previewCase] = URL.createObjectURL(blob);
      const image = document.querySelector(`#preview-${previewCase}-image`);
      image.src = previewUrls[previewCase];
      image.hidden = false;
      image.parentElement.querySelector(".preview-empty").hidden = true;
      document.querySelector(`[data-preview-download="${previewCase}"]`).disabled = false;
    }));
    previewState.textContent = "Up to date";
  } catch (error) {
    if (error.name === "AbortError") return;
    previewState.textContent = "Could not render";
    setMessage(error.message, true);
  }
}

document.querySelectorAll("[data-preview-download]").forEach((button) => {
  button.addEventListener("click", () => {
    const previewCase = button.dataset.previewDownload;
    const blob = previewBlobs[previewCase];
    if (blob) downloadBlob(blob, `name_tag_${previewCase}_preview.png`);
  });
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