const accessToken = document.body.dataset.accessToken;

function sendPurchaseRequest(plan, total) {
  alert(`Plan: ${plan}, Total: ${total}, AccessToken: ${accessToken}`);

  fetch("/api/create-invoice", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      plan: plan,
      total: total,
      access_token: accessToken,
    }),
  })
    .then((response) => {
      if (response.ok) {
        return response.json();
      } else {
        throw new Error("Failed to process the purchase.");
      }
    })
    .then((data) => {
      alert(`Purchase is successful!`);
      window.location.href = data.payment_url;
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Something went wrong. Please try again later.");
    });
}

// ==================================

const tabButtons = document.querySelectorAll(".tab-button");
const tabContents = document.querySelectorAll(".tab-content");

tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    tabButtons.forEach((btn) => btn.classList.remove("active"));
    tabContents.forEach((content) => content.classList.remove("active"));

    button.classList.add("active");
    document.getElementById(button.dataset.tab).classList.add("active");

    if (button.dataset.tab !== "monthly") {
      resetMonthlyValues();
    }
    if (button.dataset.tab !== "annual") {
      resetAnnualValues();
    }
    if (button.dataset.tab !== "onetime") {
      resetOnetimeValues();
    }
  });
});

// ===================================================

const monthlyVideosCounter = document.getElementById("monthly-videos-counter");
const monthlyVersionsCounter = document.getElementById(
  "monthly-versions-counter"
);
const monthlyTotalAmount = document.getElementById("monthly-total-amount");

const pricingTable = {
  1: { 1: 240, 2: 456, 3: 648 },
  2: { 1: 456, 2: 816, 3: 1080 },
  3: { 1: 648, 2: 1080, 3: 1296 },
  4: { 1: 816, 2: 1248, 3: 1728 },
  5: { 1: 960, 2: 1440, 3: 2160 },
  6: { 1: 1080, 2: 1728, 3: 2592 },
  7: { 1: 1092, 2: 2016, 3: 3024 },
};

function initializeMonthlyTotal() {
  const videos = parseInt(monthlyVideosCounter.textContent, 10);
  const versions = parseInt(monthlyVersionsCounter.textContent, 10);
  const total = pricingTable[videos][versions];
  monthlyTotalAmount.textContent = `$${total}`;
}

function updateMonthlyTotal() {
  const videos = parseInt(monthlyVideosCounter.textContent, 10);
  const versions = parseInt(monthlyVersionsCounter.textContent, 10);
  const total = pricingTable[videos][versions];
  monthlyTotalAmount.textContent = `$${total}`;
}

function resetMonthlyValues() {
  monthlyVideosCounter.textContent = "1";
  monthlyVersionsCounter.textContent = "1";
  monthlyTotalAmount.textContent = `$${pricingTable[1][1]}`;
}

document
  .getElementById("monthly-videos-increment")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVideosCounter.textContent, 10);
    if (current < 7) {
      monthlyVideosCounter.textContent = current + 1;
      updateMonthlyTotal();
    }
  });

document
  .getElementById("monthly-videos-decrement")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVideosCounter.textContent, 10);
    if (current > 1) {
      monthlyVideosCounter.textContent = current - 1;
      updateMonthlyTotal();
    }
  });

document
  .getElementById("monthly-versions-increment")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVersionsCounter.textContent, 10);
    if (current < 3) {
      monthlyVersionsCounter.textContent = current + 1;
      updateMonthlyTotal();
    }
  });

document
  .getElementById("monthly-versions-decrement")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVersionsCounter.textContent, 10);
    if (current > 1) {
      monthlyVersionsCounter.textContent = current - 1;
      updateMonthlyTotal();
    }
  });

initializeMonthlyTotal();

document
  .getElementById("monthly-purchase-btn")
  .addEventListener("click", () => {
    const total = parseInt(monthlyTotalAmount.textContent.replace("$", ""), 10);
    sendPurchaseRequest("monthly", total);
  });

// ===================================================

const annualVideosCounter = document.getElementById("annual-videos-counter");
const annualVersionsCounter = document.getElementById(
  "annual-versions-counter"
);
const annualTotalAmount = document.getElementById("annual-total-amount");
const annualMonthlyAmount = document.getElementById("annual-monthly-amount");

const annualPricingTable = {
  1: { 1: 2592, 2: 4925, 3: 6998 },
  2: { 1: 4925, 2: 8813, 3: 11664 },
  3: { 1: 6698, 2: 11664, 3: 13997 },
  4: { 1: 8813, 2: 13478, 3: 18662 },
  5: { 1: 10368, 2: 15552, 3: 23328 },
  6: { 1: 11664, 2: 18662, 3: 27994 },
  7: { 1: 12701, 2: 21773, 3: 32659 },
};

