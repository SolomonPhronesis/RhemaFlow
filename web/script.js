const references = {
  "john 3:16": {
    ref: "John 3:16",
    confidence: "98% confidence",
    verse: "For God so loved the world, that he gave his only begotten Son, that whosoever believeth in him should not perish."
  },
  "romans 8:28": {
    ref: "Romans 8:28",
    confidence: "96% confidence",
    verse: "And we know that all things work together for good to them that love God."
  },
  "psalm 23:1": {
    ref: "Psalm 23:1",
    confidence: "97% confidence",
    verse: "The LORD is my shepherd; I shall not want."
  }
};

function detectReference(text) {
  const normalized = text.toLowerCase().replace(/[.,!?]/g, " ");
  const match = Object.keys(references).find(key => normalized.includes(key));
  return match ? references[match] : null;
}

function runDemo() {
  const input = document.getElementById("speechInput");
  const result = document.getElementById("demoResult");
  const detectedRef = document.getElementById("detectedRef");
  const detectedConfidence = document.getElementById("detectedConfidence");
  const verseText = document.getElementById("verseText");
  const found = detectReference(input.value);

  result.hidden = false;

  if (!found) {
    detectedRef.textContent = "No reference detected";
    detectedConfidence.textContent = "Try John 3:16, Romans 8:28 or Psalm 23:1";
    verseText.textContent = "The demo uses a small set of mock references. Try one of the examples above.";
    return;
  }

  detectedRef.textContent = found.ref;
  detectedConfidence.textContent = found.confidence;
  verseText.textContent = found.verse;
}

const detectBtn = document.getElementById("detectBtn");
if (detectBtn) detectBtn.addEventListener("click", runDemo);
const speechInput = document.getElementById("speechInput");
if (speechInput) speechInput.addEventListener("keydown", event => {
  if (event.key === "Enter") runDemo();
});
document.querySelectorAll(".mini").forEach(button => {
  button.addEventListener("click", () => {
    button.parentElement.querySelectorAll(".mini").forEach(b => b.style.opacity = "0.45");
    button.style.opacity = "1";
    button.textContent = button.textContent + " ✓";
  });
});
