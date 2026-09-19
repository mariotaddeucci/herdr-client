function labelSearchDialogs() {
  document.documentElement.classList.toggle(
    "landing-home",
    Boolean(document.querySelector(".landing-page")),
  );
  document.body.classList.toggle(
    "api-page",
    window.location.pathname.includes("/reference/"),
  );

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
