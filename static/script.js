const accessToken = document.body.dataset.accessToken;
const baseUrl = "https://5667-185-19-6-117.ngrok-free.app/";

function sendPurchaseRequest(plan, total) {
  //  alert(`Plan: ${plan}, Total: ${total}, AccessToken: ${accessToken}`);

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
      //      alert(`Purchase is successful!`);
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
// MONTHLY SUBSCRIPTION SECTION

// Get elements for monthly subscription
const monthlyVideosCounter = document.getElementById("monthly-videos-counter");
const monthlyVersionsCounter = document.getElementById(
  "monthly-versions-counter"
);
const monthlyTotalAmount = document.getElementById("monthly-total-amount");

// New updateMonthlyTotal function (calculates dynamically and rounds to integers)
function updateMonthlyTotal() {
  // Get current values (as numbers)
  const videos = parseInt(monthlyVideosCounter.textContent, 10);
  const packagesPerVideo = parseInt(monthlyVersionsCounter.textContent, 10);

  // Calculate total packages: Videos per month × Packages per video
  const totalPackages = videos * packagesPerVideo;

  // Calculate price per package:
  // If total packages is 30 or less, use the formula; otherwise, fix it at $30.
  let pricePerPackage;
  if (totalPackages <= 30) {
    pricePerPackage = 51.43 - 0.7143 * totalPackages;
  } else {
    pricePerPackage = 30;
  }

  // Calculate the total cost
  const totalCost = totalPackages * pricePerPackage;

  // Update the total price display (rounded to an integer)
  monthlyTotalAmount.textContent = `$${Math.round(totalCost)}`;

  // Calculate Videos per week (divide videos by 4.3) and round to two decimals
  const videosPerWeek = (videos / 4.3).toFixed(2);
  const monthlyVideosPerWeekElement = document.getElementById(
    "monthly-videos-per-week"
  );
  if (monthlyVideosPerWeekElement) {
    monthlyVideosPerWeekElement.textContent = `Videos per week - ${videosPerWeek}`;
  }

  // Update the Total packages message with integer price per package
  const monthlyTotalPackagesElement = document.getElementById(
    "monthly-total-packages"
  );
  if (monthlyTotalPackagesElement) {
    monthlyTotalPackagesElement.textContent = `Total packages - ${totalPackages} ($${Math.round(
      pricePerPackage
    )} per package)`;
  }
}

// Reset function sets default values: 4 Videos per Month and 2 Packages per Video
function resetMonthlyValues() {
  monthlyVideosCounter.textContent = "4";
  monthlyVersionsCounter.textContent = "2";
  updateMonthlyTotal();
}

// Event listeners for Videos per Month buttons
document
  .getElementById("monthly-videos-increment")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVideosCounter.textContent, 10);
    if (current < 60) {
      // Maximum is 60 videos per month
      monthlyVideosCounter.textContent = current + 1;
      updateMonthlyTotal();
    }
  });

document
  .getElementById("monthly-videos-decrement")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVideosCounter.textContent, 10);
    if (current > 2) {
      // Minimum is 2 videos per month
      monthlyVideosCounter.textContent = current - 1;
      updateMonthlyTotal();
    }
  });

// Event listeners for Packages per Video buttons
document
  .getElementById("monthly-versions-increment")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVersionsCounter.textContent, 10);
    if (current < 4) {
      // Maximum is 4 packages per video
      monthlyVersionsCounter.textContent = current + 1;
      updateMonthlyTotal();
    }
  });

document
  .getElementById("monthly-versions-decrement")
  .addEventListener("click", () => {
    const current = parseInt(monthlyVersionsCounter.textContent, 10);
    if (current > 1) {
      // Minimum is 1 package per video
      monthlyVersionsCounter.textContent = current - 1;
      updateMonthlyTotal();
    }
  });

// Initialize monthly values on page load
resetMonthlyValues();

// Monthly purchase button event
document
  .getElementById("monthly-purchase-btn")
  .addEventListener("click", () => {
    const total = parseFloat(monthlyTotalAmount.textContent.replace("$", ""));
    sendPurchaseRequest("monthly", total);
  });

// ===================================================
// ANNUAL SUBSCRIPTION SECTION =======================

// Get elements for annual subscription
const annualVideosCounter = document.getElementById("annual-videos-counter");
const annualVersionsCounter = document.getElementById(
  "annual-versions-counter"
);
const annualTotalAmount = document.getElementById("annual-total-amount");
// This element displays the annual total cost (small label)
const annualTotalYear = document.getElementById("annual-total-year");

