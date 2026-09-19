function labelSearchDialogs() {
  document.querySelectorAll('.md-search[role="dialog"]').forEach((dialog) => {
    if (!dialog.hasAttribute("aria-label")) {
      dialog.setAttribute("aria-label", "Search documentation");
    }
  });
}

if (typeof document$ !== "undefined") {
  document$.subscribe(labelSearchDialogs);
} else {
  document.addEventListener("DOMContentLoaded", labelSearchDialogs);
}