function initializeAnnualTotal() {
  const videos = parseInt(annualVideosCounter.textContent, 10);
  const versions = parseInt(annualVersionsCounter.textContent, 10);
  const total = annualPricingTable[videos][versions];
  const monthlyEquivalent = Math.round(total / 12);
  annualTotalAmount.textContent = `$${total}`;
  annualMonthlyAmount.textContent = `(${monthlyEquivalent} per month)`;
}

function updateAnnualTotal() {
  const videos = parseInt(annualVideosCounter.textContent, 10);
  const versions = parseInt(annualVersionsCounter.textContent, 10);
  const total = annualPricingTable[videos][versions];
  const monthlyEquivalent = Math.round(total / 12);
  annualTotalAmount.textContent = `$${total}`;
  annualMonthlyAmount.textContent = `(${monthlyEquivalent} per month)`;
}

function resetAnnualValues() {
  annualVideosCounter.textContent = "1";
  annualVersionsCounter.textContent = "1";
  annualTotalAmount.textContent = `$${annualPricingTable[1][1]}`;
  annualMonthlyAmount.textContent = `(216 per month)`;
}

document
  .getElementById("annual-videos-increment")
  .addEventListener("click", () => {
    const current = parseInt(annualVideosCounter.textContent, 10);
    if (current < 7) {
      annualVideosCounter.textContent = current + 1;
      updateAnnualTotal();
    }
  });

document
  .getElementById("annual-videos-decrement")
  .addEventListener("click", () => {
    const current = parseInt(annualVideosCounter.textContent, 10);
    if (current > 1) {
      annualVideosCounter.textContent = current - 1;
      updateAnnualTotal();
    }
  });

document
  .getElementById("annual-versions-increment")
  .addEventListener("click", () => {
    const current = parseInt(annualVersionsCounter.textContent, 10);
    if (current < 3) {
      annualVersionsCounter.textContent = current + 1;
      updateAnnualTotal();
    }
  });

document
  .getElementById("annual-versions-decrement")
  .addEventListener("click", () => {
    const current = parseInt(annualVersionsCounter.textContent, 10);
    if (current > 1) {
      annualVersionsCounter.textContent = current - 1;
      updateAnnualTotal();
    }
  });

initializeAnnualTotal();

document.getElementById("annual-purchase-btn").addEventListener("click", () => {
  const total = parseInt(annualTotalAmount.textContent.replace("$", ""), 10);
  sendPurchaseRequest("annual", total);
});

// ===================================================

const onetimeCreditsCounter = document.getElementById(
  "onetime-credits-counter"
);
const onetimeTotalAmount = document.getElementById("onetime-total-amount");

const onetimePricingTable = {
  1: 70,
  2: 140,
  3: 210,
  4: 260,
  5: 325,
  6: 390,
  7: 455,
  8: 480,
  9: 540,
  10: 600,
};

function initializeOnetimeTotal() {
  const credits = parseInt(onetimeCreditsCounter.textContent, 10);
  const total = onetimePricingTable[credits];
  onetimeTotalAmount.textContent = `$${total}`;
}

function updateOnetimeTotal() {
  const credits = parseInt(onetimeCreditsCounter.textContent, 10);
  const total = onetimePricingTable[credits];
  onetimeTotalAmount.textContent = `$${total}`;
}

function resetOnetimeValues() {
  onetimeCreditsCounter.textContent = "1";
  onetimeTotalAmount.textContent = `$${onetimePricingTable[1]}`;
}

document
  .getElementById("onetime-credits-increment")
  .addEventListener("click", () => {
    const current = parseInt(onetimeCreditsCounter.textContent, 10);
    if (current < 10) {
      onetimeCreditsCounter.textContent = current + 1;
      updateOnetimeTotal();
    }
  });

document
  .getElementById("onetime-credits-decrement")
  .addEventListener("click", () => {
    const current = parseInt(onetimeCreditsCounter.textContent, 10);
    if (current > 1) {
      onetimeCreditsCounter.textContent = current - 1;
      updateOnetimeTotal();
    }
  });

initializeOnetimeTotal();

document
  .getElementById("onetime-purchase-btn")
  .addEventListener("click", () => {
    const total = parseInt(onetimeTotalAmount.textContent.replace("$", ""), 10);
    sendPurchaseRequest("onetime", total);
  });
