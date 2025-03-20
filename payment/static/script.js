const accessToken = document.body.dataset.accessToken;
const isSubscriptionActive =
  document.body.dataset.isSubscriptionActive === "true";
const baseUrl =
  "https://1c1c-2a02-2378-1040-50f6-e124-656a-ed4-2441.ngrok-free.app/";

const payAsYouGoTab = document.querySelector(
  '.tab-button[data-tab="pay-as-you-go"]'
);
const payAsYouGoContent = document.getElementById("pay-as-you-go");
const payAsYouGoPurchaseBtn = document.getElementById("onetime-purchase-btn");

console.log("Subscription Active:", isSubscriptionActive);
console.log("Tab Element:", payAsYouGoTab);
console.log("Content Element:", payAsYouGoContent);
console.log("Purchase Button:", payAsYouGoPurchaseBtn);

if (!isSubscriptionActive) {
  payAsYouGoTab.classList.add("disabled");
  payAsYouGoContent.classList.add("disabled");
  payAsYouGoPurchaseBtn.disabled = true;
} else {
  payAsYouGoTab.classList.remove("disabled");
  payAsYouGoContent.classList.remove("disabled");
  payAsYouGoPurchaseBtn.disabled = false;
}

function sendPurchaseRequest(plan, total) {
  fetch(baseUrl + "api/create-invoice", {
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
      window.location.href = data.payment_url;
    })
    .catch((error) => {
      console.error("Error:", error);
      alert("Something went wrong. Please try again later.");
    });
}

// === === === === === //

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

function updateMonthlyTotal() {
  const videos = parseInt(monthlyVideosCounter.textContent, 10);
  const packagesPerVideo = parseInt(monthlyVersionsCounter.textContent, 10);

  const totalPackages = videos * packagesPerVideo;

  let pricePerPackage;
  if (totalPackages <= 30) {
    pricePerPackage = 51.43 - 0.7143 * totalPackages;
  } else {
    pricePerPackage = 30;
  }

  const totalCost = totalPackages * pricePerPackage;

  monthlyTotalAmount.textContent = `$${Math.round(totalCost)}`;

  const videosPerWeek = (videos / 4.3).toFixed(2);
  const monthlyVideosPerWeekElement = document.getElementById(
    "monthly-videos-per-week"
  );
  if (monthlyVideosPerWeekElement) {
    monthlyVideosPerWeekElement.textContent = `Videos per week - ${videosPerWeek}`;
  }

  const monthlyTotalPackagesElement = document.getElementById(
    "monthly-total-packages"
  );
  if (monthlyTotalPackagesElement) {
    monthlyTotalPackagesElement.textContent = `Total packages - ${totalPackages} ($${Math.round(
      pricePerPackage
    )} per package)`;
  }
}

function resetMonthlyValues() {
  monthlyVideosCounter.textContent = "4";
  monthlyVersionsCounter.textContent = "2";
  updateMonthlyTotal();
}

document
  .getElementById("monthly-videos-increment")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVideosCounter.textContent, 10);
    if (current < 60) {
      monthlyVideosCounter.textContent = current + 1;
      updateMonthlyTotal();
    }
  });

document
  .getElementById("monthly-videos-decrement")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVideosCounter.textContent, 10);
    if (current > 2) {
      monthlyVideosCounter.textContent = current - 1;
      updateMonthlyTotal();
    }
  });