// New updateAnnualTotal function with 10% discount
function updateAnnualTotal() {
  // Get current values (convert to numbers)
  const videos = parseInt(annualVideosCounter.textContent, 10);
  const packagesPerVideo = parseInt(annualVersionsCounter.textContent, 10);

  // Calculate total packages = Videos per month * Packages per video
  const totalPackages = videos * packagesPerVideo;

  // Calculate price per package using the same formula as monthly:
  // If totalPackages <= 30, price = 51.43 - 0.7143 * totalPackages; otherwise, price = $30.
  let pricePerPackage;
  if (totalPackages <= 30) {
    pricePerPackage = 51.43 - 0.7143 * totalPackages;
  } else {
    pricePerPackage = 30;
  }

  // Calculate the monthly cost (before discount)
  const monthlyCost = totalPackages * pricePerPackage;
  const roundedMonthlyCost = Math.round(monthlyCost);

  // Apply a 10% discount for annual subscriptions:
  const discountedMonthlyCost = Math.round(roundedMonthlyCost * 0.9);

  // Annual cost is 12 times the discounted monthly cost
  const annualCost = discountedMonthlyCost * 12;

  // Update the main annual label to show the discounted monthly cost (without duplicating "/month")
  annualTotalAmount.textContent = `$${discountedMonthlyCost}`;

  // Update the smaller label to show the annual total cost.
  // "$XXX" is in the current font size, and "/year" is set to 50% of that.
  annualTotalYear.innerHTML = `$${annualCost}<span style="font-size:50%;">/year</span>`;

  // (Optional) Update "Videos per week" if desired (annual version uses same formula)
  const videosPerWeek = (videos / 4.3).toFixed(2);
  const annualVideosPerWeekElement = document.getElementById(
    "annual-videos-per-week"
  );
  if (annualVideosPerWeekElement) {
    annualVideosPerWeekElement.textContent = `Videos per week - ${videosPerWeek}`;
  }

  // Update the "Total packages" message with discounted per package price
  // (Apply 10% discount to the per package price as well)
  const annualTotalPackagesElement = document.getElementById(
    "annual-total-packages"
  );
  if (annualTotalPackagesElement) {
    annualTotalPackagesElement.textContent = `Total packages - ${totalPackages} ($${Math.round(
      pricePerPackage * 0.9
    )} per package)`;
  }
}

// Reset function: sets default values for annual subscription (4 videos and 2 packages)
function resetAnnualValues() {
  annualVideosCounter.textContent = "4";
  annualVersionsCounter.textContent = "2";
  updateAnnualTotal();
}

// Event listeners for annual Videos per Month buttons
document
  .getElementById("annual-videos-increment")
  .addEventListener("click", () => {
    const current = parseInt(annualVideosCounter.textContent, 10);
    if (current < 60) {
      // Maximum is 60 videos per month
      annualVideosCounter.textContent = current + 1;
      updateAnnualTotal();
    }
  });

document
  .getElementById("annual-videos-decrement")
  .addEventListener("click", () => {
    const current = parseInt(annualVideosCounter.textContent, 10);
    if (current > 2) {
      // Minimum is 2 videos per month
      annualVideosCounter.textContent = current - 1;
      updateAnnualTotal();
    }
  });

// Event listeners for annual Packages per Video buttons
document
  .getElementById("annual-versions-increment")
  .addEventListener("click", () => {
    const current = parseInt(annualVersionsCounter.textContent, 10);
    if (current < 4) {
      // Maximum is 4 packages per video
      annualVersionsCounter.textContent = current + 1;
      updateAnnualTotal();
    }
  });

document
  .getElementById("annual-versions-decrement")
  .addEventListener("click", () => {
    const current = parseInt(annualVersionsCounter.textContent, 10);
    if (current > 1) {
      // Minimum is 1 package per video
      annualVersionsCounter.textContent = current - 1;
      updateAnnualTotal();
    }
  });

// Initialize annual values on page load with default settings
resetAnnualValues();

// Annual purchase button: when clicked, send the annual total (from the small label) to the payment system.
document.getElementById("annual-purchase-btn").addEventListener("click", () => {
  const annualTotalYearText = annualTotalYear.textContent;
  // Remove the "$" and "/year" parts to obtain a number.
  const total = parseFloat(
    annualTotalYearText.replace("$", "").replace("/year", "")
  );
  sendPurchaseRequest("annual", total);
});

// ===================================================
// ONETIME (PAY AS YOU GO) SECTION ===================

// Get elements for onetime subscription (pay as you go)
const onetimeCreditsCounter = document.getElementById(
  "onetime-credits-counter"
);
const onetimeTotalAmount = document.getElementById("onetime-total-amount");

// The dynamic pricing for onetime (pay as you go):
// For q packages (1 ≤ q ≤ 10):
//   Cost per package = 60 - (10/9) * (q - 1)
//   Total cost = q * (cost per package), rounded to the nearest integer.
function computeOnetimeTotal(q) {
  let costPerPackage = 60 - (10 / 9) * (q - 1);
  let total = q * costPerPackage;
  return Math.round(total);
}

function updateOnetimeTotal() {
  const credits = parseInt(onetimeCreditsCounter.textContent, 10);
  const total = computeOnetimeTotal(credits);
  onetimeTotalAmount.textContent = `$${total}`;

  // Compute cost per package for onetime pricing
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