document
  .getElementById("monthly-versions-increment")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVersionsCounter.textContent, 10);
    if (current < 4) {
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

resetMonthlyValues();

document
  .getElementById("monthly-purchase-btn")
  .addEventListener("click", () => {
    const total = parseFloat(monthlyTotalAmount.textContent.replace("$", ""));
    sendPurchaseRequest("monthly", total);
  });

const annualVideosCounter = document.getElementById("annual-videos-counter");
const annualVersionsCounter = document.getElementById(
  "annual-versions-counter"
);
const annualTotalAmount = document.getElementById("annual-total-amount");
const annualTotalYear = document.getElementById("annual-total-year");

function updateAnnualTotal() {
  const videos = parseInt(annualVideosCounter.textContent, 10);
  const packagesPerVideo = parseInt(annualVersionsCounter.textContent, 10);

  const totalPackages = videos * packagesPerVideo;

  let pricePerPackage;
  if (totalPackages <= 30) {
    pricePerPackage = 51.43 - 0.7143 * totalPackages;
  } else {
    pricePerPackage = 30;
  }

  const monthlyCost = totalPackages * pricePerPackage;
  const roundedMonthlyCost = Math.round(monthlyCost);

  const discountedMonthlyCost = Math.round(roundedMonthlyCost * 0.9);

  const annualCost = discountedMonthlyCost * 12;

  annualTotalAmount.textContent = `$${discountedMonthlyCost}`;

  annualTotalYear.innerHTML = `$${annualCost}<span style="font-size:50%;">/year</span>`;

  const videosPerWeek = (videos / 4.3).toFixed(2);
  const annualVideosPerWeekElement = document.getElementById(
    "annual-videos-per-week"
  );
  if (annualVideosPerWeekElement) {
    annualVideosPerWeekElement.textContent = `Videos per week - ${videosPerWeek}`;
  }

  const annualTotalPackagesElement = document.getElementById(
    "annual-total-packages"
  );
  if (annualTotalPackagesElement) {
    annualTotalPackagesElement.textContent = `Total packages - ${totalPackages} ($${Math.round(
      pricePerPackage * 0.9
    )} per package)`;
  }
}

function resetAnnualValues() {
  annualVideosCounter.textContent = "4";
  annualVersionsCounter.textContent = "2";
  updateAnnualTotal();
}

document
  .getElementById("annual-videos-increment")
  .addEventListener("click", () => {
    const current = parseInt(annualVideosCounter.textContent, 10);
    if (current < 60) {
      annualVideosCounter.textContent = current + 1;
      updateAnnualTotal();
    }
  });

document
  .getElementById("annual-videos-decrement")
  .addEventListener("click", () => {
    const current = parseInt(annualVideosCounter.textContent, 10);
    if (current > 2) {
      annualVideosCounter.textContent = current - 1;
      updateAnnualTotal();
    }
  });

document
  .getElementById("annual-versions-increment")
  .addEventListener("click", () => {
    const current = parseInt(annualVersionsCounter.textContent, 10);
    if (current < 4) {
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

resetAnnualValues();

document.getElementById("annual-purchase-btn").addEventListener("click", () => {
  const annualTotalYearText = annualTotalYear.textContent;
  const total = parseFloat(
    annualTotalYearText.replace("$", "").replace("/year", "")
  );
  sendPurchaseRequest("annual", total);
});

const onetimeCreditsCounter = document.getElementById(
  "onetime-credits-counter"
);
const onetimeTotalAmount = document.getElementById("onetime-total-amount");

function computeOnetimeTotal(q) {
  let costPerPackage = 60 - (10 / 9) * (q - 1);
  let total = q * costPerPackage;
  return Math.round(total);
}

function updateOnetimeTotal() {
  const credits = parseInt(onetimeCreditsCounter.textContent, 10);
  const total = computeOnetimeTotal(credits);
  onetimeTotalAmount.textContent = `$${total}`;

  let costPerPackage = 60 - (10 / 9) * (credits - 1);
  costPerPackage = Math.round(costPerPackage);
  const onetimePricePerPackageElement = document.getElementById(
    "onetime-price-per-package"
  );
  if (onetimePricePerPackageElement) {
    onetimePricePerPackageElement.textContent = `$${costPerPackage} per package`;
  }
}

function initializeOnetimeTotal() {
  const credits = parseInt(onetimeCreditsCounter.textContent, 10);
  const total = computeOnetimeTotal(credits);
  onetimeTotalAmount.textContent = `$${total}`;

  let costPerPackage = 60 - (10 / 9) * (credits - 1);
  costPerPackage = Math.round(costPerPackage);
  const onetimePricePerPackageElement = document.getElementById(
    "onetime-price-per-package"
  );
  if (onetimePricePerPackageElement) {
    onetimePricePerPackageElement.textContent = `$${costPerPackage} per package`;
  }
}

function resetOnetimeValues() {
  onetimeCreditsCounter.textContent = "1";
  onetimeTotalAmount.textContent = `$${computeOnetimeTotal(1)}`;
  const onetimePricePerPackageElement = document.getElementById(
    "onetime-price-per-package"
  );
  if (onetimePricePerPackageElement) {
    onetimePricePerPackageElement.textContent = `$60 per package`;
  }
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
